"""Reglas de negocio del catálogo de servicios básicos.

Contiene la función obligatoria `validar_servicio()` y las consultas sobre el
catálogo. Este módulo es la ÚNICA puerta de acceso a `SERVICIOS_DISPONIBLES`:
ningún otro archivo del sistema debe leer ese diccionario directamente.

Esa restricción es deliberada. Si mañana el catálogo pasa de un `dict` en
`config/` a una tabla en base de datos, solo cambian las funciones de este
archivo y el resto del sistema no se entera.

El servicio se identifica por su nombre en el catálogo (`AGUA`, `LUZ`,
`INTERNET`, `TELEFONIA`) y cada uno expone: codigo | descripcion | monto_maximo
"""

from decimal import Decimal

from config.constantes import MONTO_MAXIMO_PAGO, SERVICIOS_DISPONIBLES
from core.dinero import formatear
from core.excepciones import DatoInvalidoError, ServicioNoDisponibleError
from core.validaciones import validar_opcion

CAMPO_SERVICIO = "servicio"


# --------------------------------------------------------------------------- #
# Consultas al catálogo (sin efectos secundarios)
# --------------------------------------------------------------------------- #
def listar_servicios() -> tuple[str, ...]:
    """Devuelve los nombres de los servicios habilitados, en orden de catálogo."""
    return tuple(SERVICIOS_DISPONIBLES.keys())


def existe_servicio(servicio: str) -> bool:
    """Indica si el servicio pertenece al catálogo, sin lanzar excepción.

    Útil para consultar antes de decidir, cuando un error no es la respuesta
    esperada.
    """
    try:
        validar_servicio(servicio)
        return True
    except ServicioNoDisponibleError:
        return False


def obtener_definicion(servicio: str) -> dict:
    """Devuelve una COPIA de la ficha del servicio validado.

    Se devuelve copia para que ningún módulo pueda alterar el catálogo por
    accidente al manipular el resultado.
    """
    return dict(SERVICIOS_DISPONIBLES[validar_servicio(servicio)])


def obtener_descripcion(servicio: str) -> str:
    """Devuelve el nombre comercial del servicio: `AGUA` -> `Agua Potable`."""
    return obtener_definicion(servicio)["descripcion"]


def obtener_codigo(servicio: str) -> str:
    """Devuelve el código corto del servicio, usado en el comprobante: `AGU`."""
    return obtener_definicion(servicio)["codigo"]


def obtener_monto_maximo(servicio: str) -> Decimal:
    """Devuelve el tope efectivo del servicio.

    Es el menor entre el tope propio del servicio y el tope global de la
    cooperativa: nunca puede autorizarse un pago por encima del límite
    institucional, aunque el catálogo del servicio permitiera más.
    """
    return min(obtener_definicion(servicio)["monto_maximo"], MONTO_MAXIMO_PAGO)


# --------------------------------------------------------------------------- #
# Reglas de negocio
# --------------------------------------------------------------------------- #
def validar_servicio(servicio: str) -> str:
    """Verifica que el servicio exista en el catálogo. [FUNCIÓN REQUERIDA]

    Acepta la entrada con cualquier combinación de mayúsculas, tildes o
    espacios sobrantes (`' telefonía '` -> `TELEFONIA`) y devuelve el nombre
    exacto del catálogo.

    Raises:
        ServicioNoDisponibleError: si el servicio no está habilitado.
    """
    try:
        return validar_opcion(CAMPO_SERVICIO, servicio, listar_servicios())
    except DatoInvalidoError as error:
        raise ServicioNoDisponibleError(servicio, listar_servicios()) from error