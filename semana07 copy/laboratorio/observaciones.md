# Observaciones de la Semana 7

Equipo
Integrantes
Dominio del servicio

## Paso 1  diagrama de despliegue v1 (el sistema de la semana 6)

Archivo entregado en `diagramas/`
Cantidad de nodos, redes y puertos representados

## Paso 2  revisión por pares

Equipo que revisó nuestro diagrama
Ítems de la pauta marcados como NO (copiar el número y el comentario)
Qué vamos a corregir primero y por qué

Equipo cuyo diagrama revisamos
Los dos hallazgos más importantes que les dejamos

## Paso 3  una operación como servicio REST

Operación del protocolo de texto elegida
Método y ruta HTTP
Salida de la prueba contra api1 (copiar la línea completa)
Salida de un caso de error y su código HTTP

## Paso 4  dos réplicas detrás de Nginx

Salida de `cliente_http.py --repetir 4` (copiar las cuatro líneas)
¿Qué réplica atendió cada petición?
¿El dato es el mismo sin importar la réplica? ¿Por qué?

## Paso 5  falla provocada en dos tiempos

### Tiempo 1, cae una réplica de la API
Predicción escrita ANTES de ejecutar
Comando usado
Qué respondió el sistema (copiar las líneas)
¿Cuánto tardó la primera petición después de la caída?

### Tiempo 2, cae el servidor TCP
Predicción escrita ANTES de ejecutar
Comando usado
Qué respondió el sistema y con qué código HTTP
¿Qué se perdió al volver a levantar el servidor?

### Conclusión en tres líneas
¿Qué nivel se pudo replicar sin problemas y cuál no? ¿Por qué?







# Observaciones de la Semana 7

**Equipo:** (nombre del equipo)
**Integrantes:** (nombres)
**Dominio del servicio:** Pagos, saldos y transferencias entre cuentas (billetera digital, tema Webpay). Estado compartido: `cuentas` (ana, beto, caja, carla) y `movimientos`.

## Paso 1: diagrama de despliegue v1 (el sistema de la semana 6)

**Archivo entregado en `diagramas/`:** (nombre del archivo)

**Cantidad de nodos, redes y puertos representados:**
- Nodos: (ej. contenedores `servidor`, `cliente`, `carga`)
- Redes: (ej. `sd_net`)
- Puertos: (ej. 5000 publicado en el host)

## Paso 2: revisión por pares

**Equipo que revisó nuestro diagrama:** (nombre)

**Ítems de la pauta marcados como NO (número y comentario):**
- (ítem N: comentario)

**Qué vamos a corregir primero y por qué:** (respuesta)

**Equipo cuyo diagrama revisamos:** (nombre)

**Los dos hallazgos más importantes que les dejamos:**
1. (hallazgo)
2. (hallazgo)

## Paso 3: una operación como servicio REST

**Operación del protocolo de texto elegida:** `SALDO <cuenta>` (propuesta; es la que el enunciado del tema sugiere para la semana 7)

**Método y ruta HTTP:** (propuesta: `GET /cuentas/{cuenta}/saldo`)

**Salida de la prueba contra api1 (línea completa):**
```
(pegar aquí)
```

**Salida de un caso de error y su código HTTP:**
```
(pegar aquí; ej. cuenta inexistente)
```

Correspondencia usada entre errores del protocolo y códigos HTTP (completar o ajustar):

| Error del protocolo TCP | Código HTTP |
|---|---|
| `CUENTA_NO_EXISTE` | (propuesta: 404) |
| `FORMATO` / `MONTO_INVALIDO` / `MISMA_CUENTA` | (propuesta: 400) |
| `SALDO_INSUFICIENTE` | (propuesta: 409 o 422) |

## Paso 4: dos réplicas detrás de Nginx

**Salida de `cliente_http.py --repetir 4` (las cuatro líneas):**
```
(pegar aquí)
```

**¿Qué réplica atendió cada petición?** (api1 / api2, en qué orden)

**¿El dato es el mismo sin importar la réplica? ¿Por qué?**
(Pista para responder: ¿las réplicas de la API guardan los saldos ellas mismas, o consultan al mismo servidor TCP? Eso decide si `SALDO ana` puede dar valores distintos.)

## Paso 5: falla provocada en dos tiempos

### Tiempo 1, cae una réplica de la API

**Predicción escrita ANTES de ejecutar:** (escribirla antes de correr el comando)

**Comando usado:**
```
(comando)
```

**Qué respondió el sistema (líneas):**
```
(pegar aquí)
```

**¿Cuánto tardó la primera petición después de la caída?** (segundos)

### Tiempo 2, cae el servidor TCP

**Predicción escrita ANTES de ejecutar:** (escribirla antes de correr el comando)

**Comando usado:**
```
(comando)
```

**Qué respondió el sistema y con qué código HTTP:**
```
(pegar aquí)
```

**¿Qué se perdió al volver a levantar el servidor?**
(Pista: el estado vive en memoria. Compara `SALDO` y `TOTAL` antes de la caída y después del reinicio, y revisa si `movimientos` sigue igual.)

### Conclusión en tres líneas

**¿Qué nivel se pudo replicar sin problemas y cuál no? ¿Por qué?**
1. (la capa de API)
2. (la capa del servidor TCP con estado)
3. (por qué)
