"""Constantes de configuración del sistema de pago de servicios.

Este módulo no contiene lógica: es la única fuente de verdad para catálogos,
tasas y límites. Cualquier ajuste de negocio (comisión, topes, servicios
disponibles) se hace aquí y se propaga al resto del sistema.
"""

from decimal import Decimal

# --------------------------------------------------------------------------- #
# Identidad de la aplicación
# --------------------------------------------------------------------------- #
NOMBRE_APLICACION = "Cooperativa - Pago de Servicios Básicos"
VERSION_APLICACION = "1.0.0"

# --------------------------------------------------------------------------- #
# Configuración monetaria
# --------------------------------------------------------------------------- #
SIMBOLO_MONEDA = "$"
DECIMALES_MONEDA = 2
PORCENTAJE_COMISION = Decimal("0.02")  # 2% sobre el valor del servicio

MONTO_MINIMO_PAGO = Decimal("0.01")
MONTO_MAXIMO_PAGO = Decimal("5000.00")

# --------------------------------------------------------------------------- #
# Estados del cliente
# --------------------------------------------------------------------------- #
ESTADO_CLIENTE_ACTIVO = "ACTIVO"
ESTADO_CLIENTE_BLOQUEADO = "BLOQUEADO"
ESTADOS_CLIENTE_VALIDOS = (ESTADO_CLIENTE_ACTIVO, ESTADO_CLIENTE_BLOQUEADO)

# --------------------------------------------------------------------------- #
# Catálogo de servicios habilitados
# La clave es el código que digita el operador; el valor describe el servicio
# y su tope individual (un pago de agua no puede ser de $4.000).
# --------------------------------------------------------------------------- #
SERVICIO_AGUA = "AGUA"
SERVICIO_LUZ = "LUZ"
SERVICIO_INTERNET = "INTERNET"
SERVICIO_TELEFONIA = "TELEFONIA"

SERVICIOS_DISPONIBLES = {
    SERVICIO_AGUA: {
        "codigo": "AGU",
        "descripcion": "Agua Potable",
        "monto_maximo": Decimal("300.00"),
    },
    SERVICIO_LUZ: {
        "codigo": "LUZ",
        "descripcion": "Energía Eléctrica",
        "monto_maximo": Decimal("500.00"),
    },
    SERVICIO_INTERNET: {
        "codigo": "INT",
        "descripcion": "Internet Fijo",
        "monto_maximo": Decimal("250.00"),
    },
    SERVICIO_TELEFONIA: {
        "codigo": "TEL",
        "descripcion": "Telefonía Móvil",
        "monto_maximo": Decimal("200.00"),
    },
}

# --------------------------------------------------------------------------- #
# Reglas de entrada de datos
# --------------------------------------------------------------------------- #
LONGITUD_MINIMA_NOMBRE = 3
LONGITUD_MAXIMA_NOMBRE = 60
MAXIMO_INTENTOS_LOGIN = 3

# --------------------------------------------------------------------------- #
# Turnos de caja
# --------------------------------------------------------------------------- #
PREFIJO_TURNO = "TRN"
LONGITUD_SECUENCIAL_TURNO = 6

# --------------------------------------------------------------------------- #
# Comprobantes y auditoría
# --------------------------------------------------------------------------- #
PREFIJO_COMPROBANTE = "CMP"
LONGITUD_SECUENCIAL_COMPROBANTE = 6
FORMATO_FECHA_HORA = "%Y-%m-%d %H:%M:%S"

# --------------------------------------------------------------------------- #
# Eventos de auditoría
# --------------------------------------------------------------------------- #
EVENTO_TURNO_INICIADO = "TURNO_INICIADO"
EVENTO_TURNO_CERRADO = "TURNO_CERRADO"
EVENTO_PAGO_APROBADO = "PAGO_APROBADO"
EVENTO_PAGO_RECHAZADO = "PAGO_RECHAZADO"
EVENTO_CONSULTA_HISTORIAL = "CONSULTA_HISTORIAL"
EVENTO_CLIENTE_REGISTRADO = "CLIENTE_REGISTRADO"
EVENTO_CONSULTA_CLIENTES = "CONSULTA_CLIENTES"
EVENTO_ESTADO_CLIENTE_CAMBIADO = "ESTADO_CLIENTE_CAMBIADO"

# --------------------------------------------------------------------------- #
# Opciones del menú principal
# --------------------------------------------------------------------------- #
OPCION_REGISTRAR_PAGO = "1"
OPCION_REGISTRAR_CLIENTE = "2"
OPCION_CAMBIAR_ESTADO_CLIENTE = "3"
OPCION_CARGAR_DEMO = "4"
OPCION_VER_CLIENTES = "5"
OPCION_VER_HISTORIAL = "6"
OPCION_VER_AUDITORIA = "7"
OPCION_CAMBIAR_TURNO = "8"
OPCION_SALIR = "0"

ETIQUETAS_MENU = {
    OPCION_REGISTRAR_PAGO: "Registrar pago de servicio",
    OPCION_REGISTRAR_CLIENTE: "Registrar nuevo cliente",
    OPCION_CAMBIAR_ESTADO_CLIENTE: "Activar / bloquear un cliente",
    OPCION_CARGAR_DEMO: "Cargar clientes de demostración",
    OPCION_VER_CLIENTES: "Ver clientes registrados",
    OPCION_VER_HISTORIAL: "Ver historial de pagos",
    OPCION_VER_AUDITORIA: "Ver bitácora de auditoría",
    OPCION_CAMBIAR_TURNO: "Cambiar turno de operador",
    OPCION_SALIR: "Cerrar turno y salir",
}

# --------------------------------------------------------------------------- #
# Presentación del comprobante
# --------------------------------------------------------------------------- #
ANCHO_COMPROBANTE = 46
MENSAJE_PIE_COMPROBANTE = "Documento generado electrónicamente"

# --------------------------------------------------------------------------- #
# Resultados de auditoría
# --------------------------------------------------------------------------- #
RESULTADO_EXITOSO = "EXITOSO"
RESULTADO_RECHAZADO = "RECHAZADO"

PREFIJO_AUDITORIA = "AUD"
LONGITUD_SECUENCIAL_AUDITORIA = 6

EVENTOS_AUDITABLES = (
    EVENTO_TURNO_INICIADO,
    EVENTO_TURNO_CERRADO,
    EVENTO_CLIENTE_REGISTRADO,
    EVENTO_ESTADO_CLIENTE_CAMBIADO,
    EVENTO_PAGO_APROBADO,
    EVENTO_PAGO_RECHAZADO,
    EVENTO_CONSULTA_HISTORIAL,
    EVENTO_CONSULTA_CLIENTES,
)

# --------------------------------------------------------------------------- #
# Presentación en pantalla
# --------------------------------------------------------------------------- #
ANCHO_PANTALLA = 70

PREFIJO_EXITO = "[OK]"
PREFIJO_ERROR = "[X]"
PREFIJO_AVISO = "[!]"
PREFIJO_AYUDA = "  ->"

# --------------------------------------------------------------------------- #
# Respuestas de confirmación
# --------------------------------------------------------------------------- #
RESPUESTAS_AFIRMATIVAS = ("S", "SI")
RESPUESTAS_NEGATIVAS = ("N", "NO")