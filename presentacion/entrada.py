"""Captura de datos desde la consola.

Este módulo concentra TODOS los `input()` del sistema. Su responsabilidad es
obtener datos limpios y bien formados; las reglas de negocio no se evalúan
aquí.
"""

from decimal import Decimal

from config.constantes import (
    ESTADOS_CLIENTE_VALIDOS,
    ETIQUETAS_MENU,
    RESPUESTAS_AFIRMATIVAS,
    RESPUESTAS_NEGATIVAS,
)
from core.excepciones import (
    DatoInvalidoError,
    MontoInvalidoError,
    ServicioNoDisponibleError,
)
from core.validaciones import normalizar_codigo
from dominio.clientes import validar_estado, validar_nombre, validar_saldo
from dominio.operadores import validar_nombre_operador
from dominio.pagos import validar_monto
from dominio.servicios import listar_servicios, validar_servicio
from presentacion.salida import (
    mostrar_ayuda,
    mostrar_error,
    mostrar_opcion_invalida,
    mostrar_servicios_disponibles,
)
from aplicacion.gestion_clientes import (
    hay_clientes_registrados,
    listar_clientes,
    obtener_cliente_por_posicion,
    registrar_nuevo_cliente,
)
from presentacion.salida import (
    mostrar_aviso,
    mostrar_cliente_registrado,
    mostrar_cliente_seleccionado,
    mostrar_clientes_para_seleccion,
    mostrar_titulo_alta_cliente,
)

# Errores que el operador puede corregir volviendo a digitar. Cualquier otra
# excepción se propaga: no es un problema de captura.
ERRORES_REINTENTABLES = (
    DatoInvalidoError,
    ServicioNoDisponibleError,
    MontoInvalidoError,
)

MENSAJE_NOMBRE_OPERADOR = "Nombre del operador que inicia turno: "
MENSAJE_OPERADOR_ENTRANTE = "Nombre del operador entrante: "
MENSAJE_NOMBRE_CLIENTE = "Nombre del cliente: "
MENSAJE_ESTADO_CLIENTE = "Estado del cliente (ACTIVO/BLOQUEADO): "
MENSAJE_SALDO = "Saldo disponible: "
MENSAJE_SERVICIO = "Servicio a pagar: "
MENSAJE_VALOR = "Valor del servicio: "
MENSAJE_OPCION = "Seleccione una opción: "
MENSAJE_PAUSA = "Presione ENTER para continuar..."
MENSAJE_SELECCION_CLIENTE = "Número del cliente: "
PREGUNTA_CLIENTE_NUEVO = "¿Desea operar con un cliente NUEVO?"
MENSAJE_CARTERA_VACIA = "No hay clientes registrados. Debe registrar uno para continuar."

AYUDA_NOMBRE = "Solo letras y espacios. Ejemplo: Juan Pérez"
AYUDA_SALDO = "Use punto decimal y no incluya el símbolo. Ejemplo: 100.00"
AYUDA_VALOR = "Use punto decimal y no incluya el símbolo. Ejemplo: 37.45"
AYUDA_CONFIRMACION = "Responda S (sí) o N (no)."


# --------------------------------------------------------------------------- #
# Primitiva de lectura
# --------------------------------------------------------------------------- #
def _leer(mensaje: str) -> str:
    """Lee una línea de la consola y le quita los espacios de los extremos.
    """
    try:
        return input(mensaje).strip()
    except EOFError:
        raise KeyboardInterrupt from None


# --------------------------------------------------------------------------- #
# Solicitador genérico
# --------------------------------------------------------------------------- #
def solicitar(mensaje: str, validador, ayuda: str = ""):
    """Pide un dato hasta que el validador lo acepte, y devuelve el valor limpio.
    """
    while True:
        try:
            return validador(_leer(mensaje))
        except ERRORES_REINTENTABLES as error:
            mostrar_error(error.mensaje)
            if ayuda:
                mostrar_ayuda(ayuda)


# --------------------------------------------------------------------------- #
# Captura de campos individuales
# --------------------------------------------------------------------------- #
def solicitar_nombre_cliente() -> str:
    """Pide el nombre del cliente y lo devuelve capitalizado."""
    return solicitar(MENSAJE_NOMBRE_CLIENTE, validar_nombre, AYUDA_NOMBRE)


def solicitar_estado_cliente() -> str:
    """Pide el estado del cliente y lo devuelve normalizado al catálogo.

    Acepta la entrada en minúsculas o con tildes: `activo` -> `ACTIVO`.
    """
    ayuda = f"Valores permitidos: {', '.join(ESTADOS_CLIENTE_VALIDOS)}"
    return solicitar(MENSAJE_ESTADO_CLIENTE, validar_estado, ayuda)


def solicitar_saldo() -> Decimal:
    """Pide el saldo disponible del cliente."""
    return solicitar(MENSAJE_SALDO, validar_saldo, AYUDA_SALDO)


def solicitar_servicio() -> str:
    """Muestra el catálogo y pide el servicio a pagar.
    """
    mostrar_servicios_disponibles()
    ayuda = f"Servicios válidos: {', '.join(listar_servicios())}"
    return solicitar(MENSAJE_SERVICIO, validar_servicio, ayuda)


def solicitar_valor(servicio: str) -> Decimal:
    """Pide el valor del servicio, validado contra el tope de ese servicio.
    """
    return solicitar(
        MENSAJE_VALOR, lambda texto: validar_monto(texto, servicio), AYUDA_VALOR
    )


def solicitar_nombre_operador(mensaje: str = MENSAJE_NOMBRE_OPERADOR) -> str:
    """Pide el nombre del operador responsable del turno."""
    return solicitar(mensaje, validar_nombre_operador, AYUDA_NOMBRE)


def solicitar_operador_entrante() -> str:
    """Pide el nombre del operador que asume la caja en un relevo."""
    return solicitar_nombre_operador(MENSAJE_OPERADOR_ENTRANTE)

# --------------------------------------------------------------------------- #
# Selección y alta de clientes
# --------------------------------------------------------------------------- #
def solicitar_indice(mensaje: str, cantidad: int) -> int:
    """Pide un número de lista y devuelve su índice (base cero).

    No lanza excepción ante un valor fuera de rango: informa y vuelve a
    preguntar, igual que el menú. Elegir mal un número de lista es un error
    de tecleo, no un evento del sistema.
    """
    while True:
        texto = _leer(mensaje)

        if texto.isdigit() and 1 <= int(texto) <= cantidad:
            return int(texto) - 1

        mostrar_error(f"Debe ingresar un número entre 1 y {cantidad}.")


def seleccionar_cliente_registrado() -> dict:
    """Muestra la cartera y devuelve el cliente elegido por el operador."""
    clientes = listar_clientes()
    mostrar_clientes_para_seleccion(clientes)

    indice = solicitar_indice(MENSAJE_SELECCION_CLIENTE, len(clientes))
    cliente = obtener_cliente_por_posicion(indice)

    mostrar_cliente_seleccionado(cliente)
    return cliente


def solicitar_alta_cliente() -> dict:
    """Captura los datos de un cliente nuevo y lo registra en la cartera.

    Los reintentos por dato inválido los resuelve `solicitar()`. Un nombre
    duplicado, en cambio, se propaga como error de negocio: no es un problema
    de digitación, sino un intento de crear algo que ya existe.

    Raises:
        ClienteDuplicadoError: si el cliente ya está registrado.
    """
    mostrar_titulo_alta_cliente()

    nombre = solicitar_nombre_cliente()
    estado = solicitar_estado_cliente()
    saldo = solicitar_saldo()

    cliente = registrar_nuevo_cliente(nombre, estado, saldo)
    mostrar_cliente_registrado(cliente)
    return cliente


def obtener_cliente_para_pago() -> dict:
    """Resuelve con qué cliente se procesará el pago.

    Con la cartera vacía el alta es obligatoria: no existe forma de pagar sin
    un titular registrado. Con clientes disponibles, se pregunta primero, para
    que el caso frecuente (cliente recurrente) sea el camino corto.
    """
    if not hay_clientes_registrados():
        mostrar_aviso(MENSAJE_CARTERA_VACIA)
        return solicitar_alta_cliente()

    if confirmar(PREGUNTA_CLIENTE_NUEVO):
        return solicitar_alta_cliente()

    return seleccionar_cliente_registrado()


# --------------------------------------------------------------------------- #
# Captura del caso de uso (FUNCIÓN REQUERIDA)
# --------------------------------------------------------------------------- #
def solicitar_datos() -> dict:
    """Captura todos los datos necesarios para procesar un pago.
    [FUNCIÓN REQUERIDA]

    El cliente ya NO se digita en cada pago: se selecciona de la cartera o se
    da de alta una sola vez. Su estado y su saldo se leen del registro, de
    modo que reflejan los débitos anteriores.

    El servicio se pide antes que el valor porque el tope máximo del monto
    depende del servicio elegido.

    Devuelve: nombre | estado | saldo | servicio | valor
    """
    cliente = obtener_cliente_para_pago()

    servicio = solicitar_servicio()
    valor = solicitar_valor(servicio)

    return {
        "nombre": cliente["nombre"],
        "estado": cliente["estado"],
        "saldo": cliente["saldo"],
        "servicio": servicio,
        "valor": valor,
    }


# --------------------------------------------------------------------------- #
# Interacción con el menú
# --------------------------------------------------------------------------- #
def solicitar_opcion_menu() -> str:
    """Pide una opción del menú y la devuelve solo si existe en el catálogo.
    """
    opciones_validas = tuple(ETIQUETAS_MENU.keys())

    while True:
        opcion = _leer(MENSAJE_OPCION)
        if opcion in opciones_validas:
            return opcion
        mostrar_opcion_invalida(opciones_validas)


def confirmar(pregunta: str) -> bool:
    """Pide una confirmación y devuelve `True` solo ante una respuesta afirmativa.

    Acepta S, SI, sí, N o NO en cualquier combinación de mayúsculas o tildes.
    """
    while True:
        respuesta = normalizar_codigo(_leer(f"{pregunta} (S/N): "))

        if respuesta in RESPUESTAS_AFIRMATIVAS:
            return True
        if respuesta in RESPUESTAS_NEGATIVAS:
            return False

        mostrar_error("Respuesta no reconocida.")
        mostrar_ayuda(AYUDA_CONFIRMACION)


def pausar() -> None:
    """Detiene la ejecución hasta que el operador presione ENTER.
    """
    _leer(f"\n{MENSAJE_PAUSA}")