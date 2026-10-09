"""Servidor TCP concurrente — plantilla de la Semana 6 (hilo por cliente).

Dominio de referencia: INVENTARIO (equipo E-commerce). Cada equipo reemplaza
las operaciones por las de su propio dominio, manteniendo la estructura:
  - un hilo por cliente
  - estado compartido protegido por un Lock
  - manejo explícito de errores y desconexión abrupta
  - logging con identificador del cliente en cada línea

Protocolo por líneas, UTF-8, terminador "\n". Ver protocolo.md.
"""
import logging
import os
import socket
import threading
import time

HOST = os.environ.get("HOST", "0.0.0.0")
PUERTO = int(os.environ.get("PUERTO", "5000"))
SIN_LOCK = os.environ.get("SIN_LOCK", "0") == "1"
TIMEOUT_CLIENTE = int(os.environ.get("TIMEOUT_CLIENTE", "60"))

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [servidor] %(threadName)s %(message)s")

# ----------------------------------------------------------------- estado compartido
estado = {
    "cuentas": {"ana": 100000, "beto": 20000, "caja": 0},
    "movimientos": [],          # (origen, destino, monto) en orden
    "operaciones": 0,
}
lock = threading.Lock()


class SinLock:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def seccion_critica():
    return SinLock() if SIN_LOCK else lock


# ----------------------------------------------------------------- helpers
def parsear_monto(txt):
    """Devuelve el monto entero positivo o None si es inválido."""
    if not txt.isdigit():
        return None
    monto = int(txt)
    return monto if monto > 0 else None


# ----------------------------------------------------------------- operaciones del dominio
def op_saldo(arg):
    partes = arg.split()
    if len(partes) != 1:
        return "ERROR FORMATO SALDO <cuenta>"
    cuenta = partes[0].lower()
    with seccion_critica():
        if cuenta not in estado["cuentas"]:
            return "ERROR CUENTA_NO_EXISTE"
        saldo = estado["cuentas"][cuenta]
    return f"OK {cuenta} {saldo}"


def op_depositar(arg):
    partes = arg.split()
    if len(partes) != 2:
        return "ERROR FORMATO DEPOSITAR <cuenta> <monto>"
    cuenta, monto = partes[0].lower(), parsear_monto(partes[1])
    if monto is None:
        return "ERROR MONTO_INVALIDO"
    with seccion_critica():
        if cuenta not in estado["cuentas"]:
            return "ERROR CUENTA_NO_EXISTE"
        actual = estado["cuentas"][cuenta]
        time.sleep(0.001)                      # ventana para observar la carrera sin Lock
        estado["cuentas"][cuenta] = actual + monto
        estado["movimientos"].append(("externo", cuenta, monto))
        nuevo = estado["cuentas"][cuenta]
    return f"OK {cuenta} {nuevo}"


def op_retirar(arg):
    partes = arg.split()
    if len(partes) != 2:
        return "ERROR FORMATO RETIRAR <cuenta> <monto>"
    cuenta, monto = partes[0].lower(), parsear_monto(partes[1])
    if monto is None:
        return "ERROR MONTO_INVALIDO"
    with seccion_critica():
        if cuenta not in estado["cuentas"]:
            return "ERROR CUENTA_NO_EXISTE"
        actual = estado["cuentas"][cuenta]
        if actual < monto:
            return f"ERROR SALDO_INSUFICIENTE {actual}"
        time.sleep(0.001)
        estado["cuentas"][cuenta] = actual - monto
        estado["movimientos"].append((cuenta, "externo", monto))
        nuevo = estado["cuentas"][cuenta]
    return f"OK {cuenta} {nuevo}"


def op_transferir(arg):
    partes = arg.split()
    if len(partes) != 3:
        return "ERROR FORMATO TRANSFERIR <origen> <destino> <monto>"
    origen, destino, monto = partes[0].lower(), partes[1].lower(), parsear_monto(partes[2])
    if monto is None:
        return "ERROR MONTO_INVALIDO"
    if origen == destino:
        return "ERROR MISMA_CUENTA"
    with seccion_critica():
        if origen not in estado["cuentas"] or destino not in estado["cuentas"]:
            return "ERROR CUENTA_NO_EXISTE"
        saldo_origen = estado["cuentas"][origen]
        if saldo_origen < monto:
            return f"ERROR SALDO_INSUFICIENTE {saldo_origen}"
        saldo_destino = estado["cuentas"][destino]
        time.sleep(0.001)
        # descuento y suma dentro de la MISMA sección crítica
        estado["cuentas"][origen] = saldo_origen - monto
        estado["cuentas"][destino] = saldo_destino + monto
        estado["movimientos"].append((origen, destino, monto))
        n_origen = estado["cuentas"][origen]
        n_destino = estado["cuentas"][destino]
    return f"OK {origen} {n_origen} {destino} {n_destino}"


def op_total(arg):
    """Suma de todos los saldos (para la demo del invariante)."""
    with seccion_critica():
        total = sum(estado["cuentas"].values())
    return f"OK TOTAL {total}"


def op_espera(arg):
    try:
        seg = float(arg)
    except ValueError:
        return "ERROR FORMATO ESPERA <segundos>"
    time.sleep(seg)                            # operación lenta, NO toma el Lock
    return f"OK ESPERA {arg}"


OPERACIONES = {
    "SALDO": op_saldo,
    "DEPOSITAR": op_depositar,
    "RETIRAR": op_retirar,
    "TRANSFERIR": op_transferir,
    "TOTAL": op_total,
    "ESPERA": op_espera,
}

def procesar(linea):
    """Devuelve (respuesta, seguir)."""
    partes = linea.strip().split(" ", 1)
    cmd = partes[0].upper() if partes and partes[0] else ""
    arg = partes[1] if len(partes) > 1 else ""
    if cmd == "HOLA":
        return f"OK HOLA {arg or 'anonimo'}", True
    if cmd == "SALIR":
        return "OK CHAO", False
    if cmd in OPERACIONES:
        with seccion_critica():
            estado["operaciones"] += 1
        return OPERACIONES[cmd](arg), True
    return "ERROR COMANDO_DESCONOCIDO", True


# ----------------------------------------------------------------- atención de un cliente
def atender(conn, addr):
    logging.info("conexion de %s", addr)
    conn.settimeout(TIMEOUT_CLIENTE)
    try:
        with conn, conn.makefile("r", encoding="utf-8", errors="replace") as entrada:
            for linea in entrada:
                respuesta, seguir = procesar(linea)
                conn.sendall((respuesta + "\n").encode("utf-8"))
                if not seguir:
                    break
    except (ConnectionResetError, BrokenPipeError) as e:
        logging.warning("cliente %s se desconecto abruptamente (%s)", addr, e.__class__.__name__)
    except socket.timeout:
        logging.warning("cliente %s inactivo %ss, cerrando", addr, TIMEOUT_CLIENTE)
    except Exception as e:  # noqa: BLE001  — un cliente nunca puede botar el servidor
        logging.error("error inesperado con %s: %r", addr, e)
    finally:
        logging.info("cierre de %s | operaciones=%s", addr, estado["operaciones"])


def main():
    logging.info("SIN_LOCK=%s timeout=%ss", SIN_LOCK, TIMEOUT_CLIENTE)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PUERTO))
        srv.listen(64)
        logging.info("escuchando en %s:%s", HOST, PUERTO)
        while True:
            conn, addr = srv.accept()
            threading.Thread(target=atender, args=(conn, addr),
                             name=f"cli-{addr[1]}", daemon=True).start()


if __name__ == "__main__":
    main()
