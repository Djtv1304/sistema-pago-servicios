"""Adaptador para probar conexión Azure SQL usando mssql-python."""

from os import getenv
from pathlib import Path

from core.excepciones import ConexionBaseDatosError, DatoInvalidoError
from core.validaciones import validar_entero_positivo, validar_texto_requerido

NOMBRE_ARCHIVO_ENTORNO = ".env"

VARIABLE_PUERTO = "AZURE_SQL_PORT"
VARIABLE_TIMEOUT = "AZURE_SQL_TIMEOUT"

PUERTO_POR_DEFECTO = 1433
TIMEOUT_POR_DEFECTO = 10


def _leer_env_local() -> dict[str, str]:
    """Lee un archivo .env local y devuelve pares clave-valor simples."""
    raiz_proyecto = Path(__file__).resolve().parent.parent
    ruta = raiz_proyecto / NOMBRE_ARCHIVO_ENTORNO
    if not ruta.exists():
        return {}

    variables = {}
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        contenido = linea.strip()
        if not contenido or contenido.startswith("#"):
            continue
        if "=" not in contenido:
            continue

        clave, valor = contenido.split("=", 1)
        clave_limpia = clave.strip()
        valor_limpio = valor.strip().strip('"').strip("'")
        if clave_limpia:
            variables[clave_limpia] = valor_limpio

    return variables


def _obtener_variable(nombre: str, desde_env: dict[str, str]) -> str:
    """Obtiene una variable priorizando entorno del proceso y luego .env local."""
    return str(getenv(nombre, desde_env.get(nombre, ""))).strip()


def _obtener_requerida(nombre: str, desde_env: dict[str, str]) -> str:
    """Obtiene y valida una variable obligatoria de conexión."""
    valor = _obtener_variable(nombre, desde_env)
    return validar_texto_requerido(nombre, valor)


def _obtener_entero(
        nombre: str, desde_env: dict[str, str], por_defecto: int, campo: str
) -> int:
    """Obtiene una variable numérica opcional con valor por defecto."""
    texto = _obtener_variable(nombre, desde_env)
    if not texto:
        return por_defecto

    if not texto.isdigit():
        raise DatoInvalidoError(campo, "debe ser un número entero mayor o igual a 1.")
    return validar_entero_positivo(campo, int(texto))


def construir_configuracion_desde_entorno() -> dict:
    """Construye la configuración de conexión a partir de entorno y .env."""
    variables_env = _leer_env_local()

    return {
        "server": _obtener_requerida("AZURE_SQL_SERVER", variables_env),
        "database": _obtener_requerida("AZURE_SQL_DATABASE", variables_env),
        "user": _obtener_requerida("AZURE_SQL_USER", variables_env),
        "password": _obtener_requerida("AZURE_SQL_PASSWORD", variables_env),
        "port": _obtener_entero(
            VARIABLE_PUERTO, variables_env, PUERTO_POR_DEFECTO, "AZURE_SQL_PORT"
        ),
        "timeout": _obtener_entero(
            VARIABLE_TIMEOUT, variables_env, TIMEOUT_POR_DEFECTO, "AZURE_SQL_TIMEOUT"
        ),
    }


def _obtener_conector():
    """Resuelve la función `connect` de la librería mssql-python."""
    try:
        from mssql import connect
    except ImportError as error:
        try:
            from mssql_python import connect
        except ImportError:
            raise ConexionBaseDatosError(
                "No se encontró la librería 'mssql-python' en el entorno.", str(error)
            ) from error

    return connect


def _cerrar_conexion(conexion) -> None:
    """Cierra la conexión abierta, exigiendo que el conector lo soporte."""
    if not hasattr(conexion, "close"):
        raise ConexionBaseDatosError(
            "La conexión se abrió, pero el objeto devuelto no soporta cierre explícito."
        )

    try:
        conexion.close()
    except Exception as error:
        raise ConexionBaseDatosError(
            "La conexión se abrió, pero falló el cierre de la sesión.", str(error)
        ) from error


def _abrir_conexion(connect, configuracion: dict):
    """Abre la conexión probando aliases de parámetros comunes."""
    parametros = {
        "server": configuracion["server"],
        "database": configuracion["database"],
        "uid": configuracion["user"],
        "pwd": configuracion["password"],
        "port": configuracion["port"],
        "timeout": configuracion["timeout"],
    }

    try:
        return connect(**parametros)
    except Exception as error:
        raise ConexionBaseDatosError(
            "No fue posible establecer la conexión con Azure SQL.", str(error)
        ) from error

    raise ConexionBaseDatosError(
        "La librería mssql-python rechazó la firma de conexión usada.",
        str(ultimo_error_tipo),
    )


def probar_conexion_azure_sql(configuracion: dict) -> None:
    """Prueba la conexión a Azure SQL abriendo y cerrando una sesión."""
    connect = _obtener_conector()
    conexion = _abrir_conexion(connect, configuracion)
    _cerrar_conexion(conexion)
