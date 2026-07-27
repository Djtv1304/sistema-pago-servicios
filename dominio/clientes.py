"""Reglas de negocio del cliente de la cooperativa.

Contiene la función obligatoria `validar_cliente()` y las reglas asociadas al
estado y al saldo. No hay `input()` ni `print()`: los datos llegan ya
capturados desde la capa de presentación.

El cliente se representa como un `dict` con las claves:
    nombre | estado | saldo
"""

from decimal import Decimal

from config.constantes import (
    ESTADO_CLIENTE_ACTIVO,
    ESTADOS_CLIENTE_VALIDOS,
    LONGITUD_MAXIMA_NOMBRE,
    LONGITUD_MINIMA_NOMBRE,
)
from core.dinero import alcanza_para, es_mayor_que_cero, formatear, restar
from core.excepciones import (
    ClienteBloqueadoError,
    DatoInvalidoError,
    SaldoInsuficienteError,
)
from core.validaciones import (
    validar_monto_no_negativo,
    validar_nombre_persona,
    validar_opcion,
)

CAMPO_NOMBRE = "nombre del cliente"
CAMPO_ESTADO = "estado del cliente"
CAMPO_SALDO = "saldo disponible"
CAMPO_DEBITO = "monto a debitar"


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


# --------------------------------------------------------------------------- #
# Construcción
# --------------------------------------------------------------------------- #
def crear_cliente(nombre: str, estado: str, saldo) -> dict:
    """Construye un cliente con todos sus campos validados.

    Es el único constructor permitido: si un cliente existe, está bien formado.
    """
    return {
        "nombre": validar_nombre(nombre),
        "estado": validar_estado(estado),
        "saldo": validar_saldo(saldo),
    }


# --------------------------------------------------------------------------- #
# Predicados (consultas sin efectos secundarios)
# --------------------------------------------------------------------------- #
def esta_activo(cliente: dict) -> bool:
    """Indica si el cliente se encuentra en estado ACTIVO."""
    return bool(cliente) and cliente.get("estado") == ESTADO_CLIENTE_ACTIVO


def obtener_saldo(cliente: dict) -> Decimal:
    """Devuelve el saldo disponible del cliente."""
    return cliente["saldo"]


def tiene_saldo_suficiente(cliente: dict, total_a_debitar: Decimal) -> bool:
    """Indica si el saldo cubre el total a debitar (valor del servicio + comisión)."""
    return alcanza_para(obtener_saldo(cliente), total_a_debitar)


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

    La comparación se hace contra el TOTAL (servicio + comisión), nunca contra
    el valor del servicio: validar solo el valor dejaría la cuenta en negativo
    al cobrar la comisión.

    Raises:
        SaldoInsuficienteError: si el saldo no alcanza.
    """
    if not tiene_saldo_suficiente(cliente, total_a_debitar):
        raise SaldoInsuficienteError(
            formatear(obtener_saldo(cliente)), formatear(total_a_debitar)
        )
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


# --------------------------------------------------------------------------- #
# Formato para presentación (devuelve texto, no imprime)
# --------------------------------------------------------------------------- #
def describir_cliente(cliente: dict) -> str:
    """Devuelve el resumen del cliente: `Juan Pérez | ACTIVO | $ 100.00`."""
    return (
        f"{cliente['nombre']} | {cliente['estado']} | "
        f"{formatear(obtener_saldo(cliente))}"
    )