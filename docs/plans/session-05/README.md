# Plan de implementación — Sesión 5 (estimador-cag)

Este plan aterriza el ejercicio de clase de Sesión 5 sobre el estado actual del repo.

## Objetivo

Pasar de un estimator transaccional (una petición, una respuesta) a un flujo conversacional con:

- sesiones (`session_id`),
- memoria separada del historial (`project_metadata`),
- ventana deslizante (`MAX_TURNS`),
- adjuntos en `multipart/form-data` (PDF/DOCX),
- cliente Streamlit multi-turno.

## Decisiones cerradas para esta implementación

- **Adjuntos:** Camino B (extracción local de texto).
- **Memoria:** `ProjectMetadata` tipado separado de `ConversationHistory`.
- **Estrategia historial:** ventana deslizante con `MAX_TURNS = 6`.
- **Estado sesión:** diccionario en memoria de proceso (sin BBDD/Redis para sesiones).
- **Actualización metadata:** heurística simple en esta fase (coste/latencia baja).
- **Compatibilidad:** mantener `POST /api/v1/estimate` actual y añadir rutas de sesión nuevas.

## Alcance y no alcance

### Entra

- `POST /api/v1/sessions` -> crea sesión, devuelve `session_id`.
- `POST /api/v1/sessions/{session_id}/estimate` -> recibe `transcript` + `attachments[]` (multipart).
- Inyección de `project_metadata` en prompt Jinja2.
- Actualización de historial y metadata por turno.
- Adaptación de Streamlit para sesión multi-turno.
- Tests mínimos de integración.

### No entra

- Persistencia de sesiones (Redis/PostgreSQL).
- RAG/chunking vectorial.
- TTL/archivado automático de sesiones inactivas.
- Actor-Critic-Boss (se verá en directo).

## Estructura objetivo (nuevo código)

```text
app/
├── schemas/
│   ├── estimation.py                  # existente
│   └── sessions.py                    # NEW: SessionCreateResponse, SessionEstimateForm...
├── services/
│   ├── sessions.py                    # NEW: SessionStore, ConversationHistory, metadata update
│   └── attachments.py                 # NEW: extract_text_from_pdf/docx, validation
├── routers/
│   ├── estimations.py                 # existente (stateless)
│   └── sessions.py                    # NEW: /api/v1/sessions/*
└── prompts/
    └── estimation/
        ├── v1/system.j2               # update: bloque <project_metadata>
        └── v2/system.j2               # update: bloque <project_metadata>
```

## Plan por pasos

### Paso 0 — Preparación

- Crear rama `pre-session-05`.
- Añadir dependencias para Camino B:
  - `pypdf` o `pymupdf` (PDF),
  - `python-docx` (DOCX).
- Definir variable `MAX_TURNS` (config o constante de servicio).

**Verificación**

- Proyecto instala dependencias sin errores.

---

### Paso 1 — Estado de sesión en memoria

Implementar `app/services/sessions.py` con:

- `Message` (`role`, `content`),
- `ProjectMetadata` (`project_name`, `assumed_team_size`, `mentioned_technologies`, `agreed_scope`, `explicit_constraints`, `rejected_options`),
- `ConversationHistory`:
  - añade pares `user/assistant`,
  - aplica ventana deslizante por turnos,
  - método `build_messages(system_prompt: str) -> list[dict]`.
- `Session` y `SessionStore` (`dict[str, Session]` en memoria).

Documentar en docstring la volatilidad (se pierde al reiniciar, single-process).

**Verificación**

- Test unitario de recorte de ventana.

---

### Paso 2 — Endpoint de creación de sesión

Crear `app/routers/sessions.py`:

- `POST /api/v1/sessions` -> `{"session_id": "<uuid>"}`.

Actualizar `app/main.py` para incluir el router nuevo.

**Verificación**

- `curl -X POST /api/v1/sessions` devuelve UUID válido.

---

### Paso 3 — Adjuntos multipart (Camino B)

Crear `app/services/attachments.py`:

- Validar MIME/extensiones permitidas: PDF, DOCX.
- Extraer texto:
  - PDF -> `pypdf`/`pymupdf`,
  - DOCX -> `python-docx`.
- Limitar tamaño por archivo y número de adjuntos.
- Construir bloque con delimitadores:

```text
--- attachment: file.pdf ---
<texto extraído>
```

En `POST /sessions/{session_id}/estimate`, recibir:

- `transcript: str = Form(...)`,
- `attachments: list[UploadFile] = File(default=[])`.

**Verificación**

- Endpoint acepta multipart sin adjuntos y con adjuntos.
- Error 422/400 para tipo no soportado.

---

### Paso 4 — Inyección de `project_metadata` en templates

Actualizar `system.j2` (v1 y v2):

- bloque `<project_metadata>` condicional,
- tratar metadata como hechos establecidos.

Ajustar render en loader/servicio para pasar `project_metadata`.

**Verificación**

- Test de prompts: con metadata presente aparece bloque, sin metadata no.

---

### Paso 5 — Orquestación de turno multi-turno

Implementar en router/servicio de sesiones:

1. Recuperar sesión por `session_id`.
2. Construir `user_turn = transcript + attachments_text`.
3. Renderizar system con metadata actual.
4. Construir `messages` desde historial + turno actual.
5. Llamar LLM.
6. Añadir `assistant` a historial.
7. Actualizar metadata por heurística.
8. Devolver `EstimationResponse` existente (`text`, `prompt_version`).

Heurística inicial sugerida:

- tecnologías mencionadas por vocabulario,
- patrón básico para nombre de proyecto,
- alcance acordado como resumen corto del último turno.

**Verificación**

- Dos turnos sobre misma sesión conservan coherencia.

---

### Paso 6 — Cliente Streamlit

Actualizar `streamlit_app.py`:

- crear sesión al iniciar (`POST /sessions`),
- guardar `session_id` en `st.session_state`,
- enviar multipart al endpoint de sesión,
- `file_uploader(..., accept_multiple_files=True)`,
- panel lateral con metadata (debug),
- botón "Nueva conversación" (nuevo `session_id` + reset local).

**Verificación**

- conversación de 3 turnos en misma sesión,
- metadata visible y cambiante.

---

### Paso 7 — Tests mínimos (integración)

Añadir tests con `pytest`:

1. **Memoria multi-turno:** 2 peticiones, metadata evoluciona.
2. **Adjunto influye:** con PDF adjunto cambia contenido de prompt o salida mockeada.
3. **Ventana:** tras 8 turnos, historial efectivo no supera `MAX_TURNS`.

Mantener suite actual en verde.

**Verificación**

- `uv run pytest -q` todo verde.

---

### Paso 8 — README y entregable

Actualizar `README.md` con:

- endpoints de sesión,
- flujo multipart con adjuntos,
- camino de adjuntos elegido (B) y justificación,
- cómo se actualiza `project_metadata`,
- limitaciones actuales (memoria en proceso, sin persistencia).

## Criterios de "hecho"

- `POST /api/v1/sessions` funciona.
- `POST /api/v1/sessions/{session_id}/estimate` multipart funciona.
- misma sesión conserva coherencia entre turnos.
- metadata visible/actualizada por turno.
- historial respeta `MAX_TURNS`.
- README explica decisiones.
- tests pasan en local.

## Checklist de progreso

- [x] Paso 0 — Preparación y dependencias
- [x] Paso 1 — SessionStore + ConversationHistory + ProjectMetadata
- [x] Paso 2 — Endpoint `POST /sessions`
- [x] Paso 3 — Adjuntos Camino B (multipart + extracción)
- [x] Paso 4 — Metadata en system prompt
- [x] Paso 5 — Endpoint multi-turno con actualización de memoria
- [x] Paso 6 — Streamlit multi-turno
- [x] Paso 7 — Tests sesión 05
- [x] Paso 8 — README y cierre

## Rama sugerida

```bash
git checkout -b pre-session-05
```

## Referencias

- Documento de clase: `sesion5.md` (adjuntos, memoria, ventanas, anti-patrones).
- Continuidad de sesión 04: `docs/plans/session-04/`.
