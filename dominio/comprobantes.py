"""Generación del comprobante de pago.

Contiene la función obligatoria `generar_comprobante()`.

El módulo separa dos responsabilidades que suelen mezclarse:
  - `generar_comprobante()` construye el DATO (un dict con la información
    fiscal del documento).
  - `renderizar_comprobante()` construye el TEXTO imprimible a partir de ese
    dato.

La separación permite que el mismo comprobante se muestre en pantalla hoy y
se exporte a archivo o PDF mañana, sin volver a calcular nada. Coherente con
el resto del sistema, aquí no hay un solo `print()`: se devuelve texto.

El comprobante se representa como un `dict` con las claves:
    numero | fecha | operador | turno | cliente | servicio |
    descripcion_servicio | valor | porcentaje_comision | comision |
    total | saldo_anterior | saldo_nuevo
"""

from datetime import datetime

from config.constantes import (
    ANCHO_COMPROBANTE,
    FORMATO_FECHA_HORA,
    LONGITUD_SECUENCIAL_COMPROBANTE,
    MENSAJE_PIE_COMPROBANTE,
    NOMBRE_APLICACION,
    PREFIJO_COMPROBANTE,
)
from core.dinero import formatear, formatear_porcentaje
from core.validaciones import validar_entero_positivo

CAMPO_SECUENCIAL = "secuencial del comprobante"

ANCHO_ETIQUETA = 16
CARACTER_BORDE = "="
CARACTER_DIVISOR = "-"

TITULO_DOCUMENTO = "COMPROBANTE DE PAGO"


# --------------------------------------------------------------------------- #
# Numeración
# --------------------------------------------------------------------------- #
def formatear_numero_comprobante(secuencial: int) -> str:
    """Construye el número del comprobante con ceros a la izquierda: `CMP-000001`."""
    numero = validar_entero_positivo(CAMPO_SECUENCIAL, secuencial)
    return f"{PREFIJO_COMPROBANTE}-{numero:0{LONGITUD_SECUENCIAL_COMPROBANTE}d}"


# --------------------------------------------------------------------------- #
# Construcción del comprobante
# --------------------------------------------------------------------------- #
def generar_comprobante(pago: dict, secuencial: int) -> dict:
    """Emite el comprobante de un pago ya registrado. [FUNCIÓN REQUERIDA]

    El comprobante se construye A PARTIR del pago, no lo recalcula: los montos
    se copian tal cual quedaron asentados. Un documento que recalcula sus
    propias cifras puede terminar mostrando algo distinto a lo debitado.

    La fecha del pago se conserva como fecha del comprobante, para que ambos
    documentos referencien el mismo instante.

    Args:
        pago: registro de pago construido por `dominio.pagos.construir_pago`.
        secuencial: número correlativo provisto por la capa de aplicación.
    """
    return {
        "numero": formatear_numero_comprobante(secuencial),
        "fecha": pago["fecha"],
        "operador": pago["operador"],
        "turno": pago["turno"],
        "cliente": pago["cliente"],
        "servicio": pago["servicio"],
        "descripcion_servicio": pago["descripcion_servicio"],
        "valor": pago["valor"],
        "porcentaje_comision": pago["porcentaje_comision"],
        "comision": pago["comision"],
        "total": pago["total"],
        "saldo_anterior": pago["saldo_anterior"],
        "saldo_nuevo": pago["saldo_nuevo"],
    }


# --------------------------------------------------------------------------- #
# Consultas (sin efectos secundarios)
# --------------------------------------------------------------------------- #
def obtener_numero(comprobante: dict) -> str:
    """Devuelve el número del comprobante."""
    return comprobante["numero"]


def obtener_fecha(comprobante: dict) -> datetime:
    """Devuelve la fecha y hora de emisión."""
    return comprobante["fecha"]


# --------------------------------------------------------------------------- #
# Armado de líneas (helpers reutilizables del formato)
# --------------------------------------------------------------------------- #
def _linea_borde() -> str:
    """Línea sólida que abre y cierra el documento."""
    return CARACTER_BORDE * ANCHO_COMPROBANTE


def _linea_divisor() -> str:
    """Línea punteada que separa bloques internos."""
    return CARACTER_DIVISOR * ANCHO_COMPROBANTE


def _linea_centrada(texto: str) -> str:
    """Centra un texto dentro del ancho del comprobante."""
    return texto.center(ANCHO_COMPROBANTE)


def _linea_campo(etiqueta: str, valor: str) -> str:
    """Arma una línea de dato alineada a la izquierda: ` Cliente  : Juan Pérez`."""
    return f" {etiqueta:<{ANCHO_ETIQUETA}}: {valor}"


def _linea_importe(etiqueta: str, monto) -> str:
    """Arma una línea de dinero con el importe alineado al margen derecho.

    Alinear los importes a la derecha es lo que permite comparar cifras de un
    vistazo: las unidades quedan una debajo de la otra.
    """
    prefijo = f" {etiqueta:<{ANCHO_ETIQUETA}}: "
    importe = formatear(monto)
    return prefijo + importe.rjust(ANCHO_COMPROBANTE - len(prefijo))


def _bloque_encabezado(comprobante: dict) -> list[str]:
    """Identificación del documento y del responsable de la emisión."""
    return [
        _linea_borde(),
        _linea_centrada(NOMBRE_APLICACION),
        _linea_centrada(TITULO_DOCUMENTO),
        _linea_borde(),
        _linea_campo("No. Comprobante", obtener_numero(comprobante)),
        _linea_campo("Fecha", obtener_fecha(comprobante).strftime(FORMATO_FECHA_HORA)),
        _linea_campo("Atendido por", comprobante["operador"]),
        _linea_campo("Turno", comprobante["turno"]),
    ]


def _bloque_transaccion(comprobante: dict) -> list[str]:
    """Datos del cliente y del servicio pagado."""
    servicio = f"{comprobante['servicio']} - {comprobante['descripcion_servicio']}"
    return [
        _linea_divisor(),
        _linea_campo("Cliente", comprobante["cliente"]),
        _linea_campo("Servicio", servicio),
    ]


def _bloque_importes(comprobante: dict) -> list[str]:
    """Desglose económico: valor, comisión y total debitado."""
    etiqueta_comision = (
        f"Comisión ({formatear_porcentaje(comprobante['porcentaje_comision'])})"
    )
    return [
        _linea_divisor(),
        _linea_importe("Valor servicio", comprobante["valor"]),
        _linea_importe(etiqueta_comision, comprobante["comision"]),
        _linea_divisor(),
        _linea_importe("TOTAL DEBITADO", comprobante["total"]),
    ]


def _bloque_saldos(comprobante: dict) -> list[str]:
    """Saldo antes y después del débito, para verificación del cliente."""
    return [
        _linea_divisor(),
        _linea_importe("Saldo anterior", comprobante["saldo_anterior"]),
        _linea_importe("Saldo actual", comprobante["saldo_nuevo"]),
    ]


def _bloque_pie() -> list[str]:
    """Cierre del documento."""
    return [
        _linea_borde(),
        _linea_centrada(MENSAJE_PIE_COMPROBANTE),
        _linea_borde(),
    ]


# --------------------------------------------------------------------------- #
# Formato para presentación (devuelve texto, no imprime)
# --------------------------------------------------------------------------- #
def renderizar_comprobante(comprobante: dict) -> str:
    """Devuelve el comprobante completo como texto listo para mostrar."""
    lineas = [
        *_bloque_encabezado(comprobante),
        *_bloque_transaccion(comprobante),
        *_bloque_importes(comprobante),
        *_bloque_saldos(comprobante),
        *_bloque_pie(),
    ]
    return "\n".join(lineas)


def describir_comprobante(comprobante: dict) -> str:
    """Resume el comprobante en una línea, para listados y auditoría.

    Ejemplo: `CMP-000001 | Juan Pérez | LUZ | $ 38.20`
    """
    return (
        f"{obtener_numero(comprobante)} | {comprobante['cliente']} | "
        f"{comprobante['servicio']} | {formatear(comprobante['total'])}"
    )