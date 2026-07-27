"""
Procesa el pago de un servicio

    1. Exigir turno de caja abierto          → sin responsable no hay pago
    2. Construir y validar el cliente        → nombre, estado y saldo
    3. Verificar que el cliente esté ACTIVO
    4. Calcular el detalle (servicio, valor, comisión, total)
    5. Verificar saldo suficiente contra el TOTAL
    6. Debitar                               ← primer cambio de estado
    7. Registrar el pago                     → obtiene su secuencial
    8. Generar el comprobante
    9. Auditar el resultado                  → aprobado o rechazado

"""

from decimal import Decimal

from core.excepciones import ErrorSistemaPagos
from dominio.clientes import (
    crear_cliente,
    debitar,
    describir_cliente,
    obtener_saldo,
    validar_cliente,
    validar_saldo_suficiente,
)
from dominio.comprobantes import generar_comprobante, renderizar_comprobante
from dominio.pagos import calcular_detalle, construir_pago, describir_detalle
from infraestructura.auditoria import auditar_pago_aprobado, auditar_pago_rechazado
from infraestructura.repositorio_pagos import obtener_secuencial, registrar_pago
from aplicacion.sesion import exigir_turno_activo

CLIENTE_NO_IDENTIFICADO = "(cliente no identificado)"


# --------------------------------------------------------------------------- #
# Previsualización (cálculo sin efectos: nada se debita ni se registra)
# --------------------------------------------------------------------------- #
def previsualizar_pago(servicio: str, valor) -> dict:
    """Calcula el detalle de un pago para confirmarlo antes de ejecutarlo.

    Permite mostrar al cliente cuánto se le va a debitar ANTES de tocar su
    saldo. Valida el servicio y el monto, pero no persiste nada: si el
    operador no confirma, no queda rastro de una operación que no ocurrió.

    Raises:
        ServicioNoDisponibleError: si el servicio no está habilitado.
        MontoInvalidoError: si el valor no es cobrable.
    """
    return calcular_detalle(servicio, valor)


# --------------------------------------------------------------------------- #
# Pasos del flujo (cada uno con una sola responsabilidad)
# --------------------------------------------------------------------------- #
def _preparar_cliente(nombre: str, estado: str, saldo) -> dict:
    """Construye el cliente y verifica que esté habilitado para operar.

    Raises:
        DatoInvalidoError: si algún campo no cumple su formato.
        ClienteBloqueadoError: si el cliente no está ACTIVO.
    """
    cliente = crear_cliente(nombre, estado, saldo)
    return validar_cliente(cliente)


def _autorizar_debito(cliente: dict, detalle: dict) -> dict:
    """Verifica el saldo y aplica el débito, devolviendo el cliente actualizado.

    Raises:
        SaldoInsuficienteError: si el saldo no cubre el total a debitar.
    """
    validar_saldo_suficiente(cliente, detalle["total"])
    return debitar(cliente, detalle["total"])


def _asentar_transaccion(
        operador: dict,
        cliente: dict,
        cliente_actualizado: dict,
        detalle: dict,
) -> tuple[dict, dict]:
    """Registra el pago y emite su comprobante.

    Devuelve `(pago_registrado, comprobante)`. El número del comprobante se
    deriva del secuencial que el repositorio asignó al pago, de modo que
    ambos documentos comparten la misma numeración.
    """
    pago = construir_pago(operador, cliente, cliente_actualizado, detalle)
    pago_registrado = registrar_pago(pago)
    comprobante = generar_comprobante(
        pago_registrado, obtener_secuencial(pago_registrado)
    )
    return pago_registrado, comprobante


def _armar_resultado(
        cliente: dict,
        cliente_actualizado: dict,
        detalle: dict,
        pago: dict,
        comprobante: dict,
) -> dict:
    """Empaqueta todo lo producido por la transacción.

    La capa de presentación recibe este único diccionario y decide qué mostrar,
    sin tener que recomponer nada.
    """
    return {
        "cliente": cliente,
        "cliente_actualizado": cliente_actualizado,
        "detalle": detalle,
        "pago": pago,
        "comprobante": comprobante,
        "saldo_anterior": obtener_saldo(cliente),
        "saldo_nuevo": obtener_saldo(cliente_actualizado),
    }


# --------------------------------------------------------------------------- #
# Caso de uso principal (FUNCIÓN REQUERIDA)
# --------------------------------------------------------------------------- #
def procesar_pago(nombre: str, estado: str, saldo, servicio: str, valor) -> dict:
    """Procesa el pago de un servicio de principio a fin. [FUNCIÓN REQUERIDA]

    Args:
        nombre: nombre del cliente.
        estado: ACTIVO o BLOQUEADO.
        saldo: saldo disponible del cliente.
        servicio: AGUA, LUZ, INTERNET o TELEFONIA.
        valor: valor del servicio a pagar.

    Returns:
        Diccionario con el cliente actualizado, el detalle del cálculo, el
        pago registrado y el comprobante emitido.

    Raises:
        TurnoNoIniciadoError: si no hay turno de caja abierto.
        DatoInvalidoError: si algún dato ingresado no cumple su formato.
        ClienteBloqueadoError: si el cliente no está ACTIVO.
        ServicioNoDisponibleError: si el servicio no existe.
        MontoInvalidoError: si el valor no es cobrable.
        SaldoInsuficienteError: si el saldo no cubre el total.
    """
    operador = exigir_turno_activo()

    try:
        cliente = _preparar_cliente(nombre, estado, saldo)
        detalle = calcular_detalle(servicio, valor)
        cliente_actualizado = _autorizar_debito(cliente, detalle)

        pago, comprobante = _asentar_transaccion(
            operador, cliente, cliente_actualizado, detalle
        )
        auditar_pago_aprobado(operador, pago, comprobante)

        return _armar_resultado(
            cliente, cliente_actualizado, detalle, pago, comprobante
        )

    except ErrorSistemaPagos as error:
        auditar_pago_rechazado(operador, _identificar_cliente(nombre), error)
        raise


def _identificar_cliente(nombre: str) -> str:
    """Devuelve un identificador del cliente utilizable en la auditoría.
    """
    texto = str(nombre).strip() if nombre else ""
    return texto or CLIENTE_NO_IDENTIFICADO


# --------------------------------------------------------------------------- #
# Formato para presentación (devuelve texto, no imprime)
# --------------------------------------------------------------------------- #
def obtener_comprobante_impreso(resultado: dict) -> str:
    """Devuelve el comprobante del resultado listo para mostrar en pantalla."""
    return renderizar_comprobante(resultado["comprobante"])


def describir_resultado(resultado: dict) -> str:
    """Resume la transacción en dos líneas: cálculo aplicado y estado final.

    Ejemplo:
    `LUZ | Valor: $ 37.45 | Comisión (2%): $ 0.75 | Total: $ 38.20`
    `Juan Pérez | ACTIVO | $ 61.80`
    """
    return (
        f"{describir_detalle(resultado['detalle'])}\n"
        f"{describir_cliente(resultado['cliente_actualizado'])}"
    )