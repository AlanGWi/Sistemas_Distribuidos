# Observaciones — fallas provocadas · semana 4 · Equipo Diego Leiva --- Alan Gimilio

Anoten lo que vieron, no lo que esperaban ver. Un tiempo sin unidad no sirve.

## Falla 1 — servidor muerto con el cliente conectado

Comando usado: `docker compose kill servidor`

| Pregunta | Respuesta |
|---|---|
| ¿Qué mensaje mostró el cliente? | `CONEXIÓN PERDIDA: ConnectionError: el servidor cerró la conexión sin responder` |
| ¿Cuánto tardó en aparecer desde que enviaron el comando? (ms o s) | Prácticamente al instante (<1 s) — recién al intentar enviar el siguiente comando (`ECO prueba`) tras el kill |
| ¿El cliente supo que el servidor estaba muerto o solo que la conexión se cerró? | Solo que la conexión se cerró sin responder. No distingue si el servidor murió, se colgó, o cerró el socket a propósito |
| Al levantar el servidor de nuevo, ¿se recuperó la sesión anterior (nombre, contador)? | No — al reconectar, el servidor trata la conexión como nueva, sin memoria del nombre ni del contador previos |

## Falla 2 — cliente sin red con el servidor vivo

Comando usado: `docker network disconnect sd_net cliente`

| Pregunta | Respuesta |
|---|---|
| ¿Qué mensaje mostró el cliente? | `TIMEOUT: el servidor no respondió en 5 s. ¿Caído, sin red o lento? No se puede saber.` |
| ¿Cuánto tardó en aparecer? | 5 segundos (el timeout configurado del cliente) |
| ¿Qué mostró el log del servidor en ese momento? | No se ve nada solo muestra conexion del cliente servidor  | [18:38:58] conexión desde 172.18.0.3:60802 |
| Desde el punto de vista del cliente, ¿en qué se diferencia esta falla de la falla 1? | En la Falla 1 el cliente se enteró casi al instante con un error de conexión claro (el servidor cerró el socket). Acá el cliente no recibe ninguna señal de que algo falló  el socket sigue "abierto" para él, así que solo puede esperar su propio timeout y no puede distinguir si el servidor está caído, lento, o si es él mismo quien perdió la red |

## Segundo cliente mientras el primero está conectado (paso 3)


## Segundo cliente mientras el primero está conectado (paso 3)

| Pregunta | Respuesta |
|---|---|
| ¿El segundo cliente logró conectarse (`connect`)? | Sí, el TCP connect/accept se completó de inmediato |
| ¿Recibió respuesta a su primer comando? ¿Qué mostró? | No — al mandar `HOLA` quedó esperando y cayó en `TIMEOUT: el servidor no respondió en 5 s` porque el servidor seguía ocupado con el primer cliente |
| ¿Qué mostró el log del servidor cuando el primer cliente hizo `SALIR`? | montro el cierra del cliente 1 y muestro que el cliente 2 hizo conexion |

## Conclusión del equipo (3 a 5 líneas)

¿Qué falacia de la semana 2 asumiría un programador que solo probara el camino feliz de este sistema? ¿Por qué el cliente no puede distinguir entre servidor caído, servidor ocupado y red cortada?
 Asumiría la falacia de que "la red es confiable" que si el cliente envía algo, el servidor lo recibe y responde, y que cualquier falla se anuncia de inmediato con un error claro. Las pruebas muestran que eso es falso: cuando el servidor muere abruptamente el cliente al menos recibe un cierre de conexión reconocible, pero cuando es la red la que se corta, el cliente no recibe ninguna señal  el socket sigue "vivo" desde su punto de vista y solo puede esperar un timeout. Por eso el cliente nunca puede distinguir con certeza entre servidor caído, servidor ocupado (atendiendo a otro cliente) y red cortada: en los tres casos el síntoma que observa es el mismo, silencio, y solo la duda cambia según si hubo o no un cierre explícito del socket.
