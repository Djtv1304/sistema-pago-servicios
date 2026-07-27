"""Punto de entrada del Sistema de Pago de Servicios.

Responsabilidad única: arrancar la aplicación en un estado válido y
garantizar que termine de forma ordenada.

Ejecución:
    python main.py
"""

from aplicacion.sesion import cerrar_jornada, hay_turno_abierto, iniciar_jornada
from core.excepciones import ErrorSistemaPagos
from presentacion.entrada import solicitar_nombre_operador
from presentacion.menu import ejecutar_menu
from presentacion.salida import (
    mostrar_aviso,
    mostrar_bienvenida,
    mostrar_cierre_de_turno,
    mostrar_despedida,
    mostrar_error,
    mostrar_turno_iniciado,
)

MENSAJE_INTERRUPCION = "Ejecución interrumpida por el operador."
MENSAJE_CIERRE_FORZADO = "Se cerró automáticamente el turno que estaba abierto."


# --------------------------------------------------------------------------- #
# Arranque
# --------------------------------------------------------------------------- #
def abrir_jornada() -> dict:
    """Solicita el operador responsable y abre el primer turno de la jornada.

    `solicitar_nombre_operador()` reintenta hasta obtener un nombre válido, de
    modo que si esta función retorna, el turno quedó efectivamente abierto.
    """
    operador = iniciar_jornada(solicitar_nombre_operador())
    mostrar_turno_iniciado(operador)
    return operador


def iniciar_aplicacion() -> None:
    """Ejecuta la secuencia completa: bienvenida, apertura de turno y menú."""
    mostrar_bienvenida()
    abrir_jornada()
    ejecutar_menu()


# --------------------------------------------------------------------------- #
# Cierre ante interrupción
# --------------------------------------------------------------------------- #
def cerrar_turno_pendiente() -> None:
    """Cierra el turno que quedó abierto si la ejecución se interrumpió.
    """
    if not hay_turno_abierto():
        return

    try:
        mostrar_cierre_de_turno(cerrar_jornada())
        mostrar_aviso(MENSAJE_CIERRE_FORZADO)
    except ErrorSistemaPagos as error:
        mostrar_error(error.mensaje)


# --------------------------------------------------------------------------- #
# Punto de entrada
# --------------------------------------------------------------------------- #
def main() -> None:
    """Ejecuta la aplicación garantizando la despedida en cualquier escenario.
    """
    try:
        iniciar_aplicacion()
    except KeyboardInterrupt:
        print()
        mostrar_aviso(MENSAJE_INTERRUPCION)
        cerrar_turno_pendiente()
    finally:
        mostrar_despedida()


# Este bloque solo se ejecuta cuando el archivo se corre directamente
# (`python main.py`), no cuando se importa desde otro módulo.
if __name__ == "__main__":
    main()