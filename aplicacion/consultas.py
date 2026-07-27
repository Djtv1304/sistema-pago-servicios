"""Consultas de historial de pagos y bitácora de auditoría.

Este módulo arma REPORTES: recupera los registros de la infraestructura, los
totaliza y devuelve la información ya formateada en líneas de texto.

Cada reporte es un `dict` con las claves:
    titulo | lineas | resumen | cantidad | vacio

"""

from decimal import Decimal

from config.constantes import RESULTADO_RECHAZADO
from dominio.operadores import obtener_codigo, obtener_nombre
from infraestructura import auditoria
from infraestructura import repositorio_pagos as repositorio
from aplicacion.sesion import exigir_turno_activo

TITULO_HISTORIAL_GENERAL = "HISTORIAL DE PAGOS DE LA JORNADA"
TITULO_HISTORIAL_TURNO = "HISTORIAL DE PAGOS DEL TURNO"
TITULO_BITACORA_GENERAL = "BITÁCORA DE AUDITORÍA"
TITULO_BITACORA_TURNO = "BITÁCORA DE AUDITORÍA DEL TURNO"
TITULO_RECHAZOS = "OPERACIONES RECHAZADAS"
TITULO_CIERRE_CAJA = "CIERRE DE CAJA DEL TURNO"

MENSAJE_SIN_PAGOS = "No se han registrado pagos."
MENSAJE_SIN_EVENTOS = "No hay eventos registrados."
MENSAJE_SIN_RECHAZOS = "No se registraron operaciones rechazadas."


# --------------------------------------------------------------------------- #
# Constructor genérico de reportes
# --------------------------------------------------------------------------- #
def _construir_reporte(
        titulo: str,
        registros: list,
        formateador,
        resumen: str = "",
        mensaje_vacio: str = "",
) -> dict:
    """Arma un reporte a partir de una colección de registros.

    Args:
        titulo: encabezado del reporte.
        registros: colección a listar.
        formateador: función que convierte un registro en una línea de texto.
        resumen: totalización final. Se omite si el reporte está vacío.
        mensaje_vacio: texto a mostrar cuando no hay registros.
    """
    esta_vacio = not registros

    return {
        "titulo": titulo,
        "lineas": [mensaje_vacio] if esta_vacio else [formateador(r) for r in registros],
        "resumen": "" if esta_vacio else resumen,
        "cantidad": len(registros),
        "vacio": esta_vacio,
    }


# --------------------------------------------------------------------------- #
# Consultas de pagos
# --------------------------------------------------------------------------- #
def consultar_historial() -> dict:
    """Devuelve el historial completo de pagos de la jornada.

    Exige turno abierto y deja constancia de la consulta en la bitácora: el
    acceso a información financiera es en sí mismo un hecho auditable.

    Raises:
        TurnoNoIniciadoError: si no hay turno de caja abierto.
    """
    operador = exigir_turno_activo()
    pagos = repositorio.listar_pagos()
    resumen = repositorio.resumir_caja(pagos)

    auditoria.auditar_consulta_historial(
        operador, resumen["cantidad"], resumen["recaudado"]
    )

    return _construir_reporte(
        titulo=TITULO_HISTORIAL_GENERAL,
        registros=pagos,
        formateador=repositorio.describir_pago_registrado,
        resumen=repositorio.describir_resumen(resumen),
        mensaje_vacio=MENSAJE_SIN_PAGOS,
    )


def consultar_historial_del_turno() -> dict:
    """Devuelve únicamente los pagos registrados en el turno vigente.

    Raises:
        TurnoNoIniciadoError: si no hay turno de caja abierto.
    """
    operador = exigir_turno_activo()
    codigo = obtener_codigo(operador)
    pagos = repositorio.filtrar_por_turno(codigo)
    resumen = repositorio.resumir_caja(pagos)

    auditoria.auditar_consulta_historial(
        operador, resumen["cantidad"], resumen["recaudado"]
    )

    return _construir_reporte(
        titulo=f"{TITULO_HISTORIAL_TURNO} {codigo}",
        registros=pagos,
        formateador=repositorio.describir_pago_registrado,
        resumen=repositorio.describir_resumen(resumen),
        mensaje_vacio=MENSAJE_SIN_PAGOS,
    )


# --------------------------------------------------------------------------- #
# Consultas de auditoría
# --------------------------------------------------------------------------- #
def consultar_bitacora() -> dict:
    """Devuelve todos los eventos registrados durante la ejecución.

    Raises:
        TurnoNoIniciadoError: si no hay turno de caja abierto.
    """
    exigir_turno_activo()
    eventos = auditoria.listar_eventos()

    return _construir_reporte(
        titulo=TITULO_BITACORA_GENERAL,
        registros=eventos,
        formateador=auditoria.describir_evento,
        resumen=_resumir_bitacora(eventos),
        mensaje_vacio=MENSAJE_SIN_EVENTOS,
    )


def consultar_bitacora_del_turno() -> dict:
    """Devuelve los eventos generados durante el turno vigente.

    Raises:
        TurnoNoIniciadoError: si no hay turno de caja abierto.
    """
    operador = exigir_turno_activo()
    codigo = obtener_codigo(operador)
    eventos = auditoria.filtrar_por_turno(codigo)

    return _construir_reporte(
        titulo=f"{TITULO_BITACORA_TURNO} {codigo}",
        registros=eventos,
        formateador=auditoria.describir_evento,
        resumen=_resumir_bitacora(eventos),
        mensaje_vacio=MENSAJE_SIN_EVENTOS,
    )


def consultar_rechazos() -> dict:
    """Devuelve las operaciones que fueron rechazadas por alguna regla.

    Es la consulta de mayor valor para un auditor: muestra qué se intentó
    hacer y por qué el sistema lo impidió.

    Raises:
        TurnoNoIniciadoError: si no hay turno de caja abierto.
    """
    exigir_turno_activo()
    rechazos = auditoria.listar_rechazos()

    return _construir_reporte(
        titulo=TITULO_RECHAZOS,
        registros=rechazos,
        formateador=auditoria.describir_evento,
        resumen=_resumir_rechazos(rechazos),
        mensaje_vacio=MENSAJE_SIN_RECHAZOS,
    )


# --------------------------------------------------------------------------- #
# Cierre de caja
# --------------------------------------------------------------------------- #
def consultar_cierre_de_caja() -> dict:
    """Devuelve el resumen de actividad del turno vigente.

    Es el reporte que el operador revisa antes de entregar la caja: cuántos
    pagos procesó, cuánto recaudó y cuánto corresponde a comisiones.

    Raises:
        TurnoNoIniciadoError: si no hay turno de caja abierto.
    """
    operador = exigir_turno_activo()
    codigo = obtener_codigo(operador)
    pagos = repositorio.filtrar_por_turno(codigo)
    resumen = repositorio.resumir_caja(pagos)

    return {
        "titulo": f"{TITULO_CIERRE_CAJA} {codigo}",
        "lineas": _detallar_cierre(operador, resumen),
        "resumen": repositorio.describir_resumen(resumen),
        "cantidad": resumen["cantidad"],
        "vacio": resumen["cantidad"] == 0,
    }


def _detallar_cierre(operador: dict, resumen: dict) -> list[str]:
    """Arma las líneas del cierre de caja, incluyendo el desglose por servicio."""
    lineas = [
        f"Operador        : {obtener_nombre(operador)}",
        f"Turno           : {obtener_codigo(operador)}",
        f"Pagos           : {resumen['cantidad']}",
        f"Recaudado       : {_texto_monto(resumen['recaudado'])}",
        f"Comisiones      : {_texto_monto(resumen['comisiones'])}",
    ]
    lineas.extend(_detallar_servicios(resumen["por_servicio"]))
    return lineas


def _detallar_servicios(conteo_por_servicio: dict) -> list[str]:
    """Arma el desglose de pagos por servicio, ordenado de mayor a menor."""
    if not conteo_por_servicio:
        return []

    ordenados = sorted(
        conteo_por_servicio.items(), key=lambda par: (-par[1], par[0])
    )
    return ["Por servicio    :"] + [
        f"  - {servicio:<10}: {cantidad} pago(s)" for servicio, cantidad in ordenados
    ]


# --------------------------------------------------------------------------- #
# Totalizadores de auditoría
# --------------------------------------------------------------------------- #
def _contar_rechazos(eventos: list[dict]) -> int:
    """Cuenta cuántos eventos de la colección quedaron marcados como rechazados."""
    return sum(1 for evento in eventos if evento["resultado"] == RESULTADO_RECHAZADO)


def _agrupar_por_codigo_error(rechazos: list[dict]) -> dict:
    """Cuenta los rechazos agrupados por código de error."""
    conteo = {}
    for rechazo in rechazos:
        codigo = rechazo["codigo_error"]
        conteo[codigo] = conteo.get(codigo, 0) + 1
    return conteo


def _resumir_bitacora(eventos: list[dict]) -> str:
    """Resume la bitácora: `12 evento(s) | 9 exitoso(s) | 3 rechazado(s)`."""
    total = len(eventos)
    rechazados = _contar_rechazos(eventos)
    return (
        f"{total} evento(s) | {total - rechazados} exitoso(s) | "
        f"{rechazados} rechazado(s)"
    )


def _resumir_rechazos(rechazos: list[dict]) -> str:
    """Resume los rechazos por motivo: `3 rechazo(s) | ERR_SALDO_INSUFICIENTE: 2, ...`."""
    if not rechazos:
        return ""

    conteo = _agrupar_por_codigo_error(rechazos)
    ordenados = sorted(conteo.items(), key=lambda par: (-par[1], par[0]))
    detalle = ", ".join(f"{codigo}: {cantidad}" for codigo, cantidad in ordenados)
    return f"{len(rechazos)} rechazo(s) | {detalle}"


def _texto_monto(monto: Decimal) -> str:
    """Formatea un monto para los reportes de esta capa."""
    from core.dinero import formatear

    return formatear(monto)