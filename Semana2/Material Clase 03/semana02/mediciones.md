# Mediciones — Laboratorio N°1 (Semana 2)

**Equipo:** _______________   **Integrantes:** Diego Leiva / Alan Gimilio
**Fecha:** 28-08-2026   **Entorno:** Docker Desktop (Windows) / otro: ________

PS D:\SistemasDistribuidos\Sistemas_Distribuidos\Semana2\Material Clase 03\semana02> c ping -c 10 servidor
PING servidor (172.18.0.2) 56(84) bytes of data.
64 bytes from servidor.sd_net (172.18.0.2): icmp_seq=1 ttl=64 time=0.144 ms
64 bytes from servidor.sd_net (172.18.0.2): icmp_seq=2 ttl=64 time=0.065 ms
64 bytes from servidor.sd_net (172.18.0.2): icmp_seq=3 ttl=64 time=0.049 ms
64 bytes from servidor.sd_net (172.18.0.2): icmp_seq=4 ttl=64 time=0.049 ms
64 bytes from servidor.sd_net (172.18.0.2): icmp_seq=5 ttl=64 time=0.046 ms
64 bytes from servidor.sd_net (172.18.0.2): icmp_seq=6 ttl=64 time=0.046 ms
64 bytes from servidor.sd_net (172.18.0.2): icmp_seq=7 ttl=64 time=0.068 ms
64 bytes from servidor.sd_net (172.18.0.2): icmp_seq=8 ttl=64 time=0.047 ms
64 bytes from servidor.sd_net (172.18.0.2): icmp_seq=9 ttl=64 time=0.046 ms
64 bytes from servidor.sd_net (172.18.0.2): icmp_seq=10 ttl=64 time=0.045 ms




Connecting to host servidor, port 5201
[  5] local 172.18.0.3 port 45188 connected to 172.18.0.2 port 5201
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-1.00   sec  2.64 GBytes  22.6 Gbits/sec    0    710 KBytes       
[  5]   1.00-2.00   sec  2.67 GBytes  22.9 Gbits/sec    0   1.01 MBytes       
[  5]   2.00-3.00   sec  2.61 GBytes  22.4 Gbits/sec    0   1.01 MBytes       
[  5]   3.00-4.00   sec  2.63 GBytes  22.6 Gbits/sec    0   1.17 MBytes       
[  5]   4.00-5.01   sec  2.92 GBytes  25.0 Gbits/sec    0   1.17 MBytes       
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-5.01   sec  13.5 GBytes  23.2 Gbits/sec    0            sender
[  5]   0.00-5.01   sec  13.5 GBytes  23.2 Gbits/sec                  receiver

iperf Done.

## Paso 1 — Línea base
| Métrica | Valor |
|---|---|
| RTT ping (promedio) | 0.060 ms |
| Throughput iperf3 | 	23.2 Gbit/s |

## Pasos 2 y 3 — Latencia inyectada (100 llamadas)
| Latencia `tc` | Total (s) | Promedio (ms) | Máx (ms) | ¿Esperado? (sí/no, por qué) |
|---|---|---|---|---|
| 0 ms (base) | 0.011 | 0.1 | 1.4 | Sí, latencia local de red Docker (~0.06 ms de RTT medido con ping) |
| 50 ms | 5.041 | 50.4 | 51.3 | Sí, 100 llamadas × 50 ms ≈ 5.0 s esperado, coincide casi exacto |
| 200 ms | 20.045 | 200.4 | 200.9 | Sí, 100 × 200 ms ≈ 20 s esperado, coincide casi exacto |
| 500 ms | 50.046 | 500.5 | 501.0 | Sí, 100 × 500 ms ≈ 50 s esperado, coincide casi exacto |

## Paso 4 — Pérdida de paquetes
| Pérdida `tc` | Throughput iperf3 | Total cliente (s) | Observación |
|---|---|---|---|
| 1% | 10.7 Gbit/s (cae de 23.2 Gbit/s base, ~54%) | Con solo 1% de pérdida el throughput ya cae a menos de la mitad, TCP reduce agresivamente su ventana de congestión ante la primera señal de pérdida |
| 5% | 449 Mbit/s | 1.459 | Total apenas cambia, pero el máximo se dispara a 412.6 ms (vs 14.6 ms promedio): retransmisión TCP en silencio |
| 20% | 1.21 Mbit/s | 5.252 | Throughput colapsa (~99.99% de caída respecto al base); máximo llega a 652.0 ms |
| 100% (falla provocada) | — | Sin timeout: no arrojó "colgado" como predice el README, sino error inmediato `[Errno 113] No route to host`. Con `TIMEOUT_S=3`: abortó a los 3.0 s con 0 llamadas completadas | El cliente sin timeout falla rápido en este entorno (Docker Desktop/Windows) en vez de quedarse esperando indefinidamente; con timeout configurado, el comportamiento es predecible y controlado |

## Falacia que asumimos sin advertirlo

**Falacia:** "La red es confiable" (Deutsch/Gosling, falacia #1).

**Dónde se ve en `cliente.py`:** el valor por defecto de `TIMEOUT_S` es `0` (sin límite), 
según la tabla de variables de entorno del README. Esto significa que el código no tiene 
ningún mecanismo propio para detectar que la red dejó de responder delega esa decisión 
por completo al sistema operativo. Lo comprobamos en el Paso 4: con `loss 100%` y sin 
timeout, el programa no mostró ningún error de aplicación; lo que apareció 
(`[Errno 113] No route to host`) fue un error del sistema operativo/Docker, no una 
decisión del cliente. Si la red hubiera fallado "en silencio" en vez de devolver ese 
error de sistema (como ocurre en una red física real), el cliente se habría quedado 
esperando para siempre.

**Evidencia adicional:** incluso con pérdidas parciales (5% y 20%), el cliente reportó 
un total casi normal (1.459s y 5.252s), pero el máximo se disparó a 412.6ms y 652.0ms 
respectivamente. El código no distingue entre "la llamada fue rápida" y "la llamada 
tuvo que reintentar varias veces a nivel TCP" confía ciegamente en que la capa de 
transporte va a resolver cualquier problema de red sin que la aplicación se entere.

**Qué cambio la corregiría:** fijar un `TIMEOUT_S` explícito por defecto (no 0), y agregar 
lógica de reintento con backoff y un límite máximo de intentos, en vez de esperar 
indefinidamente o fallar en el primer intento sin más contexto para el usuario.
