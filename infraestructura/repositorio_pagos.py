"""Persistencia de los pagos registrados.

Contiene la función obligatoria `registrar_pago()`.

Al igual que `auditoria.py`, este módulo es INFRAESTRUCTURA: almacena y
consulta, pero no decide nada de negocio. Cuando un pago llega aquí ya fue
validado, calculado y debitado; el repositorio solo lo asienta.

Responsabilidad exclusiva de esta capa: ASIGNAR EL IDENTIFICADOR. El dominio
construye el pago sin número, igual que un objeto recién creado no tiene aún
clave primaria; es la persistencia la que se lo otorga al guardarlo. Ese
secuencial es el que luego numera el comprobante.

El almacenamiento es una lista en memoria: al cerrar el programa, los datos se
pierden. Si mañana se migra a archivo o base de datos, solo cambia este
archivo — su interfaz pública se mantiene.
"""

from decimal import Decimal

from core.dinero import formatear
from core.excepciones import DatoInvalidoError
from dominio.pagos import (
    contar_por_servicio,
    describir_pago,
    es_del_servicio,
    es_del_turno,
    obtener_comision,
    obtener_total,
    totalizar,
)

CAMPO_PAGO = "registro de pago"

# Campos que todo pago debe traer para poder asentarse. Es un control de
# integridad estructural, no una regla de negocio: protege al repositorio de
# almacenar registros incompletos que romperían las consultas después.
CAMPOS_REQUERIDOS = frozenset(
    {
        "fecha",
        "operador",
        "turno",
        "cliente",
        "servicio",
        "valor",
        "comision",
        "total",
        "saldo_anterior",
        "saldo_nuevo",
    }
)

# Estado interno del módulo. Todo acceso pasa por las funciones públicas.
_pagos: list[dict] = []


# --------------------------------------------------------------------------- #
# Numeración
# --------------------------------------------------------------------------- #
def _siguiente_secuencial() -> int:
    """Devuelve el próximo número correlativo de pago.

    La numeración es continua durante toda la ejecución y no se reinicia al
    cambiar de turno: dos pagos jamás comparten número.
    """
    return len(_pagos) + 1


# --------------------------------------------------------------------------- #
# Validación de integridad
# --------------------------------------------------------------------------- #
def validar_pago(pago: dict) -> dict:
    """Verifica que el registro traiga todos los campos obligatorios.

    Raises:
        DatoInvalidoError: si el pago está vacío o le faltan campos.
    """
    if not isinstance(pago, dict) or not pago:
        raise DatoInvalidoError(CAMPO_PAGO, "no puede estar vacío.")

    faltantes = CAMPOS_REQUERIDOS - set(pago)
    if faltantes:
        campos = ", ".join(sorted(faltantes))
        raise DatoInvalidoError(CAMPO_PAGO, f"faltan campos obligatorios: {campos}")
    return pago


# --------------------------------------------------------------------------- #
# Registro (FUNCIÓN REQUERIDA)
# --------------------------------------------------------------------------- #
def registrar_pago(pago: dict) -> dict:
    """Asienta un pago en el repositorio y devuelve el registro almacenado.
    [FUNCIÓN REQUERIDA]

    Guarda una COPIA con su secuencial asignado, no la referencia recibida:
    así, si el llamador altera su diccionario después, el histórico queda
    intacto. Un registro almacenado no vuelve a cambiar nunca.

    El registro devuelto incluye la clave `secuencial`, que es la que debe
    usarse para numerar el comprobante.

    Raises:
        DatoInvalidoError: si el pago no cumple la integridad estructural.
    """
    validar_pago(pago)

    registrado = dict(pago)
    registrado["secuencial"] = _siguiente_secuencial()

    _pagos.append(registrado)
    return registrado


def obtener_secuencial(pago: dict) -> int:
    """Devuelve el número asignado al pago al ser almacenado."""
    return pago["secuencial"]


# --------------------------------------------------------------------------- #
# Consultas (devuelven copias: el histórico no se expone para modificación)
# --------------------------------------------------------------------------- #
def listar_pagos() -> list[dict]:
    """Devuelve todos los pagos en orden cronológico de registro."""
    return list(_pagos)


def filtrar_pagos(criterio) -> list[dict]:
    """Devuelve los pagos que cumplen el criterio recibido.

    El criterio es una función que recibe un pago y responde `True` o `False`.
    Una sola implementación cubre cualquier filtro:

        filtrar_pagos(lambda p: p["cliente"] == "Juan Pérez")
        filtrar_pagos(lambda p: p["total"] > Decimal("100.00"))
    """
    return [pago for pago in _pagos if criterio(pago)]


def filtrar_por_turno(codigo_turno: str) -> list[dict]:
    """Devuelve los pagos registrados durante un turno específico."""
    return filtrar_pagos(lambda pago: es_del_turno(pago, codigo_turno))


def filtrar_por_servicio(servicio: str) -> list[dict]:
    """Devuelve los pagos de un servicio específico."""
    return filtrar_pagos(lambda pago: es_del_servicio(pago, servicio))


def filtrar_por_cliente(nombre_cliente: str) -> list[dict]:
    """Devuelve los pagos asociados a un cliente."""
    return filtrar_pagos(lambda pago: pago["cliente"] == nombre_cliente)


def obtener_ultimo_pago() -> dict | None:
    """Devuelve el pago más reciente, o `None` si no hay ninguno."""
    return _pagos[-1] if _pagos else None


def contar_pagos() -> int:
    """Devuelve la cantidad total de pagos registrados."""
    return len(_pagos)


def contar_por_turno(codigo_turno: str) -> int:
    """Devuelve cuántos pagos se registraron en un turno."""
    return len(filtrar_por_turno(codigo_turno))


def hay_pagos() -> bool:
    """Indica si existe al menos un pago registrado."""
    return contar_pagos() > 0


# --------------------------------------------------------------------------- #
# Totalizadores para el cierre de caja
# --------------------------------------------------------------------------- #
def calcular_total_recaudado(pagos=None) -> Decimal:
    """Suma el total debitado. Sin argumento, calcula sobre todo el histórico."""
    return totalizar(listar_pagos() if pagos is None else pagos, obtener_total)


def calcular_total_comisiones(pagos=None) -> Decimal:
    """Suma las comisiones cobradas. Sin argumento, sobre todo el histórico."""
    return totalizar(listar_pagos() if pagos is None else pagos, obtener_comision)


def resumir_caja(pagos=None) -> dict:
    """Arma el resumen de caja de una colección de pagos.

    Devuelve: cantidad | recaudado | comisiones | por_servicio
    """
    seleccion = listar_pagos() if pagos is None else pagos
    return {
        "cantidad": len(seleccion),
        "recaudado": calcular_total_recaudado(seleccion),
        "comisiones": calcular_total_comisiones(seleccion),
        "por_servicio": contar_por_servicio(seleccion),
    }


def limpiar_repositorio() -> None:
    """Vacía el histórico de pagos.

    Existe solo para reiniciar el estado entre pruebas. El menú no debe
    ofrecer esta operación.
    """
    _pagos.clear()


# --------------------------------------------------------------------------- #
# Formato para presentación (devuelve texto, no imprime)
# --------------------------------------------------------------------------- #
def describir_pago_registrado(pago: dict) -> str:
    """Antepone el número de registro al resumen del pago.

    Ejemplo: `#000001 | 2026-07-26 10:15:00 | Juan Pérez | LUZ | $ 38.20 | ...`
    """
    return f"#{obtener_secuencial(pago):06d} | {describir_pago(pago)}"


def describir_resumen(resumen: dict) -> str:
    """Resume la caja en una línea.

    Ejemplo: `3 pago(s) | Recaudado: $ 114.60 | Comisiones: $ 2.25`
    """
    return (
        f"{resumen['cantidad']} pago(s) | "
        f"Recaudado: {formatear(resumen['recaudado'])} | "
        f"Comisiones: {formatear(resumen['comisiones'])}"
    )