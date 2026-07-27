"""Reglas de negocio del pago de servicios.

Contiene las funciones obligatorias `validar_monto()` y `calcular_comision()`,
junto con el armado del registro de pago.

Este módulo NO valida al cliente ni al operador: esas reglas viven en sus
propios archivos y `procesar_pago()` las encadena. Aquí solo se responde a
"¿cuánto se cobra y qué quedó registrado?".

El pago se representa como un `dict` con las claves:
    fecha | operador | turno | cliente | servicio | descripcion_servicio |
    valor | porcentaje_comision | comision | total | saldo_anterior | saldo_nuevo
"""

from datetime import datetime
from decimal import Decimal

from config.constantes import (
    FORMATO_FECHA_HORA,
    MONTO_MINIMO_PAGO,
    PORCENTAJE_COMISION,
)
from core.dinero import (
    aplicar_porcentaje,
    esta_en_rango,
    formatear,
    formatear_porcentaje,
    sumar,
)
from core.excepciones import DatoInvalidoError, MontoInvalidoError
from core.validaciones import validar_monto_positivo
from dominio.clientes import obtener_saldo
from dominio.operadores import obtener_codigo, obtener_nombre, validar_turno_activo
from dominio.servicios import (
    obtener_descripcion,
    obtener_monto_maximo,
    validar_servicio,
)

CAMPO_VALOR = "valor del servicio"


# --------------------------------------------------------------------------- #
# Reglas de negocio: validación del monto
# --------------------------------------------------------------------------- #
def validar_monto(valor, servicio: str | None = None) -> Decimal:
    """Verifica que el valor del servicio sea cobrable. [FUNCIÓN REQUERIDA]

    Aplica dos niveles de control:
      1. El monto debe ser numérico y estrictamente mayor que cero.
      2. Si se indica el servicio, debe respetar además su tope específico.

    El tope por servicio no es una restricción arbitraria: una planilla de agua
    de $4.000 es un error de digitación, y detenerlo antes de debitar evita
    tener que reversar la transacción después.

    Args:
        valor: monto ingresado, en cualquier formato convertible a Decimal.
        servicio: nombre del servicio. Si es `None`, solo se valida el mínimo.

    Raises:
        MontoInvalidoError: si el valor no es numérico, no es positivo o
            excede el tope permitido.
    """
    try:
        monto = validar_monto_positivo(CAMPO_VALOR, valor)
    except DatoInvalidoError as error:
        raise MontoInvalidoError(str(error.detalle)) from error

    if servicio is None:
        return monto

    servicio_valido = validar_servicio(servicio)
    monto_maximo = obtener_monto_maximo(servicio_valido)

    if not esta_en_rango(monto, MONTO_MINIMO_PAGO, monto_maximo):
        raise MontoInvalidoError(
            f"El valor de {servicio_valido} debe estar entre "
            f"{formatear(MONTO_MINIMO_PAGO)} y {formatear(monto_maximo)}. "
            f"Valor ingresado: {formatear(monto)}."
        )
    return monto


# --------------------------------------------------------------------------- #
# Reglas de negocio: cálculo
# --------------------------------------------------------------------------- #
def calcular_comision(valor: Decimal) -> Decimal:
    """Calcula la comisión de la cooperativa sobre el valor del servicio.
    [FUNCIÓN REQUERIDA]

    La comisión se aplica SOBRE EL VALOR DEL SERVICIO, no sobre el total: es
    un cargo por la gestión de recaudación, no un impuesto sobre sí mismo.

    Ejemplo: $37.45 al 2% -> $0.75 (redondeo comercial de $0.7490).
    """
    return aplicar_porcentaje(valor, PORCENTAJE_COMISION)


def calcular_total_a_debitar(valor: Decimal, comision: Decimal) -> Decimal:
    """Calcula el monto real que se descuenta de la cuenta del cliente.

    Es el único valor contra el que debe compararse el saldo disponible.
    """
    return sumar(valor, comision)


def calcular_detalle(servicio: str, valor) -> dict:
    """Resuelve el cálculo completo de una transacción, ya validado.

    Concentra en una sola llamada lo que de otro modo serían tres pasos
    encadenados y propensos a olvidarse alguno (validar, comisionar, totalizar).

    Devuelve: servicio | valor | porcentaje_comision | comision | total
    """
    servicio_valido = validar_servicio(servicio)
    monto = validar_monto(valor, servicio_valido)
    comision = calcular_comision(monto)

    return {
        "servicio": servicio_valido,
        "valor": monto,
        "porcentaje_comision": PORCENTAJE_COMISION,
        "comision": comision,
        "total": calcular_total_a_debitar(monto, comision),
    }


# --------------------------------------------------------------------------- #
# Construcción del registro de pago
# --------------------------------------------------------------------------- #
def construir_pago(
        operador: dict,
        cliente: dict,
        cliente_actualizado: dict,
        detalle: dict,
) -> dict:
    """Arma el registro histórico de un pago ya autorizado.

    Se invoca DESPUÉS de debitar, nunca antes: un pago solo existe cuando el
    saldo ya se afectó. Por eso recibe los dos estados del cliente, para dejar
    asentado el saldo anterior y el nuevo.

    El operador se exige activo aquí también, no por desconfianza del
    llamador, sino porque esta es la función que estampa la firma: si el turno
    se cerró en el intermedio, el pago no puede quedar sin responsable.

    Raises:
        TurnoNoIniciadoError: si no hay un turno de caja abierto.
    """
    validar_turno_activo(operador)

    return {
        "fecha": datetime.now(),
        "operador": obtener_nombre(operador),
        "turno": obtener_codigo(operador),
        "cliente": cliente["nombre"],
        "servicio": detalle["servicio"],
        "descripcion_servicio": obtener_descripcion(detalle["servicio"]),
        "valor": detalle["valor"],
        "porcentaje_comision": detalle["porcentaje_comision"],
        "comision": detalle["comision"],
        "total": detalle["total"],
        "saldo_anterior": obtener_saldo(cliente),
        "saldo_nuevo": obtener_saldo(cliente_actualizado),
    }


# --------------------------------------------------------------------------- #
# Consultas sobre pagos registrados (sin efectos secundarios)
# --------------------------------------------------------------------------- #
def obtener_total(pago: dict) -> Decimal:
    """Devuelve el monto debitado en el pago."""
    return pago["total"]


def obtener_comision(pago: dict) -> Decimal:
    """Devuelve la comisión cobrada en el pago."""
    return pago["comision"]


def es_del_turno(pago: dict, codigo_turno: str) -> bool:
    """Indica si el pago fue registrado durante el turno consultado."""
    return pago["turno"] == codigo_turno


def es_del_servicio(pago: dict, servicio: str) -> bool:
    """Indica si el pago corresponde al servicio consultado."""
    return pago["servicio"] == validar_servicio(servicio)


# --------------------------------------------------------------------------- #
# Totalizadores (reutilizables para el cierre de caja)
# --------------------------------------------------------------------------- #
def totalizar(pagos, extractor=obtener_total) -> Decimal:
    """Suma una magnitud a lo largo de una colección de pagos.

    El `extractor` decide QUÉ se suma, así una sola función sirve para todos
    los totales del cierre de caja:

        totalizar(pagos)                     -> total recaudado
        totalizar(pagos, obtener_comision)   -> total de comisiones
    """
    return sumar(*(extractor(pago) for pago in pagos))


def contar_por_servicio(pagos) -> dict:
    """Devuelve cuántos pagos se registraron por cada servicio.

    Solo incluye los servicios con al menos un pago.
    """
    conteo = {}
    for pago in pagos:
        servicio = pago["servicio"]
        conteo[servicio] = conteo.get(servicio, 0) + 1
    return conteo


# --------------------------------------------------------------------------- #
# Formato para presentación (devuelve texto, no imprime)
# --------------------------------------------------------------------------- #
def describir_detalle(detalle: dict) -> str:
    """Resume el cálculo previo a la confirmación.

    Ejemplo: `LUZ | Valor: $ 37.45 | Comisión (2%): $ 0.75 | Total: $ 38.20`
    """
    return (
        f"{detalle['servicio']} | "
        f"Valor: {formatear(detalle['valor'])} | "
        f"Comisión ({formatear_porcentaje(detalle['porcentaje_comision'])}): "
        f"{formatear(detalle['comision'])} | "
        f"Total: {formatear(detalle['total'])}"
    )


def describir_pago(pago: dict) -> str:
    """Resume un pago en una línea, para el historial.

    Ejemplo:
    `2026-07-26 10:15:00 | Juan Pérez | LUZ | $ 38.20 | Ana Torres (TRN-000001)`
    """
    return (
        f"{pago['fecha'].strftime(FORMATO_FECHA_HORA)} | "
        f"{pago['cliente']} | {pago['servicio']} | "
        f"{formatear(obtener_total(pago))} | "
        f"{pago['operador']} ({pago['turno']})"
    )