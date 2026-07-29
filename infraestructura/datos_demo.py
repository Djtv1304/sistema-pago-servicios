"""Cartera de clientes precargados para demostración.

Datos de prueba con planillas ya emitidas: cada cliente trae el importe que
le corresponde por cada servicio, tal como llegaría desde el sistema de la
empresa recaudadora. Con estos clientes el operador no digita el valor: lo
selecciona.
"""

from config.constantes import (
    ESTADO_CLIENTE_ACTIVO,
    ESTADO_CLIENTE_BLOQUEADO,
    SERVICIO_AGUA,
    SERVICIO_INTERNET,
    SERVICIO_LUZ,
    SERVICIO_TELEFONIA,
)

CLIENTES_DEMO = (
    {
        "nombre": "María Fernanda Loor",
        "estado": ESTADO_CLIENTE_ACTIVO,
        "saldo": "480.00",
        "valores": {
            SERVICIO_AGUA: "18.40",
            SERVICIO_LUZ: "42.75",
            SERVICIO_INTERNET: "29.99",
            SERVICIO_TELEFONIA: "22.50",
        },
    },
    {
        # Saldo ajustado: alcanza para los servicios pequeños, no para todos.
        "nombre": "Carlos Andrés Villacís",
        "estado": ESTADO_CLIENTE_ACTIVO,
        "saldo": "95.00",
        "valores": {
            SERVICIO_AGUA: "21.60",
            SERVICIO_LUZ: "58.30",
            SERVICIO_INTERNET: "34.90",
            SERVICIO_TELEFONIA: "19.99",
        },
    },
    {
        # Cliente bloqueado: permite demostrar el rechazo y su auditoría.
        "nombre": "Rosa Elena Chiluiza",
        "estado": ESTADO_CLIENTE_BLOQUEADO,
        "saldo": "250.00",
        "valores": {
            SERVICIO_AGUA: "15.20",
            SERVICIO_LUZ: "38.45",
            SERVICIO_INTERNET: "27.00",
            SERVICIO_TELEFONIA: "18.75",
        },
    },
    {
        "nombre": "Jorge Patricio Zambrano",
        "estado": ESTADO_CLIENTE_ACTIVO,
        "saldo": "1200.00",
        "valores": {
            SERVICIO_AGUA: "45.80",
            SERVICIO_LUZ: "180.25",
            SERVICIO_INTERNET: "59.99",
            SERVICIO_TELEFONIA: "35.40",
        },
    },
    {
        # Ya canceló luz y telefonía: llega con dos servicios pendientes.
        "nombre": "Ana Belén Cedeño",
        "estado": ESTADO_CLIENTE_ACTIVO,
        "saldo": "160.00",
        "pendientes": (SERVICIO_AGUA, SERVICIO_INTERNET),
        "valores": {
            SERVICIO_AGUA: "12.90",
            SERVICIO_INTERNET: "31.50",
        },
    },
)


def listar_datos_demo() -> tuple[dict, ...]:
    """Devuelve la cartera de demostración."""
    return CLIENTES_DEMO


def contar_datos_demo() -> int:
    """Devuelve cuántos clientes trae la cartera de demostración."""
    return len(CLIENTES_DEMO)