"""Puerta HTTP (API REST) delante del servidor TCP de la Semana 6. Dominio PAGOS.

Cada peticion HTTP se TRADUCE a una linea del protocolo de texto, se envia
al servidor TCP y la respuesta se traduce de vuelta a JSON y a un codigo HTTP.

    GET  /cuentas/{cuenta}             ->  SALDO <cuenta>
    GET  /total                        ->  TOTAL
    POST /cuentas/{cuenta}/depositos   ->  DEPOSITAR <cuenta> <monto>
    POST /cuentas/{cuenta}/retiros     ->  RETIRAR   <cuenta> <monto>
    POST /transferencias               ->  TRANSFERIR <origen> <destino> <monto>

La API NO guarda nada. Todo el estado sigue viviendo en el servidor TCP.
"""
import os
import socket

from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel, Field

SERVIDOR_HOST = os.environ.get("SERVIDOR_HOST", "servidor")
SERVIDOR_PUERTO = int(os.environ.get("SERVIDOR_PUERTO", "5000"))
TIMEOUT_SERVIDOR = float(os.environ.get("TIMEOUT_SERVIDOR", "3"))
REPLICA = os.environ.get("REPLICA", socket.gethostname())

app = FastAPI(title="API de pagos", version="1.0",
              description="Puerta HTTP del servicio propio. Semana 7.")

NOMBRE = r"^[a-z0-9_]{1,30}$"
CUENTA = Path(pattern=NOMBRE, description="nombre de la cuenta, sin espacios")

# Codigo de error del protocolo de texto  ->  codigo de estado HTTP
ERRORES = {
    "CUENTA_NO_EXISTE": 404,        # el recurso no existe
    "SALDO_INSUFICIENTE": 409,      # peticion valida pero choca con el estado actual
    "MISMA_CUENTA": 400,            # origen y destino iguales
    "MONTO_INVALIDO": 400,
    "FORMATO": 400,                 # la peticion esta mal armada
    "COMANDO_DESCONOCIDO": 501,     # el servidor no implementa esa operacion
}


class Monto(BaseModel):
    monto: int = Field(gt=0, description="entero mayor que cero")


class Transferencia(BaseModel):
    origen: str = Field(pattern=NOMBRE)
    destino: str = Field(pattern=NOMBRE)
    monto: int = Field(gt=0, description="entero mayor que cero")


# ----------------------------------------------------------------- hablar con el nivel de datos
def pedir(linea: str) -> str:
    """Envia UNA linea al nivel de datos y devuelve UNA linea de respuesta."""
    try:
        with socket.create_connection((SERVIDOR_HOST, SERVIDOR_PUERTO),
                                      timeout=TIMEOUT_SERVIDOR) as s:
            s.sendall((linea + "\n").encode("utf-8"))
            respuesta = s.makefile("r", encoding="utf-8").readline().strip()
    except socket.timeout:
        raise HTTPException(504, {"error": "SERVIDOR_NO_RESPONDE", "replica": REPLICA})
    except OSError as e:                     # no resuelve el nombre, conexion rechazada, red caida
        raise HTTPException(503, {"error": "SERVIDOR_NO_DISPONIBLE",
                                  "detalle": e.__class__.__name__, "replica": REPLICA})
    if not respuesta:
        raise HTTPException(503, {"error": "SERVIDOR_CERRO_LA_CONEXION", "replica": REPLICA})
    return respuesta


def traducir(respuesta: str) -> list[str]:
    """'OK a b c' -> ['a','b','c'].  'ERROR CODIGO detalle' -> excepcion HTTP."""
    partes = respuesta.split()
    if partes[0] == "OK":
        return partes[1:]
    codigo = partes[1] if len(partes) > 1 else "DESCONOCIDO"
    raise HTTPException(ERRORES.get(codigo, 500),
                        {"error": codigo, "detalle": " ".join(partes[2:]), "replica": REPLICA})


# ----------------------------------------------------------------- recursos
@app.get("/salud")
def salud():
    return {"estado": "ok", "replica": REPLICA}


@app.get("/cuentas/{cuenta}")
def ver_cuenta(cuenta: str = CUENTA):
    nombre, saldo = traducir(pedir(f"SALDO {cuenta}"))
    return {"cuenta": nombre, "saldo": int(saldo), "replica": REPLICA}


@app.get("/total")
def ver_total():
    _, total = traducir(pedir("TOTAL"))
    return {"total": int(total), "replica": REPLICA}


@app.post("/cuentas/{cuenta}/depositos", status_code=201)
def depositar(mov: Monto, cuenta: str = CUENTA):
    nombre, saldo = traducir(pedir(f"DEPOSITAR {cuenta} {mov.monto}"))
    return {"cuenta": nombre, "saldo": int(saldo), "replica": REPLICA}


@app.post("/cuentas/{cuenta}/retiros", status_code=201)
def retirar(mov: Monto, cuenta: str = CUENTA):
    nombre, saldo = traducir(pedir(f"RETIRAR {cuenta} {mov.monto}"))
    return {"cuenta": nombre, "saldo": int(saldo), "replica": REPLICA}


@app.post("/transferencias", status_code=201)
def transferir(t: Transferencia):
    o, so, d, sd = traducir(pedir(f"TRANSFERIR {t.origen} {t.destino} {t.monto}"))
    return {"origen": {"cuenta": o, "saldo": int(so)},
            "destino": {"cuenta": d, "saldo": int(sd)},
            "replica": REPLICA}