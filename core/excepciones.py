"""
Jerarquía de excepciones del sistema de pago de servicios.

Todas heredan de `ErrorSistemaPagos`, lo que permite que la capa de
presentación capture un único tipo base y muestre siempre un mensaje
controlado, sin exponer trazas técnicas al operador de ventanilla.

"""

from decimal import Decimal

def _texto_monto(monto: Decimal) -> str:
    """Formatea un importe para el mensaje de error.
    """
    from core.dinero import formatear

    return formatear(monto)

class ErrorSistemaPagos(Exception):
    """Excepción base. Nunca se lanza directamente."""

    codigo = "ERR_GENERICO"

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje

    def __str__(self) -> str:
        return f"[{self.codigo}] {self.mensaje}"


# --------------------------------------------------------------------------- #
# Errores de turnos
# --------------------------------------------------------------------------- #
class TurnoNoIniciadoError(ErrorSistemaPagos):
    """Se intentó operar sin un turno de caja abierto.

    Es la garantía estructural de que ningún pago ni registro de auditoría
    puede existir sin un operador responsable identificado.
    """

    codigo = "ERR_SIN_TURNO"

    def __init__(self) -> None:
        super().__init__("No hay un turno de caja abierto. Registre al operador responsable.")


# --------------------------------------------------------------------------- #
# Errores de reglas de negocio
# --------------------------------------------------------------------------- #
class ClienteBloqueadoError(ErrorSistemaPagos):
    """El cliente no está en estado ACTIVO."""

    codigo = "ERR_CLIENTE_BLOQUEADO"

    def __init__(self, nombre_cliente: str) -> None:
        super().__init__(
            f"El cliente '{nombre_cliente}' está BLOQUEADO. No se pueden "
            f"procesar pagos con su cuenta."
        )
        self.nombre_cliente = nombre_cliente


class SaldoInsuficienteError(ErrorSistemaPagos):
    """El saldo disponible no cubre el total a debitar (valor + comisión).

    Recibe montos `Decimal`, nunca texto
    """

    codigo = "ERR_SALDO_INSUFICIENTE"

    def __init__(self, saldo_disponible: Decimal, total_requerido: Decimal) -> None:
        faltante = total_requerido - saldo_disponible
        super().__init__(
            f"Saldo insuficiente. "
            f"Disponible: {_texto_monto(saldo_disponible)} | "
            f"Requerido: {_texto_monto(total_requerido)} | "
            f"Faltante: {_texto_monto(faltante)}."
        )
        self.saldo_disponible = saldo_disponible
        self.total_requerido = total_requerido
        self.faltante = faltante


class ServicioNoDisponibleError(ErrorSistemaPagos):
    """El servicio solicitado no pertenece al catálogo habilitado."""

    codigo = "ERR_SERVICIO_NO_DISPONIBLE"

    def __init__(self, servicio: str, servicios_validos) -> None:
        super().__init__(
            f"El servicio '{servicio}' no está disponible. "
            f"Opciones válidas: {', '.join(servicios_validos)}."
        )
        self.servicio = servicio


class MontoInvalidoError(ErrorSistemaPagos):
    """El valor del servicio no cumple los límites permitidos."""

    codigo = "ERR_MONTO_INVALIDO"

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)


class ServicioYaPagadoError(ErrorSistemaPagos):
    """El cliente ya canceló ese servicio en la jornada."""

    codigo = "ERR_SERVICIO_YA_PAGADO"

    def __init__(self, nombre_cliente: str, servicio: str) -> None:
        super().__init__(
            f"'{nombre_cliente}' ya pagó el servicio de {servicio}. "
            f"No se admite un segundo cobro."
        )
        self.nombre_cliente = nombre_cliente
        self.servicio = servicio


class SinServiciosPendientesError(ErrorSistemaPagos):
    """El cliente no tiene servicios por pagar."""

    codigo = "ERR_SIN_PENDIENTES"

    def __init__(self, nombre_cliente: str) -> None:
        super().__init__(
            f"'{nombre_cliente}' no registra servicios pendientes. "
            f"Su cuenta está al día."
        )
        self.nombre_cliente = nombre_cliente


# --------------------------------------------------------------------------- #
# Errores de entrada de datos
# --------------------------------------------------------------------------- #
class DatoInvalidoError(ErrorSistemaPagos):
    """Un dato ingresado no cumple el formato o el tipo esperado."""

    codigo = "ERR_DATO_INVALIDO"

    def __init__(self, campo: str, detalle: str) -> None:
        super().__init__(f"Campo '{campo}': {detalle}")
        self.campo = campo
        self.detalle = detalle

# --------------------------------------------------------------------------- #
# Errores de clientes
# --------------------------------------------------------------------------- #
class ClienteNoRegistradoError(ErrorSistemaPagos):
    """Se intentó operar con un cliente que no existe en la cartera."""

    codigo = "ERR_CLIENTE_NO_REGISTRADO"

    def __init__(self, referencia: str) -> None:
        super().__init__(
            f"El cliente '{referencia}' no se encuentra registrado. "
            f"Regístrelo antes de operar."
        )
        self.referencia = referencia


class ClienteDuplicadoError(ErrorSistemaPagos):
    """Se intentó registrar un cliente que ya existe."""

    codigo = "ERR_CLIENTE_DUPLICADO"

    def __init__(self, nombre: str) -> None:
        super().__init__(
            f"El cliente '{nombre}' ya está registrado. "
            f"Selecciónelo del listado en lugar de crearlo nuevamente."
        )
        self.nombre = nombre