# Semana 12 — Pagos electrónicos con Pyro5

Se reutilizó **sin modificaciones** `semana11/laboratorio/dominio.py`, con las
operaciones `saldo(cuenta)` y `transferir(origen, destino, monto)`.

- `Pasarela`: servicio principal, en `servidor:9100`, nombre lógico `sd.pagos.pasarela`.
- `Transaccion`: objeto con estado (origen, destino, monto, estado); la fábrica
  `iniciar_transaccion` lo registra y devuelve un **proxy**. `confirmar` aplica
  `dominio.transferir` y destruye el objeto; `cancelar` destruye sin transferir.
- `nombres:9090`: descubrimiento de objetos.

## Inicio en tres comandos

Desde `semana12/` (Docker Desktop iniciado):

```powershell
docker compose up -d --build
docker compose exec cliente python cliente_pyro.py uri
docker compose exec cliente python cliente_pyro.py listar
```

**Si la Semana 11 u otro repositorio utiliza `sd_servidor` o `sd_cliente`, hay
que detener ese stack antes**. Ejemplo, desde la raíz de este repositorio:

```powershell
docker compose -f semana11/laboratorio/docker-compose.yml down
```

## Pruebas para completar observaciones.md

Ejecutar desde `semana12/`:

```powershell
# Paso 1 — nombres
docker compose logs servidor
docker compose exec cliente python cliente_pyro.py uri

# Paso 2 — consultas y cambio de saldos
docker compose exec cliente python cliente_pyro.py listar
docker compose exec cliente python cliente_pyro.py saldo ana
docker compose exec cliente python cliente_pyro.py transferir ana beto 500
docker compose exec cliente python cliente_pyro.py saldo ana
docker compose exec cliente python cliente_pyro.py saldo beto

# Paso 3 — objeto con estado y referencia colgante
docker compose exec cliente python cliente_pyro.py vivos
docker compose exec cliente python cliente_pyro.py transaccion ana beto 300
docker compose exec cliente python cliente_pyro.py vivos
```

**Paso 3, paso por valor:** cambiar `POR_VALOR=1` en `.env`, recrear con
`docker compose up -d --force-recreate servidor`, probar
`docker compose exec cliente python cliente_pyro.py transaccion ana beto 200`.
Se espera un error de serialización del objeto `Transaccion` no registrado.
Restaurar `POR_VALOR=0` y recrear el servidor.

```powershell
# Paso 4 — single
docker compose exec cliente python cliente_pyro.py quien --veces 2
```

Cambiar `MODO=session` en `.env`, ejecutar
`docker compose up -d --force-recreate servidor` y repetir `quien --veces 2`.
Restaurar `MODO=single` y recrear el servidor antes del Paso 5.

**Paso 5, fallas:** utilizar dos o tres terminales en `semana12/`. El orden es
importante para interpretar los resultados:

- Terminal A: `docker compose exec cliente python cliente_pyro.py vigilar`.
- Terminal B: `docker compose kill servidor`, observar A;
  `docker compose start servidor`, observar recuperación.
- Para pérdida de estado: `transferir ana beto 100`, observar los saldos,
  `kill servidor`, `start servidor` y volver a observar: los datos son en memoria.
- Para caída de nombres: con `vigilar` ya conectado, `docker compose kill nombres`;
  abrir otro cliente (`... listar`) y comparar; luego `docker compose start nombres`
  y repetir; finalmente `docker compose restart servidor` para re-registrar.
- Para referencia rota por caída: ejecutar en otra terminal
  `docker compose exec cliente python cliente_pyro.py transaccion ana beto 200 --esperar 20`;
  mientras espera, hacer `kill servidor` y luego `start servidor`;
  documentar la salida final del primer terminal (puede tardar en reintentos).

**Nota sobre el dominio:** los saldos iniciales son `ana=100000`, `beto=20000`
y `caja=0`. Cualquier reinicio del proceso los restablece; no hay persistencia.
Una transacción de prueba confirmada **sí mueve dinero** en el estado de este
simulador y no debe reintentarse manualmente como si fuera idempotente.

`REREGISTRO=5` hace que se vuelva a publicar la URI cada cinco segundos,
introduciendo peticiones periódicas al servidor de nombres.

## Cierre

Las plantillas `observaciones.md`, `calidad.md`, `proyecto/ALCANCE.md` y
`proyecto/bitacora.md` están **pendientes de completar con el equipo**. No
contienen pruebas ni aprobaciones ficticias. Al terminar, ejecutar:

```powershell
docker compose down -v
```
