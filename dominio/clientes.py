"""Reglas de negocio del cliente de la cooperativa.

Contiene la función obligatoria `validar_cliente()` y las reglas asociadas al
estado y al saldo. No hay `input()` ni `print()`: los datos llegan ya
capturados desde la capa de presentación.

El cliente se representa como un `dict` con las claves:
    nombre | estado | saldo
"""

from decimal import Decimal

from types import MappingProxyType

from config.constantes import (
    ESTADO_CLIENTE_ACTIVO,
    ESTADOS_CLIENTE_VALIDOS,
    LONGITUD_MAXIMA_NOMBRE,
    LONGITUD_MINIMA_NOMBRE,
    ESTADO_CLIENTE_BLOQUEADO,
    MONTO_MINIMO_PAGO,
)
from core.dinero import alcanza_para, es_mayor_que_cero, formatear, restar
from core.excepciones import (
    ClienteBloqueadoError,
    DatoInvalidoError,
    SaldoInsuficienteError,
    ServicioYaPagadoError,
    SinServiciosPendientesError,
)
from core.validaciones import (
    validar_monto_no_negativo,
    validar_nombre_persona,
    validar_opcion,
    validar_monto_en_rango,
)
from dominio.servicios import listar_servicios, validar_servicio, obtener_monto_maximo

CAMPO_NOMBRE = "nombre del cliente"
CAMPO_ESTADO = "estado del cliente"
CAMPO_SALDO = "saldo disponible"
CAMPO_DEBITO = "monto a debitar"
CAMPO_PENDIENTES = "servicios pendientes"
CAMPO_VALORES = "valores de servicios"
ETIQUETA_AL_DIA = "AL DÍA"

SIN_VALORES = MappingProxyType({})

# --------------------------------------------------------------------------- #
# Validación de campos
# --------------------------------------------------------------------------- #
def validar_nombre(nombre: str) -> str:
    """Valida el nombre del cliente y lo devuelve capitalizado."""
    return validar_nombre_persona(
        CAMPO_NOMBRE, nombre, LONGITUD_MINIMA_NOMBRE, LONGITUD_MAXIMA_NOMBRE
    )


def validar_estado(estado: str) -> str:
    """Valida que el estado sea ACTIVO o BLOQUEADO.

    Acepta la entrada en cualquier combinación de mayúsculas o con tildes, y
    devuelve el valor exacto del catálogo.
    """
    return validar_opcion(CAMPO_ESTADO, estado, ESTADOS_CLIENTE_VALIDOS)


def validar_saldo(saldo) -> Decimal:
    """Valida el saldo disponible: numérico y nunca negativo.

    Se permite el cero (una cuenta sin fondos es un estado válido); lo que se
    rechaza es un saldo negativo, que sería un sobregiro no contemplado.
    """
    return validar_monto_no_negativo(CAMPO_SALDO, saldo)

def validar_pendientes(servicios=None) -> tuple[str, ...]:
    """Valida la lista de servicios por pagar y la devuelve normalizada.

    Sin argumento, un cliente nuevo arranca debiendo TODOS los servicios del
    catálogo
    """
    if servicios is None:
        return tuple(listar_servicios())

    validados = {validar_servicio(servicio) for servicio in servicios}
    return tuple(s for s in listar_servicios() if s in validados)

def validar_valores_servicios(valores=None) -> MappingProxyType:
    """Valida los importes preasignados por servicio y los devuelve inmutables.
    """
    if not valores:
        return SIN_VALORES

    validados = {}
    for servicio, monto in valores.items():
        servicio_valido = validar_servicio(servicio)
        validados[servicio_valido] = validar_monto_en_rango(
            f"{CAMPO_VALORES} ({servicio_valido})",
            monto,
            MONTO_MINIMO_PAGO,
            obtener_monto_maximo(servicio_valido),
        )
    return MappingProxyType(validados)


# --------------------------------------------------------------------------- #
# Construcción
# --------------------------------------------------------------------------- #
def crear_cliente(
        nombre: str,
        estado: str,
        saldo,
        servicios_pendientes=None,
        valores_servicios=None,
) -> dict:
    """Construye un cliente con todos sus campos validados.
    """
    return {
        "nombre": validar_nombre(nombre),
        "estado": validar_estado(estado),
        "saldo": validar_saldo(saldo),
        "servicios_pendientes": validar_pendientes(servicios_pendientes),
        "valores_servicios": validar_valores_servicios(valores_servicios),
    }


# --------------------------------------------------------------------------- #
# Predicados (consultas sin efectos secundarios)
# --------------------------------------------------------------------------- #
def esta_activo(cliente: dict) -> bool:
    """Indica si el cliente se encuentra en estado ACTIVO."""
    return bool(cliente) and cliente.get("estado") == ESTADO_CLIENTE_ACTIVO


def esta_bloqueado(cliente: dict) -> bool:
    """Indica si el cliente se encuentra BLOQUEADO."""
    return not esta_activo(cliente)

def estado_opuesto(cliente: dict) -> str:
    """Devuelve el estado contrario al actual.

    Con solo dos estados posibles, proponer el opuesto evita que el operador
    tenga que digitarlo: un cliente activo solo puede pasar a bloqueado.
    """
    return ESTADO_CLIENTE_BLOQUEADO if esta_activo(cliente) else ESTADO_CLIENTE_ACTIVO

def obtener_saldo(cliente: dict) -> Decimal:
    """Devuelve el saldo disponible del cliente."""
    return cliente["saldo"]


def tiene_saldo_suficiente(cliente: dict, total_a_debitar: Decimal) -> bool:
    """Indica si el saldo cubre el total a debitar (valor del servicio + comisión)."""
    return alcanza_para(obtener_saldo(cliente), total_a_debitar)


def obtener_pendientes(cliente: dict) -> tuple[str, ...]:
    """Devuelve los servicios que el cliente aún no ha pagado."""
    return cliente["servicios_pendientes"]


def contar_pendientes(cliente: dict) -> int:
    """Devuelve cuántos servicios le quedan por pagar."""
    return len(obtener_pendientes(cliente))


def tiene_pendientes(cliente: dict) -> bool:
    """Indica si al cliente le queda algún servicio por pagar."""
    return contar_pendientes(cliente) > 0


def esta_pendiente(cliente: dict, servicio: str) -> bool:
    """Indica si un servicio específico sigue impago."""
    return validar_servicio(servicio) in obtener_pendientes(cliente)


def obtener_valores(cliente: dict) -> MappingProxyType:
    """Devuelve los importes preasignados del cliente."""
    return cliente["valores_servicios"]


def tiene_valores_asignados(cliente: dict) -> bool:
    """Indica si el cliente llega con planilla precargada."""
    return bool(obtener_valores(cliente))


def obtener_valor_servicio(cliente: dict, servicio: str) -> Decimal | None:
    """Devuelve el importe preasignado de un servicio, o `None` si no lo tiene.

    `None` significa 'este cliente no trae planilla para ese servicio', y es
    la señal que usa la presentación para pedir el valor al operador.
    """
    return obtener_valores(cliente).get(validar_servicio(servicio))


# --------------------------------------------------------------------------- #
# Reglas de negocio
# --------------------------------------------------------------------------- #
def validar_cliente(cliente: dict) -> dict:
    """Verifica que el cliente esté habilitado para operar. [FUNCIÓN REQUERIDA]

    Raises:
        ClienteBloqueadoError: si el cliente no está en estado ACTIVO.
    """
    if not esta_activo(cliente):
        raise ClienteBloqueadoError(cliente.get("nombre", "desconocido"))
    return cliente


def validar_saldo_suficiente(cliente: dict, total_a_debitar: Decimal) -> dict:
    """Verifica que el cliente pueda cubrir el total a debitar.

    Raises:
        SaldoInsuficienteError: si el saldo no alcanza.
    """
    if not tiene_saldo_suficiente(cliente, total_a_debitar):
        raise SaldoInsuficienteError(obtener_saldo(cliente), total_a_debitar)
    return cliente


def debitar(cliente: dict, monto: Decimal) -> dict:
    """Descuenta un monto del saldo y devuelve un cliente NUEVO.

    No modifica el cliente recibido: devuelve una copia con el saldo
    actualizado. Así, si un paso posterior falla, el cliente original queda
    intacto y no existen estados a medio aplicar.

    Raises:
        DatoInvalidoError: si el monto no es positivo.
        SaldoInsuficienteError: si el saldo no cubre el débito.
    """
    if not es_mayor_que_cero(monto):
        raise DatoInvalidoError(CAMPO_DEBITO, "debe ser mayor que cero.")

    validar_saldo_suficiente(cliente, monto)

    cliente_actualizado = dict(cliente)
    cliente_actualizado["saldo"] = restar(obtener_saldo(cliente), monto)
    return cliente_actualizado

def validar_tiene_pendientes(cliente: dict) -> dict:
    """Exige que al cliente le quede algo por pagar.

    Raises:
        SinServiciosPendientesError: si ya canceló todos sus servicios.
    """
    if not tiene_pendientes(cliente):
        raise SinServiciosPendientesError(cliente["nombre"])
    return cliente


def validar_servicio_pendiente(cliente: dict, servicio: str) -> str:
    """Exige que el servicio siga impago para ese cliente.

    Raises:
        ServicioYaPagadoError: si el cliente ya canceló ese servicio.
    """
    servicio_valido = validar_servicio(servicio)

    if not esta_pendiente(cliente, servicio_valido):
        raise ServicioYaPagadoError(cliente["nombre"], servicio_valido)
    return servicio_valido


def marcar_servicio_pagado(cliente: dict, servicio: str) -> dict:
    """Retira un servicio de los pendientes y devuelve un cliente NUEVO.

    Raises:
        ServicioYaPagadoError: si el servicio ya estaba cancelado.
    """
    pagado = validar_servicio_pendiente(cliente, servicio)

    cliente_actualizado = dict(cliente)
    cliente_actualizado["servicios_pendientes"] = tuple(
        s for s in obtener_pendientes(cliente) if s != pagado
    )
    return cliente_actualizado

def cambiar_estado(cliente: dict, nuevo_estado: str) -> dict:
    """Cambia el estado del cliente y devuelve un cliente NUEVO.

    Raises:
        DatoInvalidoError: si el estado es inválido o igual al vigente.
    """
    estado_validado = validar_estado(nuevo_estado)

    if estado_validado == cliente["estado"]:
        raise DatoInvalidoError(
            CAMPO_ESTADO,
            f"'{cliente['nombre']}' ya se encuentra en estado {estado_validado}.",
        )

    cliente_actualizado = dict(cliente)
    cliente_actualizado["estado"] = estado_validado
    return cliente_actualizado


# --------------------------------------------------------------------------- #
# Formato para presentación (devuelve texto, no imprime)
# --------------------------------------------------------------------------- #
def describir_pendientes(cliente: dict) -> str:
    """Resume los servicios por pagar: `AGUA, INTERNET` o `AL DÍA`."""
    pendientes = obtener_pendientes(cliente)
    return ", ".join(pendientes) if pendientes else ETIQUETA_AL_DIA


def describir_cliente(cliente: dict) -> str:
    """Resume al cliente: `Juan Pérez | ACTIVO | $ 61.80 | Pendientes: AGUA, LUZ`."""
    return (
        f"{cliente['nombre']} | {cliente['estado']} | "
        f"{formatear(obtener_saldo(cliente))} | "
        f"Pendientes: {describir_pendientes(cliente)}"
    )