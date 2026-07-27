"""
Jerarquía de excepciones del sistema de pago de servicios.

Todas heredan de `ErrorSistemaPagos`, lo que permite que la capa de
presentación capture un único tipo base y muestre siempre un mensaje
controlado, sin exponer trazas técnicas al operador de ventanilla.

"""


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
    """El saldo disponible no cubre el total a debitar (valor + comisión)."""

    codigo = "ERR_SALDO_INSUFICIENTE"

    def __init__(self, saldo_disponible, total_requerido) -> None:
        faltante = total_requerido - saldo_disponible
        super().__init__(
            f"Saldo insuficiente. Disponible: {saldo_disponible} | "
            f"Requerido: {total_requerido} | Faltante: {faltante}."
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