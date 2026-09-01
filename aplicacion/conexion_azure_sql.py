"""Caso de uso para probar conectividad a Azure SQL desde variables de entorno."""

from infraestructura.conexion_azure_sql import (
    construir_configuracion_desde_entorno,
    probar_conexion_azure_sql,
)


def probar_conexion() -> dict:
    """Carga la configuración desde entorno, prueba conexión y devuelve resumen."""
    configuracion = construir_configuracion_desde_entorno()
    probar_conexion_azure_sql(configuracion)
    return {
        "server": configuracion["server"],
        "database": configuracion["database"],
        "port": configuracion["port"],
        "timeout": configuracion["timeout"],
    }
