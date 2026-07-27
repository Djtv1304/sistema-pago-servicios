"""Validadores genéricos y reutilizables de entrada de datos.

Estas funciones NO conocen reglas de negocio: no saben qué es un cliente ni
qué servicios existen. Solo verifican formato, tipo y rango, y reciben sus
límites por parámetro para poder reutilizarse en cualquier campo.

Convención del módulo (patrón "validar y normalizar"): cada función devuelve
el valor ya limpio en lugar de un booleano. Así el llamador nunca puede
olvidarse de usar la versión normalizada, y `' juan '` no llega jamás a la
capa de dominio.

Todas lanzan `DatoInvalidoError` ante un valor inválido.
"""

import unicodedata
from decimal import Decimal

from core.dinero import a_decimal, es_mayor_que_cero, es_negativo, esta_en_rango, formatear
from core.excepciones import DatoInvalidoError

_CARACTERES_EXTRA_NOMBRE = frozenset(" '-.")


# --------------------------------------------------------------------------- #
# Normalización
# --------------------------------------------------------------------------- #
def quitar_tildes(texto: str) -> str:
    """Elimina los acentos de un texto: `TELEFONÍA` -> `TELEFONIA`."""
    descompuesto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


def normalizar_texto(valor: str) -> str:
    """Limpia espacios sobrantes al inicio, al final y entre palabras."""
    return " ".join(str(valor).split())


def normalizar_codigo(valor: str) -> str:
    """Normaliza un valor de catálogo: sin espacios, sin tildes y en mayúsculas.

    Permite que `' telefonía '`, `'Telefonia'` y `'TELEFONÍA'` sean el mismo
    código antes de compararlo contra el catálogo.
    """
    return quitar_tildes(normalizar_texto(valor)).upper()


# --------------------------------------------------------------------------- #
# Validación de texto
# --------------------------------------------------------------------------- #
def validar_texto_requerido(campo: str, valor: str) -> str:
    """Verifica que el campo no venga vacío ni compuesto solo por espacios."""
    texto = normalizar_texto(valor)
    if not texto:
        raise DatoInvalidoError(campo, "es obligatorio y no puede estar vacío.")
    return texto


def validar_longitud_texto(campo: str, valor: str, minima: int, maxima: int) -> str:
    """Verifica que la longitud del texto esté dentro del rango permitido."""
    texto = validar_texto_requerido(campo, valor)
    if not minima <= len(texto) <= maxima:
        raise DatoInvalidoError(
            campo, f"debe tener entre {minima} y {maxima} caracteres (tiene {len(texto)})."
        )
    return texto


def validar_texto_alfabetico(campo: str, valor: str) -> str:
    """Verifica que el texto contenga solo letras, espacios, guiones o apóstrofes.

    Evita que un nombre de cliente llegue como `'12345'` o `'Juan@@'`.
    """
    texto = validar_texto_requerido(campo, valor)
    caracteres_invalidos = {
        c for c in texto if not c.isalpha() and c not in _CARACTERES_EXTRA_NOMBRE
    }
    if caracteres_invalidos:
        invalidos = " ".join(sorted(caracteres_invalidos))
        raise DatoInvalidoError(campo, f"contiene caracteres no permitidos: {invalidos}")
    return texto


def validar_nombre_persona(campo: str, valor: str, minima: int, maxima: int) -> str:
    """Valida un nombre completo y lo devuelve capitalizado (`juan pérez` -> `Juan Pérez`)."""
    texto = validar_longitud_texto(campo, valor, minima, maxima)
    validar_texto_alfabetico(campo, texto)
    return texto.title()


# --------------------------------------------------------------------------- #
# Validación contra catálogos
# --------------------------------------------------------------------------- #
def validar_opcion(campo: str, valor: str, opciones_validas) -> str:
    """Verifica que el valor pertenezca a un catálogo cerrado de opciones.

    La comparación es insensible a mayúsculas, tildes y espacios. Devuelve
    la opción tal como está escrita en el catálogo, no como la digitó el usuario.
    """
    codigo = normalizar_codigo(valor)
    if not codigo:
        raise DatoInvalidoError(campo, "es obligatorio y no puede estar vacío.")

    equivalencias = {normalizar_codigo(opcion): opcion for opcion in opciones_validas}
    if codigo not in equivalencias:
        disponibles = ", ".join(str(opcion) for opcion in opciones_validas)
        raise DatoInvalidoError(
            campo, f"'{normalizar_texto(valor)}' no es válido. Opciones: {disponibles}"
        )
    return equivalencias[codigo]


# --------------------------------------------------------------------------- #
# Validación numérica y monetaria
# --------------------------------------------------------------------------- #
def validar_monto_decimal(campo: str, valor) -> Decimal:
    """Convierte la entrada a `Decimal` monetario validando el formato."""
    return a_decimal(valor, campo)


def validar_monto_no_negativo(campo: str, valor) -> Decimal:
    """Valida un monto que puede ser cero pero nunca negativo (ej. un saldo)."""
    monto = validar_monto_decimal(campo, valor)
    if es_negativo(monto):
        raise DatoInvalidoError(campo, f"no puede ser negativo (recibido: {formatear(monto)}).")
    return monto


def validar_monto_positivo(campo: str, valor) -> Decimal:
    """Valida un monto estrictamente mayor que cero (ej. el valor de un pago)."""
    monto = validar_monto_decimal(campo, valor)
    if not es_mayor_que_cero(monto):
        raise DatoInvalidoError(campo, f"debe ser mayor que cero (recibido: {formatear(monto)}).")
    return monto


def validar_monto_en_rango(campo: str, valor, minimo: Decimal, maximo: Decimal) -> Decimal:
    """Valida que un monto positivo esté dentro de los límites permitidos."""
    monto = validar_monto_positivo(campo, valor)
    if not esta_en_rango(monto, minimo, maximo):
        raise DatoInvalidoError(
            campo,
            f"debe estar entre {formatear(minimo)} y {formatear(maximo)} "
            f"(recibido: {formatear(monto)}).",
        )
    return monto

# --------------------------------------------------------------------------- #
# Validación de enteros
# --------------------------------------------------------------------------- #
def validar_entero_positivo(campo: str, valor) -> int:
    """Valida que el valor sea un entero mayor o igual a 1.

    Se rechaza `bool` explícitamente porque en Python `True == 1`, y un
    booleano como secuencial sería un error silencioso.
    """
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise DatoInvalidoError(campo, "debe ser un número entero.")
    if valor < 1:
        raise DatoInvalidoError(campo, "debe ser mayor o igual a 1.")
    return valor