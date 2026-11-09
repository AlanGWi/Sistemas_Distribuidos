"""servidor.py — servidor TCP con hilo por cliente y mensajes estructurados (Semana 9).

Evoluciona el servidor de la semana 6/7. Cambia solo la forma de leer y
escribir mensajes. Antes, una línea de texto. Ahora, un mensaje enmarcado y
codificado con codec.py (JSON o binario según la variable CODEC).

El dominio de referencia es un inventario (LISTAR, AGREGAR, QUITAR). Cada
equipo reemplaza esas operaciones por las de su propio servicio.
"""
import json
import os
import socket
import struct
import threading
import time

import codec
from mensajes import Solicitud, VERSION, ok, error

HOST = "0.0.0.0"
PUERTO = int(os.environ.get("SERVIDOR_PUERTO", "5000"))
TIMEOUT = float(os.environ.get("TIMEOUT_SERVIDOR", "30"))

# Estado compartido del servicio de pagos
SIN_LOCK = os.environ.get("SIN_LOCK", "0") == "1"

estado = {
    "cuentas": {
        "ana": 100000,
        "beto": 20000,
        "caja": 0
    },
    "movimientos": [],
    "operaciones": 0,
}

lock = threading.Lock()


def log(*args):
    print(time.strftime("%H:%M:%S"), f"[{threading.current_thread().name}]", *args, flush=True)

class SinLock:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def seccion_critica():
    return SinLock() if SIN_LOCK else lock

def parsear_monto(txt):
    """Devuelve el monto entero positivo o None si es inválido."""
    if not txt.isdigit():
        return None

    monto = int(txt)
    return monto if monto > 0 else None


# ---------------------------------------------------------------- dominio
def procesar(sol):
    """Recibe una Solicitud y devuelve una Respuesta del servicio de pagos."""
    op = sol.operacion.upper()
    args = sol.argumentos

    # Saludo y despedida
    if op == "HOLA":
        nombre = " ".join(args) or "anonimo"
        return ok(sol, ["HOLA", nombre])

    if op == "SALIR":
        return ok(sol, ["CHAO"])

    # Comprobar que la operación pertenece al dominio
    operaciones = (
        "SALDO", "DEPOSITAR", "RETIRAR",
        "TRANSFERIR", "TOTAL", "ESPERA",
    )

    if op not in operaciones:
        return error(sol.id, "COMANDO_DESCONOCIDO")

    with seccion_critica():
        estado["operaciones"] += 1

    # Consultar saldo
    if op == "SALDO":
        if len(args) != 1:
            return error(sol.id, "FORMATO SALDO <cuenta>")

        cuenta = args[0].lower()

        with seccion_critica():
            if cuenta not in estado["cuentas"]:
                return error(sol.id, "CUENTA_NO_EXISTE")
            saldo = estado["cuentas"][cuenta]

        return ok(sol, [cuenta, str(saldo)])

    # Depositar dinero
    if op == "DEPOSITAR":
        if len(args) != 2:
            return error(sol.id, "FORMATO DEPOSITAR <cuenta> <monto>")

        cuenta = args[0].lower()
        monto = parsear_monto(args[1])

        if monto is None:
            return error(sol.id, "MONTO_INVALIDO")

        with seccion_critica():
            if cuenta not in estado["cuentas"]:
                return error(sol.id, "CUENTA_NO_EXISTE")

            actual = estado["cuentas"][cuenta]
            time.sleep(0.001)
            estado["cuentas"][cuenta] = actual + monto
            estado["movimientos"].append(("externo", cuenta, monto))
            nuevo = estado["cuentas"][cuenta]

        return ok(sol, [cuenta, str(nuevo)])

    # Retirar dinero
    if op == "RETIRAR":
        if len(args) != 2:
            return error(sol.id, "FORMATO RETIRAR <cuenta> <monto>")

        cuenta = args[0].lower()
        monto = parsear_monto(args[1])

        if monto is None:
            return error(sol.id, "MONTO_INVALIDO")

        with seccion_critica():
            if cuenta not in estado["cuentas"]:
                return error(sol.id, "CUENTA_NO_EXISTE")

            actual = estado["cuentas"][cuenta]

            if actual < monto:
                return error(sol.id, f"SALDO_INSUFICIENTE {actual}")

            time.sleep(0.001)
            estado["cuentas"][cuenta] = actual - monto
            estado["movimientos"].append((cuenta, "externo", monto))
            nuevo = estado["cuentas"][cuenta]

        return ok(sol, [cuenta, str(nuevo)])

    # Transferir entre cuentas
    if op == "TRANSFERIR":
        if len(args) != 3:
            return error(sol.id, "FORMATO TRANSFERIR <origen> <destino> <monto>")

        origen = args[0].lower()
        destino = args[1].lower()
        monto = parsear_monto(args[2])

        if monto is None:
            return error(sol.id, "MONTO_INVALIDO")

        if origen == destino:
            return error(sol.id, "MISMA_CUENTA")

        with seccion_critica():
            if origen not in estado["cuentas"] or destino not in estado["cuentas"]:
                return error(sol.id, "CUENTA_NO_EXISTE")

            saldo_origen = estado["cuentas"][origen]

            if saldo_origen < monto:
                return error(sol.id, f"SALDO_INSUFICIENTE {saldo_origen}")

            saldo_destino = estado["cuentas"][destino]
            time.sleep(0.001)

            estado["cuentas"][origen] = saldo_origen - monto
            estado["cuentas"][destino] = saldo_destino + monto
            estado["movimientos"].append((origen, destino, monto))

            nuevo_origen = estado["cuentas"][origen]
            nuevo_destino = estado["cuentas"][destino]

        return ok(sol, [
            origen, str(nuevo_origen),
            destino, str(nuevo_destino)
        ])

    # Suma de todos los saldos
    if op == "TOTAL":
        with seccion_critica():
            total = sum(estado["cuentas"].values())

        return ok(sol, ["TOTAL", str(total)])

    # Simular una operación lenta
    if op == "ESPERA":
        if len(args) != 1:
            return error(sol.id, "FORMATO ESPERA <segundos>")

        try:
            segundos = float(args[0])
            time.sleep(segundos)
        except (ValueError, OverflowError):
            return error(sol.id, "FORMATO ESPERA <segundos>")

        return ok(sol, ["ESPERA", args[0]])



# ---------------------------------------------------------------- conexión
def atender(conn, addr):
    conn.settimeout(TIMEOUT)
    log("conectado", addr)
    try:
        while True:
            try:
                sol = codec.recibir(conn, Solicitud)
            except ConnectionError:
                break
            except (struct.error, json.JSONDecodeError, UnicodeDecodeError, ValueError, KeyError, IndexError) as e:
                # Mensaje mal formado. El servidor responde y cierra ESTA conexión, no muere.
                nombre = "struct.error" if isinstance(e, struct.error) else type(e).__name__
                log("mensaje mal formado desde", addr, "->", nombre, e)
                codec.enviar(conn, error(0, f"mensaje mal formado ({nombre})"))
                break
            if sol.version != VERSION:
                log("versión no soportada", sol.version, "desde", addr)
                codec.enviar(conn, error(sol.id, f"versión {sol.version} no soportada, use {VERSION}"))
                continue
            log("solicitud", sol.id, sol.operacion, sol.argumentos)
            resp = procesar(sol)
            codec.enviar(conn, resp)
            if sol.operacion.upper() == "SALIR":
                break
    except socket.timeout:
        log("timeout de", addr, "sin mensajes completos en", TIMEOUT, "s")
    except OSError as e:
        log("error de red con", addr, e)
    finally:
        conn.close()
        log("desconectado", addr)


def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PUERTO))
    srv.listen(16)
    log(f"servidor pagos v{VERSION} en {HOST}:{PUERTO}  codec={codec.CODEC}  hilo por cliente")
    n = 0
    while True:
        conn, addr = srv.accept()
        n += 1
        threading.Thread(target=atender, args=(conn, addr), name=f"cli-{n}", daemon=True).start()


if __name__ == "__main__":
    main()
