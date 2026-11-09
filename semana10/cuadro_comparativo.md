# Cuadro comparativo — RMI, CORBA, DCOM y JSON-RPC

**Equipo:** _(nombre)_  **Integrantes:** _(nombres)_  **Semana 10, trabajo autónomo**

Completen cada celda con una o dos frases propias (no copiar y pegar). Donde una tecnología no aplique, escriban "no aplica" y por qué.

| Criterio | Java RMI | CORBA | DCOM | JSON-RPC 2.0 |
|---|---|---|---|---|
| Año y origen (quién lo creó y para qué) | Sun, 1997. Comunicación remota entre objetos Java. | OMG, 1991. Integrar sistemas diferentes. | Microsoft, 1996. Extender COM a la red. | 2010. Estandarizar llamadas remotas mediante JSON. |
| Modelo (objetos remotos o procedimientos remotos) | Objetos remotos con estado. | Objetos distribuidos mediante ORB. | Objetos COM remotos. | Procedimientos remotos. |
| Contrato o IDL (cómo se declara la interfaz) | Interfaces Java `Remote`. | Interfaces definidas con IDL. | IDL de Microsoft e interfaces COM. | No requiere IDL; métodos y parámetros acordados. |
| Transporte y formato de los mensajes | JRMP/TCP, binario. | IIOP, binario CDR. | ORPC, binario. | JSON sobre HTTP u otro transporte. |
| Lenguajes y plataformas que soporta | Java y JVM. | Múltiples lenguajes y plataformas. | Principalmente Windows. | Cualquier lenguaje compatible con JSON. |
| Referencias remotas y estado (¿el servidor recuerda al cliente?) | Referencias remotas y objetos con estado. | Referencias a objetos con estado. | Referencias COM remotas. | Sin referencias remotas; la aplicación puede guardar estado. |
| Manejo de errores (cómo viaja un fallo al cliente) | Excepciones Java. | Excepciones IDL y del sistema. | Códigos `HRESULT`. | Objeto `error` con código y mensaje. |
| Relación con las cinco decisiones de la semana 9 (enmarcado, versión, id, errores, tipos) | JRMP gestiona mensajes e IDs; Java define tipos y errores. | GIOP define enmarcado, versión e ID; IDL define tipos y errores. | RPC gestiona mensajes e IDs; COM define tipos y errores. | HTTP delimita; `jsonrpc`, `id`, `error` y JSON definen lo demás. |
| Estado actual (vigente, legado, reemplazado por qué) | Vigente, aunque REST y gRPC son alternativas habituales. | Principalmente legado; reemplazado en muchos casos por REST y gRPC. | Principalmente legado; alternativas modernas como REST y gRPC. | Vigente para servicios RPC sencillos. |
| Caso de uso típico, real o histórico | Administración remota con JMX. | Telecomunicaciones y sistemas industriales. | Componentes empresariales Windows. | APIs y servicios como nuestro prototipo de pagos. |

## Conclusión del equipo (5 a 8 líneas)

¿Cuál de las cuatro se parece más a lo que construyeron en la semana 9 y por qué? ¿Cuál elegirían hoy para un servicio interno y cuál para una API pública?

JSON-RPC es la tecnología más parecida al protocolo que construimos en semana 9, porque ambos utilizan solicitudes, identificadores y respuestas con errores. La principal diferencia es que JSON-RPC ya define un formato estándar y permite evitar la creación de un protocolo propio.

Para un servicio interno elegiríamos gRPC por su eficiencia y sus contratos definidos. Para una API pública preferiríamos REST por su facilidad de integración. JSON-RPC también sería una buena alternativa para un servicio pequeño como nuestro sistema de pagos.

## Fuentes consultadas

Mínimo tres, con formato autor, título, año y enlace.

1. Oracle (2025). Java Remote Method Invocation API Guide. https://docs.oracle.com/en/java/javase/24/rmi/java-remote-method-invocation-api-guide.pdf

2. Oracle (2025). Using JMX Connectors to Manage Resources Remotely. https://docs.oracle.com/en/java/javase/25/jmx/using-jmx-connectors-manage-resources-remotely.html

3. Object Management Group (2021). CORBA Specification, Version 3.4. https://www.omg.org/spec/CORBA/3.4

4. Microsoft (2024). Distributed Component Object Model (DCOM) Remote Protocol. https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-dcom/86b9cf84-df2e-4f0b-ac22-1b957627e1ca

5. JSON-RPC Working Group (2010, actualización de 2013). JSON-RPC 2.0 Specification. https://www.jsonrpc.org/specification