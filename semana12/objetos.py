"""Objetos distribuidos para pagos electrónicos. Semana 12, Pyro5.

Pasarela: entrada remota, delega consultas y transferencias a dominio.py.
Transaccion: objeto con estado propio, creado por fábrica y entregado por
referencia; se desregistra del daemon cuando se confirma o cancela.
"""
import os
import threading
import time

from Pyro5.api import behavior, current_context, expose

import dominio

MODO = os.environ.get("MODO", "single")
POR_VALOR = os.environ.get("POR_VALOR", "0") == "1"
_contador_instancias = 0
_lock_contador = threading.Lock()


def _nueva_instancia():
    global _contador_instancias
    with _lock_contador:
        _contador_instancias += 1
        return _contador_instancias


@expose
class Transaccion:
    """Transferencia pendiente con estado en el servidor y vida explícita.

    Guarda origen, destino y monto; el cliente recibe un Proxy y no una copia.
    """

    def __init__(self, origen):
        self.origen = origen
        self.destino = None
        self.monto = None
        self.estado = "pendiente"
        self.creado = time.strftime("%H:%M:%S")

    def configurar(self, destino, monto):
        """Modifica el estado pendiente, sin mover todavía dinero."""
        destino = dominio.validar_cuenta(destino)
        if type(monto) is not int or monto <= 0:
            raise dominio.ErrorParametros("El monto debe ser un entero positivo")
        if destino == self.origen:
            raise dominio.ErrorDominio("MISMA_CUENTA")
        dominio.saldo(destino)  # verifica que la cuenta de destino exista
        self.destino = destino
        self.monto = monto
        return self.ver()

    def ver(self):
        """Consulta el estado de la transacción, por valor (un diccionario)."""
        return {"origen": self.origen, "destino": self.destino,
                "monto": self.monto, "estado": self.estado,
                "creado": self.creado}

    def confirmar(self):
        """Transfiere fondos y desregistra este objeto, cambiando el estado."""
        if self.destino is None or self.monto is None:
            raise dominio.ErrorParametros("Primero debe configurar destino y monto")
        # Se reutiliza la operación real de la semana 11.
        resultado = dominio.transferir(self.origen, self.destino, self.monto)
        self.estado = "autorizada"
        self._terminar()
        return resultado

    def cancelar(self):
        """Cancela sin mover fondos y desregistra el objeto (cambia estado)."""
        self.estado = "cancelada"
        self._terminar()
        return "transacción cancelada"

    def _terminar(self):
        """Elimina la referencia del daemon; la URI queda colgante."""
        self._pyroDaemon.unregister(self)


@expose
@behavior(instance_mode=MODO)
class Pasarela:
    """Punto de entrada remoto para operaciones del sistema de pagos."""

    def __init__(self):
        self.numero = _nueva_instancia()
        self.llamadas = 0

    def _contar(self):
        self.llamadas += 1

    def saldo(self, cuenta):
        """Consulta el saldo; no modifica el dominio (sí cuenta la llamada)."""
        self._contar()
        return dominio.saldo(cuenta)

    def transferir(self, origen, destino, monto):
        """Transfiere fondos en el dominio; modifica los saldos compartidos."""
        self._contar()
        return dominio.transferir(origen, destino, monto)

    def listar(self):
        """Consulta saldos de las cuentas existentes; no modifica el dominio."""
        self._contar()
        return [dominio.saldo(cuenta) for cuenta in dominio.cuentas]

    def quien_soy(self):
        """Consulta instancia y aumenta su contador; distingue single/session."""
        self._contar()
        return {"modo": MODO, "instancia": self.numero,
                "llamadas": self.llamadas,
                "cliente": str(current_context.client_sock_addr)}

    def transacciones_vivas(self):
        """Cuenta transacciones registradas; solo altera contador de llamadas."""
        self._contar()
        return sum(1 for obj in self._pyroDaemon.objectsById.values()
                   if isinstance(obj, Transaccion))

    def iniciar_transaccion(self, origen):
        """Crea una Transaccion con estado y devuelve una referencia remota."""
        self._contar()
        origen = dominio.validar_cuenta(origen)
        dominio.saldo(origen)  # verifica existencia de la cuenta
        transaccion = Transaccion(origen)
        if POR_VALOR:
            # Experimento del taller: sin registrar, falla la deserialización.
            return transaccion
        self._pyroDaemon.register(transaccion)
        return transaccion
