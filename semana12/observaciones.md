# Observaciones, taller semana 12 (objetos distribuidos con Pyro5)

Equipo
Integrantes presentes
Fecha 13-11-2026

## Paso 1, nombres y servidor arriba

URI que entregó el servidor de nombres para `sd.<equipo>.inventario`
(pegar la salida de `python cliente_pyro.py uri`)

```
12:16:19 sd.pagos.pasarela -> PYRO:pasarela@servidor:9100
12:16:19 nombres registrados ['Pyro.NameServer', 'sd.pagos.pasarela']
```

¿Qué partes de la URI reconocen? (protocolo, identificador del objeto, nodo, puerto)

La URI `PYRO:pasarela@servidor:9100` utiliza el protocolo `PYRO`, identifica al objeto como `pasarela` y señala que está disponible en el nodo `servidor`, mediante el puerto `9100`. Por otra parte, el servidor de nombres se encuentra en `nombres:9090` y permite que el cliente resuelva el nombre lógico `sd.pagos.pasarela` para comunicarse con el servicio.


## Paso 2, su dominio como objeto remoto

Nuestro dominio corresponde a **pagos electrónicos**. La clase remota `Pasarela` expone las operaciones de consulta y transferencia, reutilizando la lógica de `dominio.py` de la Semana 11. También permite crear objetos `Transaccion` con estado propio, que se utilizan mediante referencias remotas.

| Clase | Método | ¿Cambia estado? |
| --- | --- | --- |
| `Pasarela` | `listar()` | No cambia los saldos; incrementa el contador de llamadas de la instancia. |
| `Pasarela` | `saldo(cuenta)` | No cambia los saldos; incrementa el contador de llamadas. |
| `Pasarela` | `transferir(origen, destino, monto)` | Sí, modifica los saldos de origen y destino. |
| `Pasarela` | `quien_soy()` | Sí, incrementa el contador propio de la instancia. |
| `Pasarela` | `iniciar_transaccion(origen)` | Sí, modifica los objetos activos del daemon. |
| `Pasarela` | `transacciones_vivas()` | No modifica los saldos; incrementa el contador de llamadas. |
| `Transaccion` | `configurar(destino, monto)` | Sí, modifica el estado propio del objeto. |
| `Transaccion` | `ver()` | No. |
| `Transaccion` | `confirmar()` | Sí, modifica saldos y termina el objeto remoto. |
| `Transaccion` | `cancelar()` | Sí, cambia su estado y termina su vida, pero no cambia saldos. |

La transferencia de 500 desde `ana` hacia `beto` se realizó correctamente. Las consultas posteriores confirmaron que los saldos cambiaron de 100.000 a 99.500 y de 20.000 a 20.500, respectivamente. El saldo de `caja` permaneció en cero.

## Paso 3, paso por referencia

Referencia que recibió el cliente al abrir el objeto con estado (`transaccion ana beto 300`)

```
12:20:20 transacciones vivas: 0
12:20:23 recibí Proxy, referencia PYRO:obj_fc307301d9b04867972049b3a72252be@servidor:9100
12:20:23 configurar -> {'origen': 'ana', 'destino': 'beto', 'monto': 300, 'estado': 'pendiente', 'creado': '12:20:23'}
12:20:23 estado remoto -> {'origen': 'ana', 'destino': 'beto', 'monto': 300, 'estado': 'pendiente', 'creado': '12:20:23'}
12:20:23 confirmar -> {'origen': 'ana', 'saldo_origen': 99200, 'destino': 'beto', 'saldo_destino': 20800}
12:20:23 uso la referencia después de finalizar la transacción
12:20:23 REFERENCIA COLGANTE (esperado): DaemonError: unknown object
12:20:27 transacciones vivas: 0
12:20:27 saldos [{'cuenta': 'ana', 'saldo': 99200}, {'cuenta': 'beto', 'saldo': 20800}, {'cuenta': 'caja', 'saldo': 0}]
```

Una vez confirmada la transferencia, el objeto `Transaccion` se desregistró del daemon. Aunque el cliente todavía conservaba la URI, al intentar consultar nuevamente el objeto recibió `DaemonError: unknown object`. Esto demuestra que la referencia quedó colgante y que el ciclo de vida del objeto remoto terminó. Además, `transacciones_vivas()` confirmó que no había transacciones pendientes registradas.

¿Qué pasó con `POR_VALOR=1`? ¿Por qué el cliente rechaza el objeto?

Al configurar `POR_VALOR=1`, `iniciar_transaccion()` devolvió el objeto sin registrarlo en el daemon. En vez de enviar una referencia remota, Pyro5 intentó serializar un objeto de una clase propia que el cliente no podía reconstruir con su configuración actual. La prueba produjo este error:

```
12:22:06 ERROR de serialización. El objeto no está registrado por referencia: unsupported serialized class: objetos.Transaccion
```

¿Qué pasó al usar la referencia después de confirmar?

Luego restauramos `POR_VALOR=0` y recreamos el servidor. Se verificó que no quedaron objetos activos y que los saldos habían regresado a los valores iniciales (100.000 para `ana`, 20.000 para `beto` y 0 para `caja`). Este último resultado evidencia que, al recrear el proceso, los saldos mantenidos en memoria no persistieron.

```
12:22:24 transacciones vivas: 0
12:22:24 saldos [{'cuenta': 'ana', 'saldo': 100000}, {'cuenta': 'beto', 'saldo': 20000}, {'cuenta': 'caja', 'saldo': 0}]
```

## Paso 4, modo de instancia

Se ejecutó `docker compose exec cliente python cliente_pyro.py quien --veces 2` en ambos modos. Para `session` se cambió `MODO=session` y se recreó el servidor.

| Modo | Instancia del proxy A | Instancia del proxy B | ¿Comparten el contador? |
|---|---|---|---|
| `single` | Instancia 1, llamadas 3 y 4 | Instancia 1, llamadas 5 y 6 | Sí. |
| `session` | Instancia 1, llamadas 1 y 2 | Instancia 2, llamadas 1 y 2 | No. |

Salida en single:

```text
12:23:13 proxy A -> {'modo': 'single', 'instancia': 1, 'llamadas': 3, 'cliente': "('172.18.0.3', 37608)"}
12:23:13 proxy A -> {'modo': 'single', 'instancia': 1, 'llamadas': 4, 'cliente': "('172.18.0.3', 37608)"}
12:23:13 proxy B -> {'modo': 'single', 'instancia': 1, 'llamadas': 5, 'cliente': "('172.18.0.3', 37614)"}
12:23:13 proxy B -> {'modo': 'single', 'instancia': 1, 'llamadas': 6, 'cliente': "('172.18.0.3', 37614)"}
```

Salida en session:

```text
12:27:29 proxy A -> {'modo': 'session', 'instancia': 1, 'llamadas': 1, 'cliente': "('172.18.0.3', 34470)"}
12:27:29 proxy A -> {'modo': 'session', 'instancia': 1, 'llamadas': 2, 'cliente': "('172.18.0.3', 34470)"}
12:27:29 proxy B -> {'modo': 'session', 'instancia': 2, 'llamadas': 1, 'cliente': "('172.18.0.3', 34476)"}
12:27:29 proxy B -> {'modo': 'session', 'instancia': 2, 'llamadas': 2, 'cliente': "('172.18.0.3', 34476)"}
```

¿En cuál de los dos modos guardarían estado de un cliente? ¿Por qué los saldos compartidos no cambian entre modos?

Usaríamos `session` para guardar datos propios de cada conexión, ya que cada una tiene una instancia independiente de `Pasarela`. Para una operación que deba mantener su propia identidad, estado y ciclo de vida, utilizamos el objeto remoto `Transaccion`, creado por la fábrica y accesible mediante un proxy.

Porque los saldos viven en el diccionario `cuentas` del módulo `dominio.py`, que comparten las instancias de `Pasarela` dentro del mismo proceso. Los modos `single` y `session` modifican cómo se crean las instancias y sus contadores, pero no separan los datos del dominio. En cambio, **al reiniciar el proceso del servidor sí se reinician los saldos**, pues no están persistidos.

## Paso 5, falla en tres tiempos

| Tiempo | Qué hicimos | Qué vio `vigilar` | Qué vio un cliente nuevo | Qué pasó con el estado |
|---|---|---|---|---|
| 1. Servidor muerto | `docker compose kill servidor` | Detectó `ConnectionClosedError` a las 12:28:51. | No se probó un cliente nuevo mientras el servidor estaba caído. | El servicio dejó de estar disponible. |
| 2. Servidor vuelve | `docker compose start servidor` | Mostró `reconectado` a las 12:28:55 y retomó las consultas a las 12:28:56 sin reiniciar `vigilar`. | `saldo ana` y `saldo beto` funcionaron después del reinicio. | Los saldos regresaron de 99.500 y 20.500 a 100.000 y 20.000: no persistieron las transferencias. |
| 3. Nombres muerto y de vuelta | `kill nombres`, `start nombres` y `restart servidor`. | Continuó consultando mientras ya tenía la conexión establecida. | Con `nombres` caído: `Failed to locate the nameserver`; después de levantarlo: `unknown name`; tras reiniciar `servidor`: `uri`, `listar` y `saldo` funcionaron. | Al reiniciar `nombres` se perdió el registro del servicio; el servidor de pagos permaneció disponible para conexiones previamente establecidas. |

¿Qué nodo es punto único de falla en esta arquitectura? ¿Cómo lo resolverían?

El nodo `servidor` es un punto único de falla porque concentra la ejecución de las operaciones y el estado de los saldos en memoria. `nombres` también representa un punto único de falla para los clientes nuevos que deben descubrir el servicio, aunque los que ya están conectados pueden seguir operando mientras el daemon continúe disponible.

Implementaríamos almacenamiento persistente para los saldos, los identificadores de solicitudes y las transacciones; también incorporaríamos mecanismos de recuperación, servidores redundantes y un servicio de nombres tolerante a fallas. En un sistema de pagos, los reintentos requieren además identificadores únicos y deduplicación para evitar transferencias duplicadas si se pierde la respuesta después de aplicar el cambio. Estas son mejoras propuestas y no características ya implementadas en el prototipo.

¿Qué hace `REREGISTRO=5` y qué costo tiene?

Hace que el servidor intente registrar su URI en `nombres` cada cinco segundos, lo que ayuda a recuperar el descubrimiento del servicio tras reiniciar el servidor de nombres sin reiniciar `servidor`. Su costo es el tráfico de red y las solicitudes periódicas adicionales, incluso cuando no hay fallas. **Esta opción se explica a partir del código, pero no se probó en la terminal.**

### Falla durante una transacción pendiente

```
12:33:57 recibí Proxy, referencia PYRO:obj_ce294756adf04343af00e4af494ec76d@servidor:9100
12:33:57 configurar -> {'origen': 'ana', 'destino': 'beto', 'monto': 300, 'estado': 'pendiente', 'creado': '12:33:57'}
12:33:57 estado remoto -> {'origen': 'ana', 'destino': 'beto', 'monto': 300, 'estado': 'pendiente', 'creado': '12:33:57'}
12:33:57 espero 20 s antes de confirmar (momento para la falla)
12:34:17 se perdió la conexión; reintento con la MISMA URI durante 30 s
12:34:17 ERROR. Referencia colgante: el objeto ya no existe. connection to ('servidor', 9100) rejected: unknown object
```