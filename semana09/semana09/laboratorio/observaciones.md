# Observaciones — Semana 9, serialización explícita

**Equipo:** _(nombre)_  **Integrantes:** _(nombres)_  **Fecha:** 23-10-2026

## Paso 2 — Ida y vuelta de los codecs

Salida de `python codec.py`:

```
(pegar aquí)
```

PS D:\SistemasDistribuidos\Sistemas_Distribuidos\semana09\semana09\laboratorio> python codec.py  
json  solicitud  81 bytes  b'{"operacion": "AGREGAR", "argumentos": ["tornillo", "25"], "id": 7, "version": 2}'
json  respuesta  64 bytes  b'{"id": 7, "estado": "OK", "datos": ["tornillo=25"], "error": ""}'
bin   solicitud  29 bytes  b'\x02\x00\x00\x00\x07\x00\x07AGREGAR\x02\x00\x08tornillo\x00\x0225'
bin   respuesta  21 bytes  b'\x00\x00\x00\x07\x00\x01\x00\x0btornillo=25\x00\x00'
ida y vuelta OK en los dos codecs

Tamaño de la misma solicitud en JSON ____ bytes y en bin ____ bytes.

## Paso 3 — Medición

Salida de `python bench_codec.py 10000`:

```
(pegar aquí la tabla)
```


PS D:\SistemasDistribuidos\Sistemas_Distribuidos\semana09\semana09\laboratorio> python bench_codec.py 10000
N = 10000 solicitudes y 10000 respuestas del dominio

| Mensaje   | Codec | Bytes promedio | Bytes totales | Codificar (ms) | Decodificar (ms) |
|-----------|-------|---------------:|--------------:|---------------:|-----------------:|
| Solicitud | json  |           79.8 |        797892 |           52.3 |             26.3 |
| Solicitud | bin   |           25.9 |        259140 |           12.8 |             16.4 |
| Respuesta | json  |          109.0 |       1089544 |           63.2 |             27.2 |
| Respuesta | bin   |           57.1 |        570654 |           21.0 |             23.6 |

Solicitud: el binario ocupa 68% menos bytes que JSON (JSON 80 B vs bin 26 B por mensaje)
Respuesta: el binario ocupa 48% menos bytes que JSON (JSON 109 B vs bin 57 B por mensaje)

Ejemplo de una misma solicitud en cada codec
  json   80 B  b'{"operacion": "QUITAR", "argumentos": ["remache", "137"], "id": 0, "version": 2}'
  bin    28 B  b'\x02\x00\x00\x00\x00\x00\x06QUITAR\x02\x00\x07remache\x00\x03137'
Conclusión en dos líneas (cuánto ahorra el binario, cuál es más rápido, qué sacrificamos a cambio):

_(escribir)_

## Paso 4 — Integración

| Prueba | codec=json | codec=bin |
|---|---|---|
| `HOLA` | | |
| `AGREGAR ...` (del dominio) | | |
| `LISTAR` | | |
| Error del dominio (por ejemplo stock insuficiente) | | |

## Paso 5 — Falla provocada

| Modo de `cliente_malo.py` | Qué vio el cliente | Qué dice el log del servidor | ¿El servidor siguió atendiendo? |
|---|---|---|---|
| `version` | | | |
| `largo` | | | |
| `basura` (codec json) | | | |
| `basura` (codec bin) | | | |
| `cruzado` | | | |

¿Cuál de los dos codecs falló de forma más clara ante la basura y por qué?

_(escribir)_

## Para la semana autónoma

Una pregunta que nos quedó sobre serialización o protocolos:

_(escribir)_
