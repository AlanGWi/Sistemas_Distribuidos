# Observaciones semana 11 · Migración a gRPC

Equipo ……………… · Dominio ……………… · Fecha 06-11-2026

## 1. Contrato
- Archivo `proto/servicio.proto` con **2 operaciones RPC**: `Saldo` y
    `Transferir`.
- Operaciones que modifican estado y llevan `id_solicitud`:
    **`Transferir`**, ya que modifica los saldos de las cuentas
    involucradas.
- Operaciones idempotentes (se pueden repetir sin efecto extra):
    **`Saldo`**, porque solamente consulta información. `Transferir` no
    es idempotente por sí sola, pero la deduplicación mediante
    `id_solicitud` evita aplicar dos veces una misma solicitud.

## 2. Stubs generados
- Clase del stub en el cliente: `PagosStub`.
- Clase base del servidor: `PagosServicer`.
- Qué hace el stub cuando llamamos `stub.Transferir(...)`, en dos
    líneas, con sus palabras:

    El stub funciona como un intermediario entre el cliente y el
    servidor remoto. Serializa la solicitud, la envía mediante gRPC y
    espera la respuesta para convertirla nuevamente en un objeto que el
    cliente pueda utilizar.

## 3. Equivalencia de errores JSON-RPC → gRPC

| Caso | JSON-RPC (semana 10) | gRPC (hoy) | Comando usado |
|---|---|---|---|
| Método inexistente | -32601 | UNIMPLEMENTED | Llamada directa a un método inexistente mediante gRPC |
| Parámetros inválidos | -32602 | INVALID_ARGUMENT | Transferir con `id_solicitud` vacío |
| Error del dominio | -32000 | FAILED_PRECONDITION | `Transferir ana beto 999999` |
| Servidor caído | sin conexión | UNAVAILABLE | `docker compose kill servidor` |
| Respuesta lenta | timeout del cliente | DEADLINE_EXCEEDED | `FALLA=siempre` y `transferir ana beto 500 --timeout 2` |

**Pistas.** En nuestro dominio, los parámetros inválidos se pueden comprobar enviando una transferencia con `id_solicitud` vacío. Para probar un método inexistente, el cliente no permite llamarlo directamente, por lo que se utiliza esta llamada gRPC:

```powershell
docker compose exec cliente python -c "import grpc; grpc.insecure_channel('servidor:50051').unary_unary('/pagos.v1.Pagos/Borrar')(b'', timeout=2)"
```

El error muestra `status = StatusCode.UNIMPLEMENTED`.

## 4. Falla intermedia · semántica teórica frente a la observada

| # | Configuración | Qué vio el cliente | Saldos finales con `saldo` | Semántica observada |
|---|---|---|---|---|
| 1 | `FALLA=no`, sin reintentos | Transferencia ejecutada correctamente (`OK`) | Ana: 99500 / Beto: 20500 | Normal |
| 2 | `FALLA=siempre`, sin reintentos | `DEADLINE_EXCEEDED`, aunque se aplicó la transferencia | Ana: 99500 / Beto: 20500 | Maybe |
| 3 | `FALLA=siempre`, `--reintentos 2`, sin `DEDUP` | Tres intentos fallidos por timeout; se aplicó tres veces | Ana: 98500 / Beto: 21500 | At-least-once |
| 4 | `FALLA=siempre DEDUP=1`, `--reintentos 2` | Primer intento con timeout; segundo exitoso | Ana: 99500 / Beto: 20500 | At-most-once |
| 5 | `docker compose kill servidor` durante una llamada | `UNAVAILABLE, Socket closed` | Tras reiniciar: Ana: 100000 / Beto: 20000 | Caída del servidor y pérdida del estado en memoria |

Pegar aquí las líneas relevantes de `docker compose logs servidor` de los casos 3 y 4.

### Caso 3 — Sin deduplicación

```text
[servidor] Transferir id=6dbae703 -> {'origen': 'ana', 'saldo_origen': 99500, 'destino': 'beto', 'saldo_destino': 20500}
[servidor] FALLA=siempre, cambio YA aplicado, demoro la respuesta 3 s
[servidor] Transferir id=6dbae703 -> {'origen': 'ana', 'saldo_origen': 99000, 'destino': 'beto', 'saldo_destino': 21000}
[servidor] FALLA=siempre, cambio YA aplicado, demoro la respuesta 3 s
[servidor] Transferir id=6dbae703 -> {'origen': 'ana', 'saldo_origen': 98500, 'destino': 'beto', 'saldo_destino': 21500}
[servidor] FALLA=siempre, cambio YA aplicado, demoro la respuesta 3 s
```

### Caso 4 — Con deduplicación

```text
[servidor] Transferir id=4ae32650 -> {'origen': 'ana', 'saldo_origen': 99500, 'destino': 'beto', 'saldo_destino': 20500}
[servidor] FALLA=siempre, cambio YA aplicado, demoro la respuesta 3 s
[servidor] Transferir id=4ae32650 repetido, devuelvo lo guardado SIN aplicar de nuevo
```

## 5. Conclusión
La operación `Transferir` es peligrosa de reintentar sin `id_solicitud`, ya que podría ejecutarse varias veces. En la vida real, esto provocaría transferencias duplicadas y movimientos incorrectos de dinero. El identificador permite reconocer solicitudes repetidas y evitar aplicar la misma transferencia más de una vez.