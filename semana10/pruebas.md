# Pruebas — Semana 10, JSON-RPC 2.0

**Servicio:** Pagos electrónicos (`saldo` y `transferir`)  
**Fecha de ejecución:** 07-11-2026  
**Herramientas:** PowerShell, `curl.exe`, Uvicorn y FastAPI  
**Endpoint:** `POST http://127.0.0.1:8001/rpc`

## Preparación

Servidor ejecutado desde `semana10/`:

```powershell
python -m uvicorn rpc:app --host 127.0.0.1 --port 8001
```

Función utilizada para las pruebas:

```powershell
function Probar-RPC {
    param(
        [string]$Caso,
        [string]$Json
    )

    Write-Host "`n========== $Caso =========="
    Write-Host "Solicitud: $Json"

    $Json | curl.exe -i -sS --max-time 10 `
        -X POST http://127.0.0.1:8001/rpc `
        -H "Content-Type: application/json" `
        --data-binary '@-'
}
```

Todas las respuestas que siguen se copiaron de la salida real de terminal del 07-11-2026. Se omiten las cabeceras repetidas de fecha, servidor y longitud para mantener el registro legible.

## 1. Operación `saldo` válida — parámetros como objeto

```powershell
Probar-RPC "01 - SALDO correcto" '{"jsonrpc":"2.0","method":"saldo","params":{"cuenta":"ana"},"id":1}'
```

**HTTP:** `200 OK`

```json
{"jsonrpc":"2.0","result":{"cuenta":"ana","saldo":99500},"id":1}
```

**Resultado:** Correcto. La consulta devolvió un `result` con el mismo identificador. El saldo ya era `99500` al iniciar esta secuencia de pruebas; el registro no establece qué operación anterior lo modificó.

## 2. Operación `transferir` válida — parámetros como lista

```powershell
Probar-RPC "02 - TRANSFERIR correcto" '{"jsonrpc":"2.0","method":"transferir","params":["ana","beto",500],"id":2}'
```

**HTTP:** `200 OK`

```json
{"jsonrpc":"2.0","result":{"origen":"ana","saldo_origen":99000,"destino":"beto","saldo_destino":21000},"id":2}
```

**Resultado:** Correcto. Descontó `500` a `ana` y los agregó a `beto`.

## 3. Error del dominio — saldo insuficiente

```powershell
Probar-RPC "03 - SALDO_INSUFICIENTE" '{"jsonrpc":"2.0","method":"transferir","params":{"origen":"ana","destino":"beto","monto":999999},"id":3}'
```

**HTTP:** `200 OK`

```json
{"jsonrpc":"2.0","error":{"code":-32000,"message":"Error del dominio","data":"SALDO_INSUFICIENTE: 99000"},"id":3}
```

**Resultado:** Correcto. El código JSON-RPC `-32000` incluye la causa en `data`.

## 4. Método inexistente

```powershell
Probar-RPC "04 - Metodo inexistente" '{"jsonrpc":"2.0","method":"no_existe","id":4}'
```

**HTTP:** `200 OK`

```json
{"jsonrpc":"2.0","error":{"code":-32601,"message":"Method not found"},"id":4}
```

**Resultado:** Correcto. Respondió con `-32601`.

## 5. Parámetros incompletos

```powershell
Probar-RPC "05 - Parametros incompletos" '{"jsonrpc":"2.0","method":"transferir","params":{"origen":"ana","destino":"beto"},"id":5}'
```

**HTTP:** `200 OK`

```json
{"jsonrpc":"2.0","error":{"code":-32602,"message":"Invalid params","data":"transferir() missing 1 required positional argument: 'monto'"},"id":5}
```

**Resultado:** Correcto. Respondió con `-32602` e identificó el parámetro faltante (`monto`).

## 6. JSON inválido

```powershell
Probar-RPC "06 - JSON invalido" '{"jsonrpc":"2.0","method":'
```

**HTTP:** `200 OK`

```json
{"jsonrpc":"2.0","error":{"code":-32700,"message":"Parse error"},"id":null}
```

**Resultado:** Correcto. Respondió con `-32700` e `id: null`.

## 7. Solicitud sin `jsonrpc`

```powershell
Probar-RPC "07 - Request sin version" '{"method":"saldo","params":{"cuenta":"ana"},"id":7}'
```

**HTTP:** `200 OK`

```json
{"jsonrpc":"2.0","error":{"code":-32600,"message":"Invalid Request"},"id":7}
```

**Resultado:** Correcto. Respondió con `-32600`.

## 8. Notificación sin `id`

```powershell
Probar-RPC "08 - Notificacion" '{"jsonrpc":"2.0","method":"saldo","params":{"cuenta":"ana"}}'
```

**HTTP:** `204 No Content`

```text
(sin cuerpo de respuesta)
```

**Resultado:** Correcto. La notificación no generó respuesta JSON.

## 9. Batch — solicitud válida y método inexistente

```powershell
Probar-RPC "09 - Batch" '[{"jsonrpc":"2.0","method":"saldo","params":{"cuenta":"ana"},"id":9},{"jsonrpc":"2.0","method":"no_existe","id":10}]'
```

**HTTP:** `200 OK`

```json
[{"jsonrpc":"2.0","result":{"cuenta":"ana","saldo":99000},"id":9},{"jsonrpc":"2.0","error":{"code":-32601,"message":"Method not found"},"id":10}]
```

**Resultado:** Correcto. Devolvió una lista con un resultado y un error `-32601`.

## Resumen de resultados

| N.º | Caso | Resultado |
|---|---|---|
| 1 | `saldo` con parámetros como objeto | Correcto (`result`) |
| 2 | `transferir` con parámetros como lista | Correcto (`result`) |
| 3 | Saldo insuficiente | Correcto (`-32000`) |
| 4 | Método inexistente | Correcto (`-32601`) |
| 5 | Parámetros incompletos | Correcto (`-32602`) |
| 6 | JSON inválido | Correcto (`-32700`) |
| 7 | Falta `jsonrpc` | Correcto (`-32600`) |
| 8 | Notificación | Correcto (HTTP `204`, sin cuerpo) |
| 9 | Batch | Correcto (`result` y `-32601`) |

**Conclusión:** Los nueve casos exigidos por la guía funcionaron en la ejecución registrada. Los errores de JSON-RPC viajaron dentro de respuestas HTTP `200`, mientras que la notificación produjo HTTP `204` sin contenido.
