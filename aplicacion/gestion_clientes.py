"""Casos de uso relacionados con la administración de clientes.
"""

from decimal import Decimal

from dominio.clientes import crear_cliente, describir_cliente
from infraestructura import repositorio_clientes as repositorio
from infraestructura.auditoria import auditar_cliente_registrado
from aplicacion.sesion import exigir_turno_activo


# --------------------------------------------------------------------------- #
# Consultas del estado de la cartera
# --------------------------------------------------------------------------- #
def hay_clientes_registrados() -> bool:
    """Indica si existe al menos un cliente con el que operar."""
    return repositorio.hay_clientes()


def listar_clientes() -> list[dict]:
    """Devuelve la cartera completa de clientes."""
    return repositorio.listar_clientes()


def obtener_cliente_por_posicion(indice: int) -> dict:
    """Devuelve el cliente seleccionado desde el listado numerado.

    Raises:
        ClienteNoRegistradoError: si la posición no existe.
    """
    return repositorio.obtener_por_posicion(indice)


# --------------------------------------------------------------------------- #
# Registro de clientes
# --------------------------------------------------------------------------- #
def registrar_nuevo_cliente(nombre: str, estado: str, saldo) -> dict:
    """Da de alta un cliente en la cartera y deja constancia en la bitácora.

    El cliente se construye con `crear_cliente()`, que valida los tres campos:
    si algo no cumple, no llega a persistirse nada.

    Raises:
        TurnoNoIniciadoError: si no hay turno de caja abierto.
        DatoInvalidoError: si algún campo no cumple su formato.
        ClienteDuplicadoError: si el cliente ya está registrado.
    """
    operador = exigir_turno_activo()

    cliente = crear_cliente(nombre, estado, saldo)
    registrado = repositorio.registrar_cliente(cliente)

    auditar_cliente_registrado(operador, registrado)
    return registrado


# --------------------------------------------------------------------------- #
# Sincronización tras un pago
# --------------------------------------------------------------------------- #
def sincronizar_saldo(cliente_actualizado: dict) -> dict:
    """Persiste el saldo resultante de un débito.

    Es el paso que hace que el pago tenga efecto duradero: sin esta llamada,
    el cliente volvería a mostrar su saldo anterior en la siguiente consulta.

    No se audita por separado porque el saldo anterior y el nuevo ya quedan
    asentados dentro del propio registro de pago; un segundo evento sería
    información duplicada.

    Raises:
        ClienteNoRegistradoError: si el cliente no está en la cartera.
    """
    return repositorio.actualizar_cliente(cliente_actualizado)


# --------------------------------------------------------------------------- #
# Formato para presentación (devuelve texto, no imprime)
# --------------------------------------------------------------------------- #
def describir_alta(cliente: dict) -> str:
    """Resume el alta de un cliente: `Juan Pérez | ACTIVO | $ 100.00`."""
    return describir_cliente(cliente)