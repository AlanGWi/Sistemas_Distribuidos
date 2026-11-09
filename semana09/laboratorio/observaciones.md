# Observaciones — Semana 9, serialización explícita

**Equipo:** _(nombre)_  **Integrantes:** _(nombres)_  **Fecha:** 23-10-2026

## Paso 2 — Ida y vuelta de los codecs

Salida de `python codec.py`:

```
json  solicitud  88 bytes  b'{"operacion": "TRANSFERIR", "argumentos": ["ana", "beto", "500"], "id": 7, "version": 2}'
json  respuesta  82 bytes  b'{"id": 7, "estado": "OK", "datos": ["ana", "99500", "beto", "20500"], "error": ""}'
bin   solicitud  34 bytes  b'\x02\x00\x00\x00\x07\x00\nTRANSFERIR\x03\x00\x03ana\x00\x04beto\x00\x03500'
bin   respuesta  33 bytes  b'\x00\x00\x00\x07\x00\x04\x00\x03ana\x00\x0599500\x00\x04beto\x00\x0520500\x00\x00'
ida y vuelta OK en los dos codecs
```

Tamaño de la misma solicitud en JSON 88 bytes y en bin 34 bytes.

## Paso 3 — Medición

Salida de `python bench_codec.py 10000`:

```
| Mensaje   | Codec | Bytes promedio | Bytes totales | Codificar (ms) | Decodificar (ms) |
|-----------|-------|---------------:|--------------:|---------------:|-----------------:|
| Solicitud | json  |           78.8 |        788058 |           45.3 |             24.4 |
| Solicitud | bin   |           24.3 |        243158 |           12.3 |             15.3 |
| Respuesta | json  |           72.4 |        724185 |           45.4 |             23.6 |
| Respuesta | bin   |           23.7 |        237167 |           14.0 |             17.5 |
```

Conclusión en dos líneas (cuánto ahorra el binario, cuál es más rápido, qué sacrificamos a cambio):

En 10 000 mensajes, el binario ahorró un 69 % en solicitudes y un 67 % en respuestas; además, fue más rápido al codificar y decodificar en esta medición.
A cambio, el formato binario es menos legible directamente y requiere conocer el esquema para interpretar los bytes.

## Paso 4 — Integración

| Prueba | codec=json | codec=bin |
|---|---|---|
| `HOLA` | `OK HOLA \| anonimo` | `OK HOLA \| anonimo` |
| `TRANSFERIR ana beto 500` | `OK ana \| 99500 \| beto \| 20500` | `OK ana \| 99500 \| beto \| 20500` |
| `TOTAL` | `OK TOTAL \| 120000` | `OK TOTAL \| 120000` |
| Error del dominio (`RETIRAR ana 999999`) | `ERROR SALDO_INSUFICIENTE 100000` | `ERROR SALDO_INSUFICIENTE 99500` |

## Paso 5 — Falla provocada

| Modo de `cliente_malo.py` | Qué vio el cliente | Qué dice el log del servidor | ¿El servidor siguió atendiendo? |
|---|---|---|---|
| `version` | `ERROR: versión 1 no soportada, use 2` en ambos codecs | Registra versión no soportada y desconexión del cliente | Sí |
| `largo` | Sin respuesta en 5 segundos (timeout) | Registra conexión y desconexión sin procesar ninguna solicitud | Sí |
| `basura` (codec json) | `ERROR: mensaje mal formado (UnicodeDecodeError)` | Registra `UnicodeDecodeError` por bytes UTF-8 inválidos | Sí |
| `basura` (codec bin) | `ERROR: mensaje mal formado (UnicodeDecodeError)` | Registra `UnicodeDecodeError` al interpretar bytes aleatorios | Sí |
| `cruzado` | JSON: `JSONDecodeError`. Binario: `struct.error` | Registra `JSONDecodeError` o `struct.error` según el codec | Sí |

¿Cuál de los dos codecs falló de forma más clara ante la basura y por qué?

En nuestras pruebas, ambos codecs detectaron los datos corruptos mediante UnicodeDecodeError. Los dos devolvieron un error controlado y el servidor continuó funcionando. Por tanto, en esta ejecución ninguno mostró una ventaja clara para detectar la basura.


¿Cuál de los dos codecs falló de forma más clara ante la basura y por qué?

En esta ejecución, ambos codecs rechazaron los bytes aleatorios con `UnicodeDecodeError`. Los dos devolvieron `ERROR mensaje mal formado` y el servidor continuó atendiendo.

## Para la semana autónoma

Una pregunta que nos quedó sobre serialización o protocolos:

_(escribir)_
