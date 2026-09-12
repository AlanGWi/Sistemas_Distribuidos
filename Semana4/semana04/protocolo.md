# Protocolo de aplicación — Equipo ______

Versión 0.1 · semana 4 · Este archivo evoluciona cada semana junto con el servicio.

## 1. Transporte

- Protocolo de transporte: TCP
- Puerto del servidor: 5000
- Codificación: UTF-8
- Delimitador de mensaje: una línea terminada en `\n`
- Quién inicia: el cliente. El servidor solo responde.

## 2. Mensajes

Completen la tabla. Una fila por comando. La operación propia del equipo va al final.



| Comando (cliente → servidor) | Argumentos | Respuesta (servidor → cliente) | ¿Cambia el estado de la conexión? |
|---|---|---|---|
| `HOLA <nombre>` | nombre, texto libre | `OK hola <nombre>` | Sí, guarda el nombre |
| `ECO <texto>` | texto libre | repite el mismo texto recibido | No |
| `CONTAR` | — | `OK <n>` (cantidad de mensajes recibidos en la sesión) | Sí, incrementa el contador |
| `SALIR` | — | `ADIOS` (y luego cierra la conexión) | Sí, termina la sesión |
| (cualquier otro) | — | `ERROR comando desconocido` | No |
| | `SUMA <a> <b>` | dos números (enteros o decimales) | `OK <resultado>` si son válidos, `ERROR argumentos invalidos` | si no se reinicia el contenedor docker aunque se haya guardado el codigo da el  `TIME OUT`|


escriban comandos (HOLA, ECO, CONTAR, SUMA 3 4, SALIR). Ctrl+C para cortar de golpe.
> SUMA 3 4
  > SUMA 3 4
  < OK 7   (0.8 ms)
> SUMA HOLA 4
  > SUMA HOLA 4
  < ERROR argumentos invalidos   (0.5 ms)
> 


## 3. Estado


- ¿Qué recuerda el servidor de cada conexión? Un diccionario `estado` local a esa conexión, con dos campos: `nombre` (el que se envió con `HOLA`) 

- ¿Qué pasa con ese estado cuando el cliente se desconecta? Se pierde por completo. El diccionario `estado` se crea de nuevo en cada llamada a , así que no hay memoria entre conexiones cada cliente nuevO, sin importar qué haya pasado en sesiones anteriores.

- Si el servidor se reinicia mientras un cliente está conectado, ¿qué pierde el cliente? Pierde toda la sesión: el nombre registrado con `HOLA` y el contador de mensajes, además de la conexión TCP misma (que se cierra abruptamente, sin un `ADIOS` de por medio). Al reconectar, debe empezar desde cero.


## 4. Secuencia típica

Dibujen o describan una sesión completa, desde `connect` hasta `ADIOS`.

```
cliente                servidor
   |---- connect --------->|
   |---- HOLA equipo ----->|
   |<--- OK hola equipo ---|
   |         ...           |
   |---- SALIR ----------->|
   |<--- ADIOS ------------|
   |         (cierre)      |
```

> HOLA
  > HOLA
  < OK hola anónimo   (0.9 ms)
> ECO hola mundo
  > ECO hola mundo
  < ECO hola mundo   (0.3 ms)
> CONTAR
  > CONTAR
  < OK 3   (0.3 ms)
> SALIR
  > SALIR
  < ADIOS   (0.6 ms)

## 5. Errores

| Situación | Qué ve el cliente | Qué ve el servidor |
|---|---|---|
| Comando desconocido | `ERROR comando desconocido` | log con el comando |
| Servidor caído durante la sesión | | |
| Cliente sin red durante la sesión | | |
| Cliente corta sin `SALIR` (Ctrl+C) | | |


## 5. Errores

| Situación | Qué ve el cliente | Qué ve el servidor |
|---|---|---|
| Comando desconocido | `ERROR comando desconocido` | log con el comando |
| Servidor caído durante la sesión | `CONEXIÓN PERDIDA: ConnectionError: el servidor cerró la conexión sin responder` (casi al instante, al intentar el siguiente comando) | Nada el proceso murió (kill), no alcanza a loguear el cierre |
| Cliente sin red durante la sesión | `TIMEOUT: el servidor no respondió en 5 s. ¿Caído, sin red o lento? No se puede saber.` (tras 5 s, el timeout configurado) | Nada el servidor sigue esperando sin ninguna señal de que la red se cortó; no aparece ni error ni desconexión en el log |
| Cliente corta sin `SALIR` (Ctrl+C) | `corte abrupto desde el cliente (sin SALIR)`, seguido del log de cierre con la cantidad de mensajes recibidos |
