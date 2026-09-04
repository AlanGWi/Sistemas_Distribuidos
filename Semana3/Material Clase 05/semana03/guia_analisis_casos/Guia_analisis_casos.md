# Guía de análisis de casos — Semana 3

**Sistemas Distribuidos (FDICI25 / INFO35) · Viernes 4 de septiembre de 2026 · Laboratorio de Informática**

Instrumento de la sesión de análisis de casos (RA1). Cada equipo trabaja **un** caso,
completa la plantilla de la sección 2 y la guarda como
`semana03/guia_analisis_casos/caso_<nombre>.md` en el repositorio del equipo.
Se expone en 3 minutos y se responde una pregunta cruzada de otro equipo.

Herramienta de referencia: la matriz de la clase del jueves (seis modelos × cinco preguntas).

---

### Caso C — Red de distribución de contenidos (CDN)

Copias de contenido (video, imágenes, archivos estáticos) ubicadas en puntos de
presencia cercanos al usuario. El DNS dirige a cada cliente al nodo más cercano;
si el nodo no tiene el objeto, lo pide al *origen* y lo guarda en caché por un
tiempo (TTL). Ejemplo de uso: streaming de los Juegos Panamericanos Santiago 2023.

Preguntas guía: ¿Qué pasa cuando el origen cambia un archivo y la copia de
Santiago aún tiene la versión anterior? ¿Qué se sacrifica a cambio de la baja
latencia? ¿Qué ocurre si cae el nodo de Santiago?


## 2. Plantilla (copiar a `caso_<nombre>.md` y completar)

```markdown
# Análisis de caso: <CND>

**Equipo:** <Diego leiva, Alan gimilio>  ·  **Fecha:** 04-09-2026

## 1. Modelo dominante
<cluster | grid | cloud | edge | P2P | ubicuo>

Justificación con las preguntas de la matriz (marcar la que más pesó):
¿Quién manda? El origen es la autoridad final del contenido, pero cada nodo de borde (PoP) atiende las solicitudes de forma autónoma sin consultar al origen en cada petición — control descentralizado en la operación diaria, jerárquico en la autoridad del dato.
¿Los nodos son parecidos? Los PoPs son homogéneos entre sí (misma función de caché), pero asimétricos respecto al origen, que es el único con la copia autoritativa. — Esta es la pregunta que más pesa para clasificarlo como edge: la asimetría origen/borde es la firma del modelo.
¿Qué tan lejos están? Los nodos están deliberadamente cerca del usuario (ese es el objetivo de diseño), mientras el origen puede estar lejos.
¿Qué pasa si uno desaparece? El servicio sigue: DNS/anycast redirige al siguiente nodo más cercano, con algo más de latencia pero sin caída total.

Modelos secundarios presentes (si los hay) y por qué no dominan:
 Cloud está presente en el origen (típicamente alojado en infraestructura cloud elástica), pero no domina porque la experiencia del usuario y el desafío central del caso ocurren en el borde, no en el origen.

## 2. Nodos y roles
| Nodo | Rol | ¿Cuántos? | ¿Estado o sin estado? |
|---|---|---|---|
| | | | |


## 3. Diagrama de interacciones
(Cajas = nodos, flechas etiquetadas con el protocolo o el tipo de mensaje.
Puede ser ASCII, una foto de la pizarrón o un archivo draw.io exportado a PNG.)


Cliente ──DNS lookup──▶ [Resolutor DNS / Anycast]
   │                          │
   │◀── IP del PoP cercano ───┘
   │
   ├──HTTP GET objeto──▶ [PoP Santiago]
   │                          │
   │                    ¿hit en caché?
   │                     ├─ sí ─▶ responde directo
   │                     └─ no ─▶ ──GET origen──▶ [Origen]
   │                                              │
   │                          ◀── objeto + TTL ───┘
   │◀── respuesta + cachea localmente ───┘

## 4. Desafío dominante
<heterogeneidad | apertura | escalabilidad | tolerancia a fallos | concurrencia | seguridad>

¿Cómo lo resuelve el sistema? ¿Qué falacia de la Semana 2 estaría asumiendo si no lo hiciera?

Escalabilidad

Lo resuelve replicando el contenido en múltiples PoPs y sirviendo desde el más cercano, evitando que cada solicitud viaje al origen. El costo de esa solución es la consistencia: el TTL implica que, por un tiempo, distintos usuarios pueden ver versiones distintas del mismo archivo.

Falacia de la Semana 2 que se estaría asumiendo si no se cacheara: "la latencia es cero" (y también, en menor medida, "el ancho de banda es infinito"). Sin caché de borde, cada petición cruzaría la red hasta el origen como si eso no tuviera costo exactamente la suposición que la falacia critica.

## 5. ¿Qué pasa si cae X?
Elegir el nodo cuya caída más duele y describir:
- Qué siguen viendo los usuarios:
- Qué deja de funcionar:
- ¿El sistema elige responder (AP) o no equivocarse (CP)? ¿Cómo lo saben?

## 6. La desventaja que vamos a defender
Una desventaja concreta del modelo elegido para este caso, con un ejemplo.
(Es la respuesta que preparan para la pregunta cruzada.)
```

---

## 3. Exposición y pregunta cruzada

- **3 minutos** por equipo: modelo dominante, diagrama, desafío dominante, qué pasa si cae X.
- **1 minuto** de pregunta cruzada: otro equipo pregunta por una desventaja o un
  escenario de falla. El equipo expositor responde con la sección 6 de su guía.
- Criterios formativos (sin nota): la clasificación está justificada con la matriz;
  el diagrama tiene nodos y flechas etiquetadas; la desventaja es concreta, no genérica.
