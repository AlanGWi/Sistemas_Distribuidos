# Bitácora individual — Semana 10

**Nombre:** _(nombre y apellido)_  **Equipo:** _(nombre)_
**Archivo:** `semana10/bitacora_<apellido>.md` en el repositorio del equipo. **Entrega:** jueves 5 de noviembre de 2026, 18.00.

Esta bitácora es individual. Cada integrante escribe la suya con sus propias horas y sus propias palabras. No lleva nota, pero es un formativo obligatorio del programa y se revisa.

## Registro de sesiones

Una fila por sesión de trabajo. Las horas deben sumar al menos 8 entre los cuatro bloques.

| Fecha | Horas | Bloque | Qué estudié o hice | Qué me costó | Qué pregunté o respondí en el foro |
|---|---|---|---|---|---|
| 06-11-2026 | 2 | 1 Lecturas | RPC, stubs, parámetros, IDL y objetos distribuidos. | Parámetros remotos. | - |
| 06-11-2026 | 3 | 2 RMI, CORBA, DCOM | Investigación y comparación de las tres tecnologías. | Diferenciar los protocolos. | - |
| 07-11-2026 | 3 | 3 JSON-RPC 2.0 | Estudio de la especificación y relación con semana 9. | Códigos de error y notificaciones. | - |
| 07-11-2026 | 1 | 4 Prototipo | Adaptación de `rpc.py` al sistema de pagos y preparación de las pruebas. | Validación de transferencias. | - |
| | | | | | |

## Tres preguntas de cierre (responder con sus palabras, 3 a 5 líneas cada una)

1. ¿Qué tienen en común JSON-RPC 2.0 y el protocolo v3 que escribieron en la semana 9? ¿Qué decisión tomó la especificación por ustedes?

Ambos protocolos permiten enviar operaciones con argumentos y relacionar las respuestas con sus solicitudes mediante un identificador. En semana 9 definimos nuestro propio formato con versión, ID, datos y errores. JSON-RPC 2.0 estandariza estas decisiones mediante campos como method, params, id, result y error. Además, al utilizar HTTP, aprovechamos su mecanismo de delimitación de mensajes.

2. ¿Por qué RMI, CORBA y DCOM casi no se usan en sistemas nuevos y qué los reemplazó?

Estas tecnologías permiten realizar invocaciones remotas, pero presentan dependencias de lenguajes, plataformas o infraestructuras específicas. RMI está principalmente asociado a Java, CORBA necesita componentes como ORB e IDL, y DCOM está vinculado al ecosistema Microsoft. Actualmente suelen preferirse alternativas como REST y gRPC, que facilitan la integración entre sistemas diferentes.

3. ¿Qué parte del prototipo les costó más y cómo la resolvieron?

## Autoevaluación

| Afirmación | Sí | Parcial | No |
|---|---|---|---|
| Leí las secciones asignadas y puedo explicar la diferencia entre RPC y objetos distribuidos | | X | |
| Aporté al cuadro comparativo con fuentes propias | | X | |
| Puedo explicar el código del endpoint `/rpc` línea por línea | | X | |
| Probé los seis casos de error del prototipo con `curl` | X | | |
| Participé en el foro al menos una vez | | | X |
