# Protocolo de aplicación — webpay

> Servicio de saldos y transferencias (núcleo de cuentas de una billetera digital, tema Webpay).

## 1. Identificación

| Campo | Valor |
|---|---|
| Equipo | (nombre del equipo) |
| Dominio del servicio | Pagos: saldos y transferencias entre cuentas |
| Versión del protocolo | 2.0 |
| Transporte | TCP, puerto 5000 |
| Codificación | UTF-8, un mensaje por línea, terminador `\n` |
| Modelo de concurrencia del servidor | hilo por cliente |
| Timeout de inactividad | 60 s (el servidor cierra la conexión) |

## 2. Formato general

- Petición: `COMANDO [argumentos separados por espacio]\n`
- Respuesta correcta: `OK [datos]\n`
- Respuesta de error: `ERROR CODIGO [detalle]\n`
- El servidor responde exactamente UNA línea por cada línea recibida.
- Los comandos no distinguen mayúsculas (`saldo` = `SALDO`).
- Los nombres de cuenta tampoco distinguen mayúsculas: el servidor los convierte a minúsculas y responde siempre en minúsculas (`SALDO ANA` → `OK ana 100000`).
- Los montos son **enteros positivos en pesos**, solo dígitos del 0 al 9: sin signo, sin decimales, sin separador de miles, sin símbolo de moneda. `0` es inválido.
- Los argumentos se separan por uno o más espacios.


Cómo agregar nuevas cuentas: el protocolo no tiene un comando para crearlas. Para agregar usuarios hay que editar el diccionario estado al inicio de servidor.py y reconstruir el servidor:

python
estado = {
    "cuentas": {"ana": 100000, "beto": 20000, "caja": 0, "carla": 50000},
    "movimientos": [],
    "operaciones": 0,
}

Cada cuenta nueva se agrega como "nombre": saldo_inicial dentro de cuentas (nombre en minúsculas, saldo entero en pesos).

## 3. Secuencia de una sesión

-se dejo el fomato anterior solo se agregaron los comandos para webpay

```
cliente                          servidor
   |--- HOLA <nombre> ------------->|
   |<-- OK HOLA <nombre> -----------|
   |--- <operaciones...> ---------->|
   |<-- OK ... / ERROR ... ---------|
   |--- SALIR --------------------->|
   |<-- OK CHAO --------------------|   (el servidor cierra)
```

**¿Es obligatorio HOLA antes de operar?** No. El servidor atiende cualquier operación sin saludo previo. `HOLA` sin nombre responde `OK HOLA anonimo`. El nombre del saludo es solo informativo: no autentica ni se asocia a una cuenta.

## 4. Operaciones

| Comando | Argumentos | Respuesta OK | Errores posibles | ¿Modifica estado compartido? |
|---|---|---|---|---|
| HOLA | nombre (opcional) | `OK HOLA nombre` | — | no |
| SALDO | cuenta | `OK ana 100000` (cuenta, saldo) | `ERROR FORMATO SALDO <cuenta>`, `ERROR CUENTA_NO_EXISTE` | no |
| DEPOSITAR | cuenta monto | `OK ana 110000` (cuenta, nuevo saldo) | `ERROR FORMATO DEPOSITAR <cuenta> <monto>`, `ERROR MONTO_INVALIDO`, `ERROR CUENTA_NO_EXISTE` | sí |
| RETIRAR | cuenta monto | `OK ana 90000` (cuenta, nuevo saldo) | `ERROR FORMATO RETIRAR <cuenta> <monto>`, `ERROR MONTO_INVALIDO`, `ERROR CUENTA_NO_EXISTE`, `ERROR SALDO_INSUFICIENTE actual` | sí |
| TRANSFERIR | origen destino monto | `OK ana 90000 beto 30000` (origen, nuevo saldo, destino, nuevo saldo) | `ERROR FORMATO TRANSFERIR <origen> <destino> <monto>`, `ERROR MONTO_INVALIDO`, `ERROR MISMA_CUENTA`, `ERROR CUENTA_NO_EXISTE`, `ERROR SALDO_INSUFICIENTE actual` | sí (dos cuentas) |
| TOTAL | — | `OK TOTAL 120000` (suma de todos los saldos) | — | no |
| ESPERA | segundos | `OK ESPERA seg` | `ERROR FORMATO ESPERA <segundos>` | no |
| SALIR | — | `OK CHAO` | — | no |

Notas por operación:

- `RETIRAR` y `DEPOSITAR` modifican el total del sistema (el dinero sale hacia, o entra desde, un origen externo que no es una cuenta). `TRANSFERIR` **conserva** la suma de los saldos.
- `SALDO_INSUFICIENTE` incluye el saldo actual de la cuenta de origen: `ERROR SALDO_INSUFICIENTE 20000`.
- En `TRANSFERIR`, el descuento al origen y la suma al destino ocurren de forma atómica: ningún otro cliente puede observar un estado intermedio.
- `ESPERA` es una operación lenta de prueba (simula una validación); no toca ningún saldo. Devuelve el argumento tal como fue enviado.
- Orden en que se validan los errores: `FORMATO` → `MONTO_INVALIDO` → `MISMA_CUENTA` (solo TRANSFERIR) → `CUENTA_NO_EXISTE` → `SALDO_INSUFICIENTE`.

Ejemplos:

```
SALDO ana              -> OK ana 100000
DEPOSITAR beto 5000    -> OK beto 25000
RETIRAR ana 1000       -> OK ana 99000
RETIRAR ana 999999     -> ERROR SALDO_INSUFICIENTE 99000
TRANSFERIR ana beto 5000 -> OK ana 94000 beto 30000
TRANSFERIR ana ana 100 -> ERROR MISMA_CUENTA
TRANSFERIR ana zoe 100 -> ERROR CUENTA_NO_EXISTE
RETIRAR ana -5         -> ERROR MONTO_INVALIDO
RETIRAR ana            -> ERROR FORMATO RETIRAR <cuenta> <monto>
TOTAL                  -> OK TOTAL 120000
```

## 5. Códigos de error

| Código | Cuándo se produce |
|---|---|
| COMANDO_DESCONOCIDO | el comando no está en la tabla, o la línea está vacía |
| FORMATO | faltan o sobran argumentos (el detalle indica el uso correcto) |
| MONTO_INVALIDO | el monto no es un entero positivo (letras, decimales, signo, cero) |
| CUENTA_NO_EXISTE | la cuenta indicada (o el origen o el destino) no existe |
| MISMA_CUENTA | `TRANSFERIR` con origen igual a destino |
| SALDO_INSUFICIENTE | el saldo de la cuenta es menor que el monto; el detalle trae el saldo actual |

## 6. Comportamiento ante situaciones anómalas

| Situación | Qué hace el servidor |
|---|---|
| Línea vacía | responde `ERROR COMANDO_DESCONOCIDO` |
| Cliente inactivo 60 s | cierra la conexión sin mensaje |
| Cliente se desconecta a mitad de una operación | registra la desconexión y sigue atendiendo a los demás; una operación que ya entró a su sección crítica se completa entera (nunca queda una transferencia a medias) |
| Dos clientes modifican la misma cuenta a la vez | las operaciones se serializan con un Lock; el resultado es el mismo que si hubieran llegado una tras otra |
| Dos transferencias cruzadas simultáneas (ana→beto y beto→ana) | se serializan con el mismo Lock; no hay interbloqueo |
| Bytes no decodificables en UTF-8 | el servidor los reemplaza por el carácter `�` y sigue; normalmente resulta en `ERROR COMANDO_DESCONOCIDO` o `ERROR CUENTA_NO_EXISTE` |
| Comando válido pero con argumento no interpretable en `ESPERA` | responde `ERROR FORMATO ESPERA <segundos>` |

## 7. Estado compartido

| Dato | Tipo | Valor inicial | Quién lo modifica |
|---|---|---|---|
| cuentas | dict cuenta → saldo (entero, pesos) | ana 100000, beto 20000, caja 0 | DEPOSITAR, RETIRAR, TRANSFERIR |
| movimientos | lista de tuplas (origen, destino, monto), en orden | vacía | DEPOSITAR, RETIRAR, TRANSFERIR |
| operaciones | int | 0 | todo comando del dominio (SALDO, DEPOSITAR, RETIRAR, TRANSFERIR, TOTAL, ESPERA) |

Invariante: tras cualquier secuencia de `TRANSFERIR`, `TOTAL` no cambia (inicialmente 120000). `DEPOSITAR` y `RETIRAR` lo aumentan o disminuyen exactamente en el monto. Las cuentas no se pueden crear ni borrar por el protocolo; el servidor arranca siempre con las tres cuentas indicadas.

Los movimientos de `DEPOSITAR` y `RETIRAR` se registran con el origen/destino `externo`.

## 8. Historial de cambios

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0 | semana 4 | protocolo inicial, servidor secuencial |
| 2.0 | semana 6 | servidor concurrente de pagos, estado compartido (cuentas, movimientos), errores y timeout documentados |