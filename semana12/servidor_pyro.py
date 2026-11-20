"""Servidor Pyro5 del servicio de pagos (Pasarela + Transaccion)."""
import os
import sys
import threading
import time

from Pyro5.api import Daemon, locate_ns
from Pyro5.errors import CommunicationError, NamingError

from objetos import MODO, Pasarela

HOST = os.environ.get("SERVIDOR_HOST", "servidor")
PUERTO = int(os.environ.get("SERVIDOR_PUERTO", "9100"))
NS_HOST = os.environ.get("NOMBRES_HOST", "nombres")
NS_PUERTO = int(os.environ.get("NOMBRES_PUERTO", "9090"))
EQUIPO = os.environ.get("EQUIPO", "pagos")
REREGISTRO = int(os.environ.get("REREGISTRO", "0"))
NOMBRE = f"sd.{EQUIPO}.pasarela"


def log(msg):
    print(time.strftime("%H:%M:%S"), "[servidor]", msg, flush=True)


def registrar(uri, intentos=30):
    """Publica la URI en el servidor de nombres; reintenta si no arranca."""
    for i in range(intentos):
        try:
            with locate_ns(host=NS_HOST, port=NS_PUERTO) as ns:
                ns.register(NOMBRE, uri)
            return True
        except (NamingError, CommunicationError) as e:
            log(f"sin servidor de nombres ({e}); reintento {i + 1}")
            time.sleep(1)
    return False


def reregistrar_cada(uri, segundos):
    """Se registra periódicamente si se habilitó REREGISTRO."""
    while True:
        time.sleep(segundos)
        try:
            with locate_ns(host=NS_HOST, port=NS_PUERTO) as ns:
                ns.register(NOMBRE, uri)
        except (NamingError, CommunicationError):
            log("re-registro falló: servidor de nombres no disponible")


def main():
    daemon = Daemon(host=HOST, port=PUERTO)
    # Registrar la CLASE, no Pasarela(): respeta MODO=single/session.
    uri = daemon.register(Pasarela, objectId="pasarela")
    log(f"daemon escuchando, modo de instancia {MODO}")
    log(f"URI {uri}")
    if not registrar(uri):
        log("no pude registrarme en el servidor de nombres")
        sys.exit(1)
    log(f"registrado como {NOMBRE}")
    if REREGISTRO > 0:
        threading.Thread(target=reregistrar_cada,
                         args=(uri, REREGISTRO), daemon=True).start()
        log(f"re-registro cada {REREGISTRO} s activado")
    daemon.requestLoop()


if __name__ == "__main__":
    main()
