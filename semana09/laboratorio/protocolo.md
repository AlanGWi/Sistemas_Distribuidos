# Protocolo del servicio — versión 3 (Semana 9)

## 1. Identificación

| Campo | Valor |
|---|---|
| Equipo | _(nombre del equipo)_ |
| Dominio | Pagos electrónicos |
| Versión del protocolo | 2 (campo `version` del mensaje) |
| Versión del documento | 3 |
| Transporte | TCP, puerto 5000 dentro de `sd_net` |

## 2. Formato del mensaje

Cada mensaje viaja **enmarcado**: 4 bytes con el largo (entero sin signo, big-endian) seguidos del cuerpo.

```
+------------+------------------------+
| largo (4B) | cuerpo (largo bytes)   |
+------------+------------------------+
```

El cuerpo se codifica con uno de dos **codecs**, elegido por la variable `CODEC`. Cliente y servidor deben usar el mismo.

### 2.1 Solicitud (cliente → servidor)

| Campo | Tipo | Descripción |
|---|---|---|
| `version` | entero | Versión del protocolo. El servidor rechaza las distintas de 2 |
| `id` | entero | Correlativo del cliente. La respuesta trae el mismo id |
| `operacion` | texto | Nombre de la operación en mayúsculas |
| `argumentos` | lista de textos | Argumentos de la operación, puede ser vacía |

### 2.2 Respuesta (servidor → cliente)

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | entero | Mismo id de la solicitud (0 si no se pudo leer la solicitud) |
| `estado` | `OK` o `ERROR` | Resultado |
| `datos` | lista de textos | Resultado cuando estado es OK |
| `error` | texto | Mensaje legible cuando estado es ERROR |

### 2.3 Codec `json`

Cuerpo en JSON UTF-8 con los campos anteriores como claves.

```json
{"operacion": "TRANSFERIR", "argumentos": ["ana", "beto", "500"], "id": 7, "version": 2}
```


### 2.4 Codec `bin`

Cuerpo binario con `struct`, big-endian. Los textos van con largo prefijado de 2 bytes y las listas con cantidad prefijada de 1 byte.

```
Solicitud: version(1B) id(4B) operacion(2B+texto) n_args(1B) [arg(2B+texto)]*
Respuesta: id(4B) estado(1B: 0=OK 1=ERROR) n_datos(1B) [dato(2B+texto)]* error(2B+texto)
```

## 3. Operaciones

| Operación | Argumentos | Respuesta OK (`datos`) | Errores posibles |
|---|---|---|---|
| `HOLA` | nombre (opcional) | `["HOLA", nombre]` | — |
| `SALDO` | cuenta | `[cuenta, saldo]` | `CUENTA_NO_EXISTE`, formato incorrecto |
| `DEPOSITAR` | cuenta, monto | `[cuenta, saldo_nuevo]` | `CUENTA_NO_EXISTE`, `MONTO_INVALIDO`, formato incorrecto |
| `RETIRAR` | cuenta, monto | `[cuenta, saldo_nuevo]` | `CUENTA_NO_EXISTE`, `MONTO_INVALIDO`, `SALDO_INSUFICIENTE`, formato incorrecto |
| `TRANSFERIR` | origen, destino, monto | `[origen, saldo_origen, destino, saldo_destino]` | `CUENTA_NO_EXISTE`, `MONTO_INVALIDO`, `SALDO_INSUFICIENTE`, `MISMA_CUENTA`, formato incorrecto |
| `TOTAL` | — | `["TOTAL", total]` | — |
| `ESPERA` | segundos | `["ESPERA", segundos]` | formato incorrecto |
| `SALIR` | — | `["CHAO"]` | — |

Ejemplo de solicitud estructurada:

```json
{"operacion": "TRANSFERIR", "argumentos": ["ana", "beto", "500"], "id": 7, "version": 2}
```


## 4. Errores de protocolo

| Situación | Reacción del servidor |
|---|---|
| `version` distinta de 2 | Responde `ERROR` con el texto `versión X no soportada, use 2` y mantiene la conexión |
| Cuerpo que no se puede decodificar | Responde `ERROR mensaje mal formado (...)` con id 0 y **cierra esa conexión** |
| Largo anunciado mayor a 1 MB | Responde `ERROR` y cierra esa conexión |
| Largo anunciado mayor a lo enviado | Espera hasta `TIMEOUT_SERVIDOR` (30 s) y cierra esa conexión |
| Operación desconocida | Responde `ERROR operación desconocida` |


## 5. Concurrencia

El servidor utiliza un modelo de concurrencia de hilo por cliente. Cada conexión TCP es atendida por un hilo independiente, permitiendo procesar varias solicitudes de distintos clientes al mismo tiempo.

El estado compartido contiene los saldos de las cuentas, el historial de movimientos y el contador de operaciones. Para evitar condiciones de carrera se utiliza `threading.Lock()`, que protege las secciones críticas durante las operaciones bancarias.

Las operaciones `DEPOSITAR`, `RETIRAR` y `TRANSFERIR` modifican los saldos dentro de la sección crítica, evitando que dos hilos actualicen simultáneamente los mismos datos. Las consultas de saldo y total también acceden al estado protegido.

El servidor dispone de la variable `SIN_LOCK`, que permite desactivar la exclusión mutua para realizar pruebas de concurrencia. Por defecto, el sistema utiliza el Lock para mantener la consistencia de las cuentas.



## 6. Ejemplo de sesión

```text
> HOLA                       -> OK HOLA | anonimo
> SALDO ana                  -> OK ana | 100000
> TRANSFERIR ana beto 500    -> OK ana | 99500 | beto | 20500
> SALDO ana                  -> OK ana | 99500
> TOTAL                      -> OK TOTAL | 120000
> RETIRAR ana 999999         -> ERROR SALDO_INSUFICIENTE 99500
```

El ejemplo muestra una transferencia de 500 desde la cuenta de Ana hacia Beto. El saldo de Ana disminuye de 100000 a 99500 y el de Beto aumenta de 20000 a 20500, manteniendo el total de 120000. También se observa el rechazo de un retiro cuando el saldo es insuficiente.


## 7. Medición de codecs

| Mensaje   | Codec | Bytes promedio | Bytes totales | Codificar (ms) | Decodificar (ms) |
|-----------|-------|---------------:|--------------:|---------------:|-----------------:|
| Solicitud | json  |           78.8 |        788058 |           44.4 |             25.3 |
| Solicitud | bin   |           24.3 |        243158 |           11.4 |             15.6 |
| Respuesta | json  |           72.4 |        724185 |           46.0 |             23.7 |
| Respuesta | bin   |           23.7 |        237167 |           13.2 |             16.9 |

## 8. Historial de cambios

| Versión doc | Fecha | Cambio |
|---|---|---|
| 1 | sem. 4 | Protocolo de texto por líneas |
| 2 | sem. 6 | Concurrencia, errores, operaciones del dominio |
| 3 | sem. 9 | Mensaje estructurado, enmarcado por largo, codecs json y bin, versión en el mensaje |
