"""Gestión de la sesión de trabajo: el turno de caja vigente.

Este módulo es la CAPA DE APLICACIÓN del turno. La diferencia con
`dominio/operadores.py` es precisa:

  - `dominio/operadores.py` define QUÉ es un turno válido y cuándo un relevo
    es legítimo. Es lógica pura: recibe datos y devuelve datos.
  - `aplicacion/sesion.py` recuerda CUÁL es el turno vigente ahora mismo,
    lleva la numeración correlativa y coordina la auditoría de cada cambio.

Es el único módulo que conoce al operador actual. Ni el dominio ni el
repositorio de pagos lo consultan: se los pasa como parámetro.

Aquí vive la garantía de la regla central del sistema: `exigir_turno_activo()`
es la puerta por la que pasa toda operación del menú.
"""

from dominio.operadores import (
    describir_duracion,
    describir_operador,
    describir_turno,
    esta_en_turno,
    iniciar_turno,
    obtener_codigo,
    obtener_nombre,
    relevar,
    validar_turno_activo,
)
from core.excepciones import DatoInvalidoError
from infraestructura.auditoria import auditar_turno_cerrado, auditar_turno_iniciado
from infraestructura.repositorio_pagos import contar_por_turno

CAMPO_TURNO = "turno de caja"

# Estado de la sesión. Son los dos únicos datos que el sistema mantiene vivos
# entre una opción del menú y la siguiente.
_operador_actual: dict | None = None
_turnos_abiertos: int = 0


# --------------------------------------------------------------------------- #
# Numeración
# --------------------------------------------------------------------------- #
def _siguiente_secuencial_turno() -> int:
    """Devuelve el próximo número de turno y lo reserva.

    Se incrementa el contador ANTES de devolverlo para que ningún relevo
    pueda reutilizar un número ya emitido.
    """
    global _turnos_abiertos
    _turnos_abiertos += 1
    return _turnos_abiertos


# --------------------------------------------------------------------------- #
# Consultas del estado (sin efectos secundarios)
# --------------------------------------------------------------------------- #
def obtener_operador_actual() -> dict | None:
    """Devuelve el turno vigente, o `None` si no hay ninguno abierto."""
    return _operador_actual


def hay_turno_abierto() -> bool:
    """Indica si existe un turno de caja en curso."""
    return esta_en_turno(_operador_actual)


def contar_turnos_abiertos() -> int:
    """Devuelve cuántos turnos se han abierto durante la ejecución."""
    return _turnos_abiertos


def exigir_turno_activo() -> dict:
    """Devuelve el turno vigente exigiendo que exista. [PRECONDICIÓN DEL MENÚ]

    Toda opción del menú que registre un pago o consulte información debe
    invocar esta función primero. Es lo que impide que exista una operación
    sin responsable identificado.

    Raises:
        TurnoNoIniciadoError: si no hay turno abierto.
    """
    return validar_turno_activo(_operador_actual)


# --------------------------------------------------------------------------- #
# Apertura de la jornada
# --------------------------------------------------------------------------- #
def iniciar_jornada(nombre_operador: str) -> dict:
    """Abre el primer turno de la jornada y lo deja como turno vigente.

    Se invoca una sola vez, al arrancar el programa, antes de mostrar el menú.
    Si ya hay un turno abierto, la operación correcta es el relevo, no una
    segunda apertura: dos turnos simultáneos harían ambiguo quién responde
    por cada pago.

    Raises:
        DatoInvalidoError: si ya existe un turno abierto.
        DatoInvalidoError: si el nombre del operador no es válido.
    """
    global _operador_actual

    if hay_turno_abierto():
        raise DatoInvalidoError(
            CAMPO_TURNO,
            f"ya existe un turno abierto ({describir_operador(_operador_actual)}). "
            f"Para relevar al operador, use el cambio de turno.",
        )

    _operador_actual = iniciar_turno(nombre_operador, _siguiente_secuencial_turno())
    auditar_turno_iniciado(_operador_actual)
    return _operador_actual


# --------------------------------------------------------------------------- #
# Relevo de operador
# --------------------------------------------------------------------------- #
def cambiar_turno(nombre_entrante: str) -> tuple[dict, dict]:
    """Cierra el turno vigente y abre uno nuevo para el operador entrante.

    Devuelve `(turno_saliente, turno_entrante)` porque ambos hechos deben
    quedar asentados: la auditoría registra el cierre con su resumen y la
    apertura por separado.

    El orden importa: primero se resuelve el relevo completo en el dominio, y
    solo si no lanzó excepción se altera el estado de la sesión. Así un relevo
    rechazado deja al operador saliente en su turno, sin estados intermedios.

    Raises:
        TurnoNoIniciadoError: si no hay turno vigente que relevar.
        DatoInvalidoError: si el operador entrante es el mismo que el saliente.
    """
    global _operador_actual

    turno_vigente = exigir_turno_activo()
    pagos_del_turno = contar_por_turno(obtener_codigo(turno_vigente))

    saliente, entrante = relevar(
        turno_vigente, nombre_entrante, _siguiente_secuencial_turno()
    )

    _operador_actual = entrante

    auditar_turno_cerrado(saliente, describir_duracion(saliente), pagos_del_turno)
    auditar_turno_iniciado(entrante)
    return saliente, entrante


# --------------------------------------------------------------------------- #
# Cierre de la jornada
# --------------------------------------------------------------------------- #
def cerrar_jornada() -> dict:
    """Cierra el turno vigente y deja la sesión sin operador.

    Se invoca al salir del sistema. El cierre se audita ANTES de descartar el
    turno: de lo contrario no quedaría constancia de quién cerró la caja.

    Raises:
        TurnoNoIniciadoError: si no hay turno abierto que cerrar.
    """
    global _operador_actual

    turno_vigente = exigir_turno_activo()
    pagos_del_turno = contar_por_turno(obtener_codigo(turno_vigente))

    saliente = cerrar_turno_vigente(turno_vigente)
    auditar_turno_cerrado(saliente, describir_duracion(saliente), pagos_del_turno)

    _operador_actual = None
    return saliente


def cerrar_turno_vigente(turno: dict) -> dict:
    """Aplica el cierre del turno delegando la regla al dominio.

    Función intermedia deliberada: mantiene el import del dominio en un solo
    punto y evita repetir la conversión en `cerrar_jornada`.
    """
    from dominio.operadores import cerrar_turno

    return cerrar_turno(turno)


def reiniciar_sesion() -> None:
    """Descarta el estado de la sesión sin auditar nada.

    Existe únicamente para reiniciar el módulo entre pruebas. El menú nunca
    debe invocarla: saltarse la auditoría es exactamente lo que el sistema
    busca impedir.
    """
    global _operador_actual, _turnos_abiertos
    _operador_actual = None
    _turnos_abiertos = 0


# --------------------------------------------------------------------------- #
# Formato para presentación
# --------------------------------------------------------------------------- #
def describir_sesion() -> str:
    """Devuelve la firma del operador vigente: `Ana Torres (TRN-000001)`.

    Es el texto que el menú muestra en su encabezado.
    """
    return describir_operador(_operador_actual)


def describir_cierre(turno: dict) -> str:
    """Devuelve el detalle completo del turno cerrado, para el cierre de caja.

    Ejemplo:
    `TRN-000001 | Ana Torres | 2026-07-26 08:00:00 → 2026-07-26 10:15:00 | 2h 15m`
    """
    return describir_turno(turno)


def describir_relevo(saliente: dict, entrante: dict) -> str:
    """Resume el cambio de turno en una línea.

    Ejemplo: `Ana Torres (TRN-000001) → Luis Mora (TRN-000002)`
    """
    return (
        f"{obtener_nombre(saliente)} ({obtener_codigo(saliente)}) → "
        f"{obtener_nombre(entrante)} ({obtener_codigo(entrante)})"
    )