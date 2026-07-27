"""Presentación de información en pantalla.

Este módulo concentra TODOS los `print()` del sistema. Ningún otro archivo
imprime: los demás módulos devuelven texto y aquí se decide cómo se muestra.

Esa concentración es lo que permitiría migrar la interfaz a una ventana
gráfica, a un log o a una API reescribiendo solo este archivo, sin tocar una
sola regla de negocio.

El módulo no calcula ni valida nada: recibe datos ya resueltos y los dibuja.
"""

from config.constantes import (
    ANCHO_PANTALLA,
    NOMBRE_APLICACION,
    PREFIJO_AVISO,
    PREFIJO_AYUDA,
    PREFIJO_ERROR,
    PREFIJO_EXITO,
    VERSION_APLICACION,
)
from core.dinero import formatear
from dominio.clientes import describir_cliente
from dominio.comprobantes import renderizar_comprobante
from dominio.operadores import describir_operador, describir_turno
from dominio.pagos import describir_detalle
from dominio.servicios import listar_servicios, obtener_descripcion

CARACTER_BORDE = "="
CARACTER_DIVISOR = "-"

TITULO_MENU = "MENÚ PRINCIPAL"
TITULO_SERVICIOS = "SERVICIOS DISPONIBLES"
TITULO_CONFIRMACION = "DETALLE DE LA TRANSACCIÓN"
TITULO_CIERRE_TURNO = "TURNO CERRADO"
TITULO_RELEVO = "CAMBIO DE TURNO"
TITULO_SELECCION_CLIENTE = "SELECCIONE UN CLIENTE"
TITULO_ALTA_CLIENTE = "REGISTRO DE NUEVO CLIENTE"


# --------------------------------------------------------------------------- #
# Primitivas de dibujo
# --------------------------------------------------------------------------- #
def mostrar_linea_en_blanco() -> None:
    """Imprime una línea vacía como separador visual."""
    print()


def mostrar_borde() -> None:
    """Imprime la línea sólida que delimita una sección."""
    print(CARACTER_BORDE * ANCHO_PANTALLA)


def mostrar_divisor() -> None:
    """Imprime la línea punteada que separa bloques internos."""
    print(CARACTER_DIVISOR * ANCHO_PANTALLA)


def mostrar_texto(texto: str) -> None:
    """Imprime un texto tal cual, sin decoración."""
    print(texto)


def mostrar_centrado(texto: str) -> None:
    """Imprime un texto centrado en el ancho de pantalla."""
    print(texto.center(ANCHO_PANTALLA))


def mostrar_titulo(titulo: str) -> None:
    """Imprime un encabezado de sección enmarcado."""
    mostrar_linea_en_blanco()
    mostrar_borde()
    mostrar_centrado(titulo)
    mostrar_borde()


# --------------------------------------------------------------------------- #
# Mensajes con intención
# Cada tipo de mensaje tiene su propia función para que el prefijo sea
# consistente en todo el sistema y no dependa de cómo lo escriba cada llamador.
# --------------------------------------------------------------------------- #
def mostrar_exito(mensaje: str) -> None:
    """Informa que una operación se completó correctamente."""
    print(f"{PREFIJO_EXITO} {mensaje}")


def mostrar_error(mensaje: str) -> None:
    """Informa que una operación fue rechazada."""
    print(f"{PREFIJO_ERROR} {mensaje}")


def mostrar_aviso(mensaje: str) -> None:
    """Informa una advertencia que no interrumpe la operación."""
    print(f"{PREFIJO_AVISO} {mensaje}")


def mostrar_ayuda(mensaje: str) -> None:
    """Orienta al operador sobre el formato esperado tras un dato inválido."""
    print(f"{PREFIJO_AYUDA} {mensaje}")


# --------------------------------------------------------------------------- #
# Pantallas de inicio y cierre
# --------------------------------------------------------------------------- #
def mostrar_bienvenida() -> None:
    """Presenta la aplicación al arrancar el programa."""
    mostrar_borde()
    mostrar_centrado(NOMBRE_APLICACION)
    mostrar_centrado(f"Versión {VERSION_APLICACION}")
    mostrar_borde()


def mostrar_despedida() -> None:
    """Cierra la ejecución del programa."""
    mostrar_linea_en_blanco()
    mostrar_borde()
    mostrar_centrado("Sistema finalizado. Hasta pronto.")
    mostrar_borde()


# --------------------------------------------------------------------------- #
# Menú
# --------------------------------------------------------------------------- #
def mostrar_menu(etiquetas: dict, firma_operador: str) -> None:
    """Dibuja el menú principal con el operador vigente en el encabezado.

    Mostrar siempre quién está en turno no es decorativo: es lo que evita que
    un operador registre pagos a nombre de quien lo relevó.
    """
    mostrar_titulo(TITULO_MENU)
    mostrar_texto(f" Operador en turno: {firma_operador}")
    mostrar_divisor()
    for opcion, descripcion in etiquetas.items():
        mostrar_texto(f"  [{opcion}] {descripcion}")
    mostrar_divisor()


def mostrar_servicios_disponibles() -> None:
    """Lista el catálogo de servicios habilitados con su descripción."""
    mostrar_texto(f" {TITULO_SERVICIOS}:")
    for servicio in listar_servicios():
        mostrar_texto(f"   - {servicio:<10} ({obtener_descripcion(servicio)})")


# --------------------------------------------------------------------------- #
# Transacción de pago
# --------------------------------------------------------------------------- #
def mostrar_detalle_a_confirmar(detalle: dict, cliente_nombre: str) -> None:
    """Muestra el cálculo antes de ejecutar el débito.

    Es la última oportunidad del operador para detectar un error de digitación
    sin haber afectado el saldo del cliente.
    """
    mostrar_titulo(TITULO_CONFIRMACION)
    mostrar_texto(f" Cliente : {cliente_nombre}")
    mostrar_texto(f" {describir_detalle(detalle)}")
    mostrar_divisor()


def mostrar_comprobante(comprobante: dict) -> None:
    """Imprime el comprobante de pago completo."""
    mostrar_linea_en_blanco()
    mostrar_texto(renderizar_comprobante(comprobante))


def mostrar_saldo_actualizado(cliente_actualizado: dict) -> None:
    """Informa el estado final del cliente tras el débito."""
    mostrar_exito(f"Saldo actualizado: {describir_cliente(cliente_actualizado)}")


def mostrar_resultado_pago(resultado: dict) -> None:
    """Presenta el desenlace completo de un pago aprobado.

    Recibe el diccionario que devuelve `procesar_pago()` y decide qué mostrar
    de él; la capa de aplicación no sabe nada de esta presentación.
    """
    mostrar_comprobante(resultado["comprobante"])
    mostrar_linea_en_blanco()
    mostrar_saldo_actualizado(resultado["cliente_actualizado"])


# --------------------------------------------------------------------------- #
# Reportes
# --------------------------------------------------------------------------- #
def mostrar_reporte(reporte: dict) -> None:
    """Dibuja cualquier reporte armado por `aplicacion/consultas.py`.

    titulo | lineas | resumen | vacio.
    """
    mostrar_titulo(reporte["titulo"])

    for linea in reporte["lineas"]:
        mostrar_texto(f" {linea}")

    if reporte["vacio"]:
        mostrar_borde()
        return

    mostrar_divisor()
    mostrar_texto(f" {reporte['resumen']}")
    mostrar_borde()

# --------------------------------------------------------------------------- #
# Clientes
# --------------------------------------------------------------------------- #
def mostrar_clientes_para_seleccion(clientes: list) -> None:
    """Dibuja el listado numerado de clientes disponibles para operar."""
    from infraestructura.repositorio_clientes import describir_opcion_cliente

    mostrar_titulo(TITULO_SELECCION_CLIENTE)
    for indice, cliente in enumerate(clientes):
        mostrar_texto(f"  {describir_opcion_cliente(indice, cliente)}")
    mostrar_divisor()


def mostrar_titulo_alta_cliente() -> None:
    """Anuncia el inicio de la captura de un cliente nuevo."""
    mostrar_titulo(TITULO_ALTA_CLIENTE)


def mostrar_cliente_registrado(cliente: dict) -> None:
    """Confirma el alta de un cliente en la cartera."""
    mostrar_exito(f"Cliente registrado: {describir_cliente(cliente)}")


def mostrar_cliente_seleccionado(cliente: dict) -> None:
    """Confirma con qué cliente se va a operar."""
    mostrar_texto(f" Cliente seleccionado: {describir_cliente(cliente)}")

# --------------------------------------------------------------------------- #
# Turnos
# --------------------------------------------------------------------------- #
def mostrar_turno_iniciado(operador: dict) -> None:
    """Confirma la apertura de un turno de caja."""
    mostrar_exito(f"Turno iniciado: {describir_operador(operador)}")


def mostrar_relevo(saliente: dict, entrante: dict) -> None:
    """Presenta el cambio de operador con el detalle del turno saliente."""
    mostrar_titulo(TITULO_RELEVO)
    mostrar_texto(f" Saliente : {describir_turno(saliente)}")
    mostrar_texto(f" Entrante : {describir_operador(entrante)}")
    mostrar_borde()


def mostrar_cierre_de_turno(turno_cerrado: dict) -> None:
    """Presenta el detalle del turno al finalizar la jornada."""
    mostrar_titulo(TITULO_CIERRE_TURNO)
    mostrar_texto(f" {describir_turno(turno_cerrado)}")
    mostrar_borde()


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #
def mostrar_monto(etiqueta: str, monto) -> None:
    """Imprime un importe con su etiqueta: ` Recaudado: $ 114.60`."""
    mostrar_texto(f" {etiqueta}: {formatear(monto)}")


def mostrar_opcion_invalida(opciones_validas) -> None:
    """Informa que la opción digitada no existe en el menú."""
    disponibles = ", ".join(str(opcion) for opcion in opciones_validas)
    mostrar_error(f"Opción no válida. Opciones disponibles: {disponibles}")