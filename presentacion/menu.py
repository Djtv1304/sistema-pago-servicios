"""Menú principal del sistema.
"""

from config import constantes
from config.constantes import ETIQUETAS_MENU
from core.excepciones import ErrorSistemaPagos
from aplicacion.consultas import (
    consultar_bitacora,
    consultar_bitacora_del_turno,
    consultar_cierre_de_caja,
    consultar_historial,
    consultar_historial_del_turno,
    consultar_rechazos,
)
from aplicacion.procesar_pago import previsualizar_pago, procesar_pago
from aplicacion.sesion import cambiar_turno, cerrar_jornada, describir_sesion
from presentacion.entrada import (
    confirmar,
    pausar,
    solicitar_datos,
    solicitar_opcion_menu,
    solicitar_operador_entrante,
)
from presentacion.salida import (
    mostrar_aviso,
    mostrar_cierre_de_turno,
    mostrar_detalle_a_confirmar,
    mostrar_error,
    mostrar_menu,
    mostrar_opcion_invalida,
    mostrar_relevo,
    mostrar_reporte,
    mostrar_resultado_pago,
)

CONTINUAR = True
FINALIZAR = False

PREGUNTA_CONFIRMAR_DEBITO = "¿Confirma el débito de esta transacción?"
PREGUNTA_SOLO_MI_TURNO = "¿Ver únicamente los registros de su turno?"
PREGUNTA_CONFIRMAR_RELEVO = "¿Confirma el cambio de operador?"
PREGUNTA_CONFIRMAR_SALIDA = "¿Confirma cerrar el turno y salir del sistema?"

MENSAJE_PAGO_CANCELADO = "Transacción cancelada. No se afectó el saldo del cliente."
MENSAJE_RELEVO_CANCELADO = "Cambio de turno cancelado. Continúa el operador actual."
MENSAJE_SALIDA_CANCELADA = "Salida cancelada. El turno permanece abierto."


# --------------------------------------------------------------------------- #
# Ciclo principal
# --------------------------------------------------------------------------- #
def ejecutar_menu() -> None:
    """Muestra el menú indefinidamente hasta que el operador decida salir.

    Requiere que la jornada ya esté abierta: el encabezado del menú muestra en
    todo momento quién responde por las operaciones que se registren.
    """
    while True:
        mostrar_menu(ETIQUETAS_MENU, describir_sesion())

        if _atender_opcion(solicitar_opcion_menu()) is FINALIZAR:
            return


def _atender_opcion(opcion: str) -> bool:
    """Ejecuta la opción elegida y devuelve si el menú debe continuar.
    """
    try:
        match opcion:
            case constantes.OPCION_REGISTRAR_PAGO:
                _registrar_pago()

            case constantes.OPCION_VER_HISTORIAL:
                _consultar_historial()

            case constantes.OPCION_VER_AUDITORIA:
                _consultar_auditoria()

            case constantes.OPCION_CAMBIAR_TURNO:
                _cambiar_turno()

            case constantes.OPCION_SALIR:
                return _finalizar_jornada()

            case _:
                mostrar_opcion_invalida(tuple(ETIQUETAS_MENU))

    except ErrorSistemaPagos as error:
        mostrar_error(error.mensaje)

    pausar()
    return CONTINUAR


# --------------------------------------------------------------------------- #
# Opción: registrar pago
# --------------------------------------------------------------------------- #
def _registrar_pago() -> None:
    """Captura los datos, confirma el débito y procesa el pago.
    """
    datos = solicitar_datos()

    detalle = previsualizar_pago(datos["servicio"], datos["valor"])
    mostrar_detalle_a_confirmar(detalle, datos["nombre"])

    if not confirmar(PREGUNTA_CONFIRMAR_DEBITO):
        mostrar_aviso(MENSAJE_PAGO_CANCELADO)
        return

    mostrar_resultado_pago(procesar_pago(**datos))


# --------------------------------------------------------------------------- #
# Opción: consultar historial
# --------------------------------------------------------------------------- #
def _consultar_historial() -> None:
    """Muestra los pagos registrados, del turno vigente o de toda la jornada."""
    if confirmar(PREGUNTA_SOLO_MI_TURNO):
        mostrar_reporte(consultar_historial_del_turno())
        return

    mostrar_reporte(consultar_historial())


# --------------------------------------------------------------------------- #
# Opción: consultar auditoría
# --------------------------------------------------------------------------- #
def _consultar_auditoria() -> None:
    """Muestra la bitácora y, si las hubo, las operaciones rechazadas.
    """
    if confirmar(PREGUNTA_SOLO_MI_TURNO):
        mostrar_reporte(consultar_bitacora_del_turno())
    else:
        mostrar_reporte(consultar_bitacora())

    rechazos = consultar_rechazos()
    if not rechazos["vacio"]:
        mostrar_reporte(rechazos)


# --------------------------------------------------------------------------- #
# Opción: cambiar turno
# --------------------------------------------------------------------------- #
def _cambiar_turno() -> None:
    """Releva al operador de caja tras revisar su cierre.
    """
    mostrar_reporte(consultar_cierre_de_caja())

    if not confirmar(PREGUNTA_CONFIRMAR_RELEVO):
        mostrar_aviso(MENSAJE_RELEVO_CANCELADO)
        return

    saliente, entrante = cambiar_turno(solicitar_operador_entrante())
    mostrar_relevo(saliente, entrante)


# --------------------------------------------------------------------------- #
# Opción: salir
# --------------------------------------------------------------------------- #
def _finalizar_jornada() -> bool:
    """Cierra el turno vigente y termina el ciclo del menú.
    """
    mostrar_reporte(consultar_cierre_de_caja())

    if not confirmar(PREGUNTA_CONFIRMAR_SALIDA):
        mostrar_aviso(MENSAJE_SALIDA_CANCELADA)
        pausar()
        return CONTINUAR

    mostrar_cierre_de_turno(cerrar_jornada())
    return FINALIZAR