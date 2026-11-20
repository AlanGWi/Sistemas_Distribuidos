"""Cliente del taller de pagos con Pyro5.

Comandos: uri, listar, saldo, transferir, transaccion, vivos, quien, vigilar.
Ejecutar con: docker compose exec cliente python cliente_pyro.py <comando>
"""
import argparse
import os
import sys
import time

from Pyro5.api import Proxy, locate_ns, register_dict_to_class
from Pyro5.errors import (CommunicationError, DaemonError, NamingError,
                          SerializeError, get_pyro_traceback)
import dominio

NS_HOST = os.environ.get("NOMBRES_HOST", "nombres")
NS_PUERTO = int(os.environ.get("NOMBRES_PUERTO", "9090"))
EQUIPO = os.environ.get("EQUIPO", "pagos")
NOMBRE = f"sd.{EQUIPO}.pasarela"


def _a_excepcion(nombre_clase, datos):
    """Reconstruye excepciones de dominio que llegaron por valor."""
    clase = getattr(dominio, nombre_clase.split(".")[-1])
    return clase(*datos.get("args", ()))


for _nombre in ("ErrorDominio", "ErrorParametros"):
    register_dict_to_class(f"dominio.{_nombre}", _a_excepcion)


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def pasarela():
    """Devuelve el proxy al servicio principal usando el servidor de nombres."""
    proxy = Proxy(f"PYRONAME:{NOMBRE}@{NS_HOST}:{NS_PUERTO}")
    proxy._pyroTimeout = 5
    return proxy


def cmd_uri(_):
    with locate_ns(host=NS_HOST, port=NS_PUERTO) as ns:
        log(f"{NOMBRE} -> {ns.lookup(NOMBRE)}")
        log(f"nombres registrados {sorted(ns.list().keys())}")


def cmd_listar(_):
    with pasarela() as p:
        log(f"saldos {p.listar()}")


def cmd_saldo(a):
    with pasarela() as p:
        log(f"saldo -> {p.saldo(a.cuenta)}")


def cmd_transferir(a):
    with pasarela() as p:
        log(f"transferir -> {p.transferir(a.origen, a.destino, a.monto)}")


def cmd_quien(a):
    """Prueba dos proxies en la misma instancia o sesión según MODO."""
    for etiqueta in ("proxy A", "proxy B"):
        with pasarela() as p:
            for _ in range(a.veces):
                log(f"{etiqueta} -> {p.quien_soy()}")


def cmd_vivos(_):
    with pasarela() as p:
        log(f"transacciones vivas: {p.transacciones_vivas()}")


def reintentar_confirmar(uri, segundos):
    """Reintenta la misma referencia tras una caída, sin crear otra transacción."""
    limite = time.monotonic() + segundos
    while True:
        try:
            with Proxy(uri) as t:
                t._pyroTimeout = 5
                return t.confirmar()
        except DaemonError:
            raise
        except CommunicationError as e:
            if "unknown object" in str(e) or time.monotonic() >= limite:
                raise
            time.sleep(1)


def cmd_transaccion(a):
    """Crea, prepara y confirma un objeto con estado recibido por Proxy."""
    with pasarela() as p:
        t = p.iniciar_transaccion(a.origen)
        t._pyroTimeout = 5
        log(f"recibí {type(t).__name__}, referencia {t._pyroUri}")
        log(f"configurar -> {t.configurar(a.destino, a.monto)}")
        log(f"estado remoto -> {t.ver()}")
        if a.esperar:
            log(f"espero {a.esperar} s antes de confirmar (momento para la falla)")
            time.sleep(a.esperar)
        if a.cancelar:
            log(f"cancelar -> {t.cancelar()}")
        else:
            try:
                resultado = t.confirmar()
            except CommunicationError:
                log("se perdió la conexión; reintento con la MISMA URI durante 30 s")
                resultado = reintentar_confirmar(t._pyroUri, 30)
            log(f"confirmar -> {resultado}")
        log("uso la referencia después de finalizar la transacción")
        try:
            t.ver()
        except (CommunicationError, DaemonError) as e:
            log(f"REFERENCIA COLGANTE (esperado): {type(e).__name__}: {e}")
        else:
            log("ADVERTENCIA: el objeto sigue respondiendo")


def cmd_vigilar(a):
    """Consulta saldos repetidamente, conservando el mismo proxy remoto."""
    p = pasarela()
    try:
        while True:
            try:
                log(f"ok, saldos {p.listar()}  [{p._pyroUri}]")
            except CommunicationError as e:
                log(f"FALLA de comunicación {type(e).__name__} {e}")
                try:
                    p._pyroReconnect(tries=1)
                    log("reconectado")
                except (CommunicationError, NamingError) as e2:
                    log(f"no pude reconectar {type(e2).__name__} {e2}")
            except NamingError as e:
                log(f"FALLA de nombres {e}")
            time.sleep(a.cada)
    finally:
        p._pyroRelease()


def main():
    parser = argparse.ArgumentParser(description="Cliente Pyro5 de pagos, semana 12")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("uri").set_defaults(f=cmd_uri)
    sub.add_parser("listar").set_defaults(f=cmd_listar)
    s = sub.add_parser("saldo")
    s.add_argument("cuenta")
    s.set_defaults(f=cmd_saldo)
    s = sub.add_parser("transferir")
    s.add_argument("origen")
    s.add_argument("destino")
    s.add_argument("monto", type=int)
    s.set_defaults(f=cmd_transferir)
    sub.add_parser("vivos").set_defaults(f=cmd_vivos)
    s = sub.add_parser("quien")
    s.add_argument("--veces", type=int, default=2)
    s.set_defaults(f=cmd_quien)
    s = sub.add_parser("transaccion")
    s.add_argument("origen")
    s.add_argument("destino")
    s.add_argument("monto", type=int)
    s.add_argument("--esperar", type=int, default=0)
    s.add_argument("--cancelar", action="store_true")
    s.set_defaults(f=cmd_transaccion)
    s = sub.add_parser("vigilar")
    s.add_argument("--cada", type=float, default=1)
    s.set_defaults(f=cmd_vigilar)
    a = parser.parse_args()
    try:
        a.f(a)
    except KeyboardInterrupt:
        pass
    except NamingError as e:
        log(f"ERROR de nombres. No encuentro {NOMBRE}. {e}")
        sys.exit(2)
    except DaemonError as e:
        log(f"ERROR del daemon. Referencia ya inexistente: {e}")
        sys.exit(3)
    except SerializeError as e:
        log(f"ERROR de serialización. El objeto no está registrado por referencia: {e}")
        sys.exit(4)
    except CommunicationError as e:
        if "unknown object" in str(e):
            log(f"ERROR. Referencia colgante: el objeto ya no existe. {e}")
            sys.exit(3)
        log(f"ERROR de comunicación. {type(e).__name__} {e}")
        sys.exit(5)
    except Exception as e:
        log(f"ERROR remoto {type(e).__name__} {e}")
        if os.environ.get("TRAZA") == "1":
            print("".join(get_pyro_traceback()))
        sys.exit(6)


if __name__ == "__main__":
    main()
