"""Bitácora de auditoría del sistema.

Contiene la función obligatoria `registrar_auditoria()`.

Este módulo es INFRAESTRUCTURA, no dominio: su responsabilidad es almacenar,
no decidir. Por eso es el único de los vistos hasta ahora que mantiene estado
(la bitácora en memoria) y el único que no exige inmutabilidad: un registro
de auditoría se agrega, jamás se modifica ni se elimina.

Regla innegociable: NINGÚN evento puede registrarse sin operador responsable.
Es la razón de ser de la bitácora.

Cada registro es un `dict` con las claves:
    id | fecha | evento | operador | turno | resultado | codigo_error | detalle
"""

from config.constantes import (
    EVENTO_CONSULTA_HISTORIAL,
    EVENTO_PAGO_APROBADO,
    EVENTO_PAGO_RECHAZADO,
    EVENTO_TURNO_CERRADO,
    EVENTO_TURNO_INICIADO,
    EVENTOS_AUDITABLES,
    FORMATO_FECHA_HORA,
    LONGITUD_SECUENCIAL_AUDITORIA,
    PREFIJO_AUDITORIA,
    RESULTADO_EXITOSO,
    RESULTADO_RECHAZADO,
)
from core.dinero import formatear
from core.excepciones import DatoInvalidoError, ErrorSistemaPagos
from core.validaciones import validar_opcion, validar_texto_requerido
from dominio.comprobantes import obtener_numero
from dominio.operadores import obtener_codigo, obtener_nombre
from dominio.pagos import describir_pago
from datetime import datetime

CAMPO_EVENTO = "evento de auditoría"
CAMPO_OPERADOR = "operador responsable"
CAMPO_DETALLE = "detalle del evento"

# Estado interno del módulo. El guion bajo indica que nadie debe tocarlo
# directamente: todo acceso pasa por las funciones públicas de abajo.
_bitacora: list[dict] = []


# --------------------------------------------------------------------------- #
# Numeración interna
# --------------------------------------------------------------------------- #
def _siguiente_identificador() -> str:
    """Genera el identificador correlativo del registro: `AUD-000001`."""
    numero = len(_bitacora) + 1
    return f"{PREFIJO_AUDITORIA}-{numero:0{LONGITUD_SECUENCIAL_AUDITORIA}d}"


# --------------------------------------------------------------------------- #
# Validación
# --------------------------------------------------------------------------- #
def validar_evento(evento: str) -> str:
    """Verifica que el evento pertenezca al catálogo de eventos auditables.

    Un catálogo cerrado impide que la bitácora se llene de etiquetas escritas
    a mano ('PAGO_OK', 'pago_aprobado', 'PagoAprobado') que después harían
    imposible filtrar o totalizar.
    """
    return validar_opcion(CAMPO_EVENTO, evento, EVENTOS_AUDITABLES)


def validar_responsable(operador: dict | None) -> dict:
    """Exige un operador responsable identificado.

    Raises:
        DatoInvalidoError: si no se recibió operador.
    """
    if not operador or not operador.get("nombre"):
        raise DatoInvalidoError(
            CAMPO_OPERADOR, "es obligatorio: ningún evento puede quedar sin responsable."
        )
    return operador


# --------------------------------------------------------------------------- #
# Registro (FUNCIÓN REQUERIDA)
# --------------------------------------------------------------------------- #
def registrar_auditoria(
        evento: str,
        operador: dict,
        detalle: str,
        codigo_error: str | None = None,
) -> dict:
    """Asienta un evento en la bitácora y devuelve el registro creado.
    [FUNCIÓN REQUERIDA]

    El resultado se deduce del `codigo_error`: si viene informado, el evento
    se marca como RECHAZADO. Así el llamador no puede registrar un pago
    fallido como exitoso por descuido.

    Args:
        evento: uno de los valores de `EVENTOS_AUDITABLES`.
        operador: turno de caja responsable. Obligatorio.
        detalle: descripción legible de lo ocurrido.
        codigo_error: código de la excepción, solo en eventos rechazados.

    Raises:
        DatoInvalidoError: si falta el operador, el detalle o el evento no
            pertenece al catálogo.
    """
    responsable = validar_responsable(operador)

    registro = {
        "id": _siguiente_identificador(),
        "fecha": datetime.now(),
        "evento": validar_evento(evento),
        "operador": obtener_nombre(responsable),
        "turno": obtener_codigo(responsable),
        "resultado": RESULTADO_RECHAZADO if codigo_error else RESULTADO_EXITOSO,
        "codigo_error": codigo_error,
        "detalle": validar_texto_requerido(CAMPO_DETALLE, detalle),
    }

    _bitacora.append(registro)
    return registro


# --------------------------------------------------------------------------- #
# Registradores especializados
# Encapsulan QUÉ se escribe en cada tipo de evento, para que la capa de
# aplicación no tenga que redactar el detalle a mano cada vez.
# --------------------------------------------------------------------------- #
def auditar_turno_iniciado(operador: dict) -> dict:
    """Deja constancia de la apertura de un turno de caja."""
    return registrar_auditoria(
        EVENTO_TURNO_INICIADO, operador, f"Turno abierto por {obtener_nombre(operador)}."
    )


def auditar_turno_cerrado(operador: dict, duracion: str, pagos_del_turno: int) -> dict:
    """Deja constancia del cierre de caja con su resumen de actividad."""
    return registrar_auditoria(
        EVENTO_TURNO_CERRADO,
        operador,
        f"Turno cerrado. Duración: {duracion}. Pagos registrados: {pagos_del_turno}.",
    )


def auditar_pago_aprobado(operador: dict, pago: dict, comprobante: dict) -> dict:
    """Deja constancia de un pago procesado con éxito.

    El detalle enlaza el número de comprobante con el pago: es lo que permite
    reconstruir la transacción completa desde la bitácora.
    """
    return registrar_auditoria(
        EVENTO_PAGO_APROBADO,
        operador,
        f"{obtener_numero(comprobante)} | {describir_pago(pago)}",
    )


def auditar_pago_rechazado(operador: dict, cliente: str, error: ErrorSistemaPagos) -> dict:
    """Deja constancia de un intento de pago rechazado.

    Auditar los rechazos es tan importante como auditar los éxitos: un intento
    de cobro sobre un cliente bloqueado es exactamente el hecho que un auditor
    necesita poder rastrear.
    """
    return registrar_auditoria(
        EVENTO_PAGO_RECHAZADO,
        operador,
        f"Intento rechazado para '{cliente}'. Motivo: {error.mensaje}",
        codigo_error=error.codigo,
    )


def auditar_consulta_historial(operador: dict, cantidad: int, total) -> dict:
    """Deja constancia de una consulta al historial de pagos."""
    return registrar_auditoria(
        EVENTO_CONSULTA_HISTORIAL,
        operador,
        f"Historial consultado: {cantidad} pago(s), total {formatear(total)}.",
    )


# --------------------------------------------------------------------------- #
# Consultas
# --------------------------------------------------------------------------- #
def listar_eventos() -> list[dict]:
    """Devuelve todos los registros en orden cronológico."""
    return list(_bitacora)


def filtrar_eventos(criterio) -> list[dict]:
    """Devuelve los registros que cumplen el criterio recibido.

    El criterio es una función que recibe un registro y devuelve `True` o
    `False`. Una sola función cubre todos los filtros posibles:

        filtrar_eventos(lambda r: r["turno"] == "TRN-000001")
        filtrar_eventos(lambda r: r["resultado"] == RESULTADO_RECHAZADO)
    """
    return [registro for registro in _bitacora if criterio(registro)]


def filtrar_por_turno(codigo_turno: str) -> list[dict]:
    """Devuelve los registros generados durante un turno específico."""
    return filtrar_eventos(lambda registro: registro["turno"] == codigo_turno)


def filtrar_por_evento(evento: str) -> list[dict]:
    """Devuelve los registros de un tipo de evento específico."""
    tipo = validar_evento(evento)
    return filtrar_eventos(lambda registro: registro["evento"] == tipo)


def listar_rechazos() -> list[dict]:
    """Devuelve únicamente los eventos marcados como rechazados."""
    return filtrar_eventos(
        lambda registro: registro["resultado"] == RESULTADO_RECHAZADO
    )


def contar_eventos() -> int:
    """Devuelve la cantidad total de registros en la bitácora."""
    return len(_bitacora)


def hay_eventos() -> bool:
    """Indica si la bitácora contiene al menos un registro."""
    return contar_eventos() > 0


def limpiar_bitacora() -> None:
    """Vacía la bitácora.

    Existe únicamente para reiniciar el estado entre pruebas. El menú no debe
    ofrecer esta operación: una bitácora que se puede borrar desde la
    aplicación no sirve como auditoría.
    """
    _bitacora.clear()


# --------------------------------------------------------------------------- #
# Formato para presentación (devuelve texto, no imprime)
# --------------------------------------------------------------------------- #
def describir_evento(registro: dict) -> str:
    """Resume un registro en una línea.

    Ejemplo aprobado:
    `AUD-000002 | 2026-07-26 10:15:00 | PAGO_APROBADO | Ana Torres (TRN-000001) | CMP-000001 | ...`

    Ejemplo rechazado:
    `AUD-000003 | 2026-07-26 10:18:00 | PAGO_RECHAZADO [ERR_CLIENTE_BLOQUEADO] | ...`
    """
    marca_error = f" [{registro['codigo_error']}]" if registro["codigo_error"] else ""
    return (
        f"{registro['id']} | {registro['fecha'].strftime(FORMATO_FECHA_HORA)} | "
        f"{registro['evento']}{marca_error} | "
        f"{registro['operador']} ({registro['turno']}) | {registro['detalle']}"
    )