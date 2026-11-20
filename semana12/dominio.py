"""
Dominio del servicio, sin nada de red. Semana 11.

Este archivo es lo que NO cambia cuando cambia el transporte. Lo usan
rpc.py (JSON-RPC, semana 10) y servidor_grpc.py (gRPC, semana 11).
El equipo reemplaza el inventario de referencia por las operaciones de su
dominio, las mismas que ya tenía en semana10/rpc.py.
"""
import threading

_lock = threading.Lock()

cuentas = {
    "ana": 100000,
    "beto": 20000,
    "caja": 0,
}


class ErrorDominio(Exception):
    """Errores de las reglas del negocio."""


class ErrorParametros(Exception):
    """Errores en los parametros recibidos."""


def validar_cuenta(cuenta):
    if not isinstance(cuenta, str) or not cuenta.strip():
        raise ErrorParametros("La cuenta debe ser un texto no vacio")

    return cuenta.strip().lower()


def saldo(cuenta: str):
    cuenta = validar_cuenta(cuenta)

    with _lock:
        if cuenta not in cuentas:
            raise ErrorDominio(f"CUENTA_NO_EXISTE: {cuenta}")

        return {
            "cuenta": cuenta,
            "saldo": cuentas[cuenta]
        }


def transferir(origen: str, destino: str, monto: int):
    origen = validar_cuenta(origen)
    destino = validar_cuenta(destino)

    if type(monto) is not int or monto <= 0:
        raise ErrorParametros("El monto debe ser un entero positivo")

    if origen == destino:
        raise ErrorDominio("MISMA_CUENTA")

    with _lock:
        if origen not in cuentas or destino not in cuentas:
            raise ErrorDominio("CUENTA_NO_EXISTE")

        if cuentas[origen] < monto:
            raise ErrorDominio(
                f"SALDO_INSUFICIENTE: {cuentas[origen]}"
            )

        cuentas[origen] -= monto
        cuentas[destino] += monto

        return {
            "origen": origen,
            "saldo_origen": cuentas[origen],
            "destino": destino,
            "saldo_destino": cuentas[destino]
        }
