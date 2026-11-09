"""
Cliente gRPC del servicio, semana 11.

Uso
  python cliente_grpc.py listar
  python cliente_grpc.py agregar tornillo 25
  python cliente_grpc.py quitar tornillo 5 --reintentos 2

Variables
  SERVIDOR_HOST    (servidor)   SERVIDOR_PUERTO (50051)
  TIMEOUT_CLIENTE  (2)          deadline de cada intento, en segundos
  REINTENTOS       (0)          intentos extra ante DEADLINE_EXCEEDED o UNAVAILABLE

Cada reintento manda el MISMO id_solicitud.
"""
import argparse
import os
import uuid

import grpc

import servicio_pb2 as pb
import servicio_pb2_grpc as pb_grpc

HOST = os.getenv("SERVIDOR_HOST", "servidor")
PUERTO = os.getenv("SERVIDOR_PUERTO", "50051")
REINTENTABLES = {grpc.StatusCode.DEADLINE_EXCEEDED, grpc.StatusCode.UNAVAILABLE}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("metodo", choices=["saldo", "transferir"])
    ap.add_argument("cuenta", nargs="?", default="")
    ap.add_argument("destino", nargs="?", default="")
    ap.add_argument("monto", nargs="?", type=int, default=0)
    ap.add_argument("--reintentos", type=int, default=int(os.getenv("REINTENTOS", "0")))
    ap.add_argument("--timeout", type=float, default=float(os.getenv("TIMEOUT_CLIENTE", "2")))
    a = ap.parse_args()

    canal = grpc.insecure_channel(f"{HOST}:{PUERTO}")
    stub = pb_grpc.PagosStub(canal)

    if a.metodo == "saldo":
        if not a.cuenta:
            ap.error("saldo requiere una cuenta")

        llamada = stub.Saldo
        solicitud = pb.SaldoSolicitud(cuenta=a.cuenta)

    else:
        if not a.cuenta or not a.destino or a.monto <= 0:
            ap.error("transferir requiere origen, destino y monto positivo")

        solicitud = pb.TransferirSolicitud(
            id_solicitud=uuid.uuid4().hex[:8],
            origen=a.cuenta,
            destino=a.destino,
            monto=a.monto
        )

        llamada = stub.Transferir


    for intento in range(1, a.reintentos + 2):
        ids = getattr(solicitud, "id_solicitud", "-")
        print(f"[cliente] intento {intento}, id_solicitud={ids}, deadline {a.timeout:.0f} s")
        try:
            resp = llamada(solicitud, timeout=a.timeout)
        except grpc.RpcError as e:
            print(f"[cliente]   {e.code().name}, {e.details()}")
            if e.code() in REINTENTABLES:
                continue
            return 1

        if a.metodo == "saldo":
            print(f"[cliente]   OK {resp.cuenta} saldo={resp.saldo}")
        else:
            print(
                f"[cliente]   OK transferencia "
                f"{resp.origen}={resp.saldo_origen} "
                f"{resp.destino}={resp.saldo_destino}"
            )
        return 0

    return 1



if __name__ == "__main__":
    raise SystemExit(main())
