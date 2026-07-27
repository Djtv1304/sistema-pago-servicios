"""
Módulo de manejo de dinero

Todas las funciones reciben y devuelven `Decimal` ya redondeado a la cantidad
de decimales configurada. Este módulo no conoce clientes, servicios ni pagos
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from config.constantes import DECIMALES_MONEDA, SIMBOLO_MONEDA
from core.excepciones import DatoInvalidoError

# Unidad mínima de cuantización: Decimal("0.01") con DECIMALES_MONEDA = 2.
_UNIDAD_MINIMA = Decimal(1).scaleb(-DECIMALES_MONEDA)

CERO = Decimal("0").quantize(_UNIDAD_MINIMA)


# --------------------------------------------------------------------------- #
# Conversión
# --------------------------------------------------------------------------- #
def a_decimal(valor, campo: str = "monto") -> Decimal:
    """Convierte un valor a `Decimal` monetario redondeado.

    Acepta `str`, `int` y `Decimal`. Los `float` se convierten vía `str` para
    no arrastrar el error binario de origen.

    Raises:
        DatoInvalidoError: si el valor no representa un número.
    """
    if isinstance(valor, Decimal):
        return redondear(valor)

    if isinstance(valor, float):
        valor = repr(valor)

    try:
        return redondear(Decimal(str(valor).strip()))
    except (InvalidOperation, ValueError, TypeError, ArithmeticError):
        raise DatoInvalidoError(campo, f"'{valor}' no es un valor numérico válido.")


def redondear(monto: Decimal) -> Decimal:
    """Redondea a los decimales de la moneda usando ROUND_HALF_UP.

    Se usa HALF_UP (redondeo comercial) porque es el criterio que aplica la banca al cobrar centavos.
    """
    return monto.quantize(_UNIDAD_MINIMA, rounding=ROUND_HALF_UP)


# --------------------------------------------------------------------------- #
# Operaciones
# --------------------------------------------------------------------------- #
def sumar(*montos: Decimal) -> Decimal:
    """Suma una cantidad variable de montos."""
    total = CERO
    for monto in montos:
        total += monto
    return redondear(total)


def restar(minuendo: Decimal, sustraendo: Decimal) -> Decimal:
    """Resta dos montos y devuelve el resultado redondeado."""
    return redondear(minuendo - sustraendo)


def aplicar_porcentaje(monto: Decimal, porcentaje: Decimal) -> Decimal:
    """Calcula el porcentaje de un monto.

    `aplicar_porcentaje(Decimal("100.00"), Decimal("0.02"))` -> Decimal("2.00")
    """
    return redondear(monto * porcentaje)


# --------------------------------------------------------------------------- #
# Comparaciones (predicados, sin efectos secundarios)
# --------------------------------------------------------------------------- #
def es_mayor_que_cero(monto: Decimal) -> bool:
    """Indica si el monto es estrictamente positivo."""
    return monto > CERO


def es_negativo(monto: Decimal) -> bool:
    """Indica si el monto es menor que cero."""
    return monto < CERO


def esta_en_rango(monto: Decimal, minimo: Decimal, maximo: Decimal) -> bool:
    """Indica si el monto está dentro del rango inclusivo [minimo, maximo]."""
    return minimo <= monto <= maximo


def alcanza_para(saldo_disponible: Decimal, monto_requerido: Decimal) -> bool:
    """Indica si el saldo cubre el monto requerido."""
    return saldo_disponible >= monto_requerido


# --------------------------------------------------------------------------- #
# Presentación de valores (solo formato de cadena, no imprime)
# --------------------------------------------------------------------------- #
def formatear(monto: Decimal) -> str:
    """Devuelve el monto como texto legible: `$ 1,234.56` / `-$ 45.00`."""
    signo = "-" if es_negativo(monto) else ""
    return f"{signo}{SIMBOLO_MONEDA} {abs(monto):,.{DECIMALES_MONEDA}f}"


def formatear_porcentaje(porcentaje: Decimal) -> str:
    """Devuelve una tasa decimal como porcentaje legible: `2%` / `2.5%`."""
    valor = porcentaje * Decimal("100")
    return f"{valor.normalize():f}%"