"""Reglas de negocio del turno de caja y su operador responsable.

En una ventanilla física la identidad del cajero ya está verificada por su
presencia: no se autentica, se REGISTRA quién está a cargo de la caja. Este
módulo modela ese turno, que es lo que convierte cada pago y cada registro de
auditoría en un hecho trazable a una persona.

Regla central del sistema: sin turno abierto no hay operación posible.

El turno se representa como un `dict` con las claves:
    nombre | codigo | inicio | fin

`fin` vale `None` mientras el turno está abierto. Igual que en `clientes.py`,
las funciones que cambian el estado devuelven un turno NUEVO en lugar de
modificar el recibido.
"""

from datetime import datetime, timedelta

from config.constantes import (
    FORMATO_FECHA_HORA,
    LONGITUD_MAXIMA_NOMBRE,
    LONGITUD_MINIMA_NOMBRE,
    LONGITUD_SECUENCIAL_TURNO,
    PREFIJO_TURNO,
)
from core.excepciones import DatoInvalidoError, TurnoNoIniciadoError
from core.validaciones import validar_nombre_persona, validar_entero_positivo

CAMPO_OPERADOR = "nombre del operador"
CAMPO_SECUENCIAL = "secuencial del turno"

TURNO_SIN_ASIGNAR = None


# --------------------------------------------------------------------------- #
# Validación de campos
# --------------------------------------------------------------------------- #
def validar_nombre_operador(nombre: str) -> str:
    """Valida el nombre del operador y lo devuelve capitalizado.

    Reutiliza el mismo validador que el cliente: ambos son nombres de persona
    y no tiene sentido duplicar la regla.
    """
    return validar_nombre_persona(
        CAMPO_OPERADOR, nombre, LONGITUD_MINIMA_NOMBRE, LONGITUD_MAXIMA_NOMBRE
    )


def validar_secuencial(secuencial: int) -> int:
    """Verifica que el secuencial del turno sea un entero positivo."""
    return validar_entero_positivo(CAMPO_SECUENCIAL, secuencial)


# --------------------------------------------------------------------------- #
# Construcción
# --------------------------------------------------------------------------- #
def formatear_codigo_turno(secuencial: int) -> str:
    """Construye el código del turno con ceros a la izquierda: `TRN-000001`."""
    numero = validar_secuencial(secuencial)
    return f"{PREFIJO_TURNO}-{numero:0{LONGITUD_SECUENCIAL_TURNO}d}"


def iniciar_turno(nombre: str, secuencial: int) -> dict:
    """Abre un turno de caja para el operador indicado.

    El secuencial lo provee la capa de aplicación, que es la que lleva el
    conteo. Así este módulo se mantiene como lógica pura de negocio.
    """
    return {
        "nombre": validar_nombre_operador(nombre),
        "codigo": formatear_codigo_turno(secuencial),
        "inicio": datetime.now(),
        "fin": None,
    }


def cerrar_turno(operador: dict) -> dict:
    """Cierra el turno y devuelve una copia con la hora de cierre registrada.

    Raises:
        TurnoNoIniciadoError: si no hay un turno abierto que cerrar.
    """
    validar_turno_activo(operador)

    turno_cerrado = dict(operador)
    turno_cerrado["fin"] = datetime.now()
    return turno_cerrado


# --------------------------------------------------------------------------- #
# Predicados (consultas sin efectos secundarios)
# --------------------------------------------------------------------------- #
def esta_en_turno(operador: dict | None) -> bool:
    """Indica si hay un turno abierto (existe y aún no ha sido cerrado)."""
    return bool(operador) and operador.get("fin") is None


def es_el_mismo_operador(operador: dict | None, nombre: str) -> bool:
    """Indica si el nombre corresponde al operador que ya está en turno."""
    if not operador:
        return False
    return operador.get("nombre") == validar_nombre_operador(nombre)


def obtener_nombre(operador: dict) -> str:
    """Devuelve el nombre del operador responsable del turno."""
    return operador["nombre"]


def obtener_codigo(operador: dict) -> str:
    """Devuelve el código del turno: `TRN-000001`."""
    return operador["codigo"]


def calcular_duracion(operador: dict) -> timedelta:
    """Calcula el tiempo transcurrido del turno.

    Si el turno sigue abierto, mide hasta el instante actual.
    """
    momento_final = operador.get("fin") or datetime.now()
    return momento_final - operador["inicio"]


# --------------------------------------------------------------------------- #
# Reglas de negocio
# --------------------------------------------------------------------------- #
def validar_turno_activo(operador: dict | None) -> dict:
    """Exige un turno abierto para poder operar. [PRECONDICIÓN DEL SISTEMA]

    Toda operación que genere un registro (pago o auditoría) debe pasar por
    aquí primero: es lo que impide que exista un movimiento sin responsable.

    Raises:
        TurnoNoIniciadoError: si no hay turno abierto.
    """
    if not esta_en_turno(operador):
        raise TurnoNoIniciadoError()
    return operador


def validar_cambio_de_turno(operador: dict | None, nuevo_nombre: str) -> str:
    """Valida el relevo de caja y devuelve el nombre del operador entrante.

    Un cambio de turno hacia la misma persona no es un relevo: es un error de
    digitación. Se rechaza para no partir la trazabilidad de la jornada en dos
    turnos artificiales.

    Raises:
        TurnoNoIniciadoError: si no hay turno vigente que relevar.
        DatoInvalidoError: si el operador entrante es el mismo que el saliente.
    """
    validar_turno_activo(operador)
    nombre_entrante = validar_nombre_operador(nuevo_nombre)

    if es_el_mismo_operador(operador, nombre_entrante):
        raise DatoInvalidoError(
            CAMPO_OPERADOR,
            f"'{nombre_entrante}' ya se encuentra en turno. "
            f"Un relevo requiere un operador distinto.",
        )
    return nombre_entrante


def relevar(operador: dict, nuevo_nombre: str, secuencial: int) -> tuple[dict, dict]:
    """Ejecuta el relevo de caja completo.

    Devuelve la tupla `(turno_saliente_cerrado, turno_entrante_abierto)`. Se
    devuelven ambos porque la auditoría necesita dejar constancia de los dos
    hechos: quién cerró y quién abrió.
    """
    nombre_entrante = validar_cambio_de_turno(operador, nuevo_nombre)
    return cerrar_turno(operador), iniciar_turno(nombre_entrante, secuencial)


# --------------------------------------------------------------------------- #
# Formato para presentación (devuelve texto, no imprime)
# --------------------------------------------------------------------------- #
def describir_duracion(operador: dict) -> str:
    """Devuelve la duración del turno en formato legible: `2h 15m`."""
    minutos_totales = int(calcular_duracion(operador).total_seconds() // 60)
    horas, minutos = divmod(minutos_totales, 60)
    return f"{horas}h {minutos:02d}m"


def describir_operador(operador: dict | None) -> str:
    """Devuelve la firma del operador: `Ana Torres (TRN-000001)`.

    Es el texto que acompaña a cada comprobante y a cada línea de auditoría.
    """
    if not operador:
        return "Sin operador en turno"
    return f"{obtener_nombre(operador)} ({obtener_codigo(operador)})"


def describir_turno(operador: dict) -> str:
    """Devuelve el detalle completo del turno para el cierre de caja.

    Ejemplo: `TRN-000001 | Ana Torres | 2026-07-26 08:00:00 → 2026-07-26 10:15:00 | 2h 15m`
    """
    inicio = operador["inicio"].strftime(FORMATO_FECHA_HORA)
    fin = operador["fin"].strftime(FORMATO_FECHA_HORA) if operador["fin"] else "EN CURSO"
    return (
        f"{obtener_codigo(operador)} | {obtener_nombre(operador)} | "
        f"{inicio} → {fin} | {describir_duracion(operador)}"
    )