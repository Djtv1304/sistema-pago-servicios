"""Persistencia de los clientes de la cooperativa.

Cada cliente se almacena como el `dict` que produce `dominio.clientes`:
    nombre | estado | saldo
"""

from decimal import Decimal

from core.dinero import formatear, sumar
from core.excepciones import ClienteDuplicadoError, ClienteNoRegistradoError
from core.validaciones import normalizar_codigo
from dominio.clientes import describir_cliente, obtener_saldo, validar_nombre

# Estado interno. La clave es el nombre normalizado; el valor, el cliente.
# Un `dict` da búsqueda inmediata y garantiza la unicidad por construcción.
_clientes: dict[str, dict] = {}


# --------------------------------------------------------------------------- #
# Identidad
# --------------------------------------------------------------------------- #
def _clave(nombre: str) -> str:
    """Devuelve la clave de identidad de un cliente a partir de su nombre.

    Valida primero el formato y luego normaliza: así un nombre inválido se
    rechaza antes de convertirse en clave.
    """
    return normalizar_codigo(validar_nombre(nombre))


# --------------------------------------------------------------------------- #
# Consultas (sin efectos secundarios)
# --------------------------------------------------------------------------- #
def existe_cliente(nombre: str) -> bool:
    """Indica si el cliente ya está registrado, sin lanzar excepción."""
    return _clave(nombre) in _clientes


def buscar_cliente(nombre: str) -> dict | None:
    """Devuelve una copia del cliente, o `None` si no está registrado."""
    encontrado = _clientes.get(_clave(nombre))
    return dict(encontrado) if encontrado else None


def obtener_cliente(nombre: str) -> dict:
    """Devuelve el cliente exigiendo que exista.

    Raises:
        ClienteNoRegistradoError: si el cliente no está en el repositorio.
    """
    cliente = buscar_cliente(nombre)
    if cliente is None:
        raise ClienteNoRegistradoError(nombre)
    return cliente


def listar_clientes() -> list[dict]:
    """Devuelve todos los clientes en orden de registro.

    Se entregan copias: el repositorio nunca expone sus estructuras internas
    para modificación directa.
    """
    return [dict(cliente) for cliente in _clientes.values()]


def obtener_por_posicion(indice: int) -> dict:
    """Devuelve el cliente ubicado en una posición del listado.

    Permite que el operador seleccione por número en lugar de digitar el
    nombre completo, que es más lento y propenso a errores.

    Raises:
        ClienteNoRegistradoError: si la posición no existe.
    """
    clientes = listar_clientes()
    if not 0 <= indice < len(clientes):
        raise ClienteNoRegistradoError(f"posición {indice + 1}")
    return clientes[indice]


def contar_clientes() -> int:
    """Devuelve la cantidad de clientes registrados."""
    return len(_clientes)


def hay_clientes() -> bool:
    """Indica si existe al menos un cliente registrado."""
    return contar_clientes() > 0


def calcular_saldo_total() -> Decimal:
    """Suma el saldo de todos los clientes registrados."""
    return sumar(*(obtener_saldo(cliente) for cliente in _clientes.values()))


# --------------------------------------------------------------------------- #
# Registro y actualización
# --------------------------------------------------------------------------- #
def registrar_cliente(cliente: dict) -> dict:
    """Asienta un cliente nuevo y devuelve el registro almacenado.

    Guarda una copia, no la referencia recibida: el llamador no puede alterar
    el repositorio manipulando su propio diccionario después.

    Raises:
        ClienteDuplicadoError: si ya existe un cliente con ese nombre.
    """
    clave = _clave(cliente["nombre"])

    if clave in _clientes:
        raise ClienteDuplicadoError(cliente["nombre"])

    _clientes[clave] = dict(cliente)
    return dict(_clientes[clave])


def actualizar_cliente(cliente: dict) -> dict:
    """Reemplaza los datos de un cliente ya registrado.

    Es la operación que persiste el saldo tras un débito. Exige que el cliente
    exista: actualizar a alguien inexistente sería crearlo por la puerta
    trasera, saltándose la validación de duplicados.

    Raises:
        ClienteNoRegistradoError: si el cliente no está registrado.
    """
    clave = _clave(cliente["nombre"])

    if clave not in _clientes:
        raise ClienteNoRegistradoError(cliente["nombre"])

    _clientes[clave] = dict(cliente)
    return dict(_clientes[clave])


def limpiar_repositorio() -> None:
    """Vacía el registro de clientes. Solo para reiniciar el estado en pruebas."""
    _clientes.clear()


# --------------------------------------------------------------------------- #
# Formato para presentación (devuelve texto, no imprime)
# --------------------------------------------------------------------------- #
def describir_cliente_registrado(cliente: dict) -> str:
    """Resume un cliente en una línea: `Juan Pérez | ACTIVO | $ 61.80`."""
    return describir_cliente(cliente)


def describir_opcion_cliente(indice: int, cliente: dict) -> str:
    """Numera un cliente para el listado de selección.

    Ejemplo: `[1] Juan Pérez | ACTIVO | $ 61.80`
    """
    return f"[{indice + 1}] {describir_cliente_registrado(cliente)}"


def describir_resumen_clientes() -> str:
    """Resume la cartera: `3 cliente(s) | Saldo total: $ 412.30`."""
    return (
        f"{contar_clientes()} cliente(s) | "
        f"Saldo total: {formatear(calcular_saldo_total())}"
    )