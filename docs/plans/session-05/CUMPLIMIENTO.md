# Informe de cumplimiento — Sesión 5

Contraste entre:

- Material: `IAENG/material/mat-sesion5.md`
- Referencia LIDR: [ai-engineering/session_5/estimator](https://github.com/LIDR-academy/ai-engineering/tree/session_5/estimator)
- Proyecto: `estimador-cag` (estado actual en rama `pre-session-06`, con base S5 implementada)

## Veredicto global

| Área | Veredicto |
|------|-----------|
| Ejercicio pre-sesión 5 (`mat-sesion5.md`, pasos 1–7) | **Cumple** |
| Entregable (rama, README, tests, Streamlit) | **Cumple** |
| Paridad estructural con LIDR `session_5` | **Parcial** — mismas capacidades, distinto layout de módulos y contrato HTTP ampliado |
| Evolución S6+ en el mismo repo | **Presente** — no invalida S5; es capa posterior |

---

## Matriz de cumplimiento (material `mat-sesion5.md`)

| Requisito | Estado | Evidencia en `estimador-cag` |
|-----------|--------|------------------------------|
| `POST /sessions` → `session_id` | **Cumple** | `app/routers/sessions.py` → `POST /api/v1/sessions` |
| Memoria en proceso (dict, sin BBDD) | **Cumple** | `app/services/sessions.py` — `SessionStore` |
| `ConversationHistory` + ventana deslizante | **Cumple** | `SESSION_MAX_TURNS` / `MAX_CONVERSATION_TURNS` (default 6) |
| `ProjectMetadata` separado del historial | **Cumple** | Dataclass + `ProjectMetadataView` en respuesta |
| `POST /sessions/{id}/estimate` multipart | **Cumple** | `transcript` + `attachments[]` |
| Adjuntos PDF/DOCX (un camino) | **Cumple** | **Camino B** — `app/services/attachments.py` (`pypdf`, `python-docx`) |
| Bloque `<project_metadata>` en system Jinja | **Cumple** | `app/prompts/estimation/project_metadata.j2` en v1/v2 |
| Actualización metadata por turno | **Cumple** | Heurísticas en `session_estimation.py` + extractor LLM (S6, compatible con material) |
| Cliente: sesión, uploads, panel metadata, nueva conversación | **Cumple** | `streamlit_app.py` — pestaña Conversación + recuperación tras reinicio API |
| Tests: metadata 2 turnos | **Cumple** | `tests/test_session_integration.py::test_multi_turn_metadata_evolves_over_two_requests` |
| Tests: adjunto PDF influye prompt | **Cumple** | `test_pdf_attachment_text_reaches_llm_messages` |
| Tests: 8 turnos → ventana ≤ MAX | **Cumple** | `test_sliding_window_keeps_at_most_max_turns_after_eight_requests` |
| README: camino B, metadata, límites | **Cumple** | `README.md` — sección Sesión 5 y Camino B |
| Mantener `POST /api/v1/estimate` stateless | **Cumple** | `app/routers/estimations.py` intacto |

### Explícitamente fuera de S5 (correcto no exigirlo en el pre-ejercicio)

| Tema material “no entra” | En tu repo hoy | Impacto en cumplimiento S5 |
|---------------------------|----------------|----------------------------|
| Resumen acumulativo + anclas | Sí (S6) | No resta; es evolución posterior |
| Tier dinámico | Sí (S6) | Idem |
| Actor-Critic-Boss | Sí (S6, opcional) | Idem |
| Persistencia Redis/Postgres para sesiones | No | Correcto para S5 |
| RAG / búsqueda web / function calling BBDD | No | Correcto para S5 |

---

## Comparación con LIDR [session_5/estimator](https://github.com/LIDR-academy/ai-engineering/tree/session_5/estimator)

| Aspecto | LIDR S5 | `estimador-cag` | ¿Cumple espíritu S5? |
|---------|---------|-----------------|----------------------|
| Módulo sesiones | `app/sessions/models.py`, `store.py` | `app/services/sessions.py` | **Sí** (misma responsabilidad) |
| Adjuntos | `app/attachments/extractor.py` | `app/services/attachments.py` | **Sí** |
| Orquestación turno | `EstimationService.estimate_conversational()` | `estimate_session_turn()` | **Sí** |
| Metadata extractor LLM | `metadata_extraction/v1/*.j2` + servicio | `app/sessions/metadata_extractor.py` | **Sí** (añadido/reforzado en S6) |
| Respuesta estimate sesión | `EstimationResponse` (`text`, `prompt_version`) | `SessionEstimationResponse` + `project_metadata` + `turn_count` | **Sí** (mejor para UI/debug) |
| Campos form en cada turno | `project_type`, `detail_level`, `output_format` en multipart | Defaults fijos en `render_session_system_prompt` | **Parcial** — ver ajuste A1 |
| Prefijo rutas | `/sessions` | `/api/v1/sessions` | **Aceptable** (convención del repo desde S4) |
| `POST /sessions` status | `201` | `200` | **Cosmético** |
| `GET /sessions/{id}` debug | `SessionInfoResponse` (metadata + counts) | `SessionDebugResponse` (+ anchors, tier, `last_turn_observed` S6) | **Sí** |
| Input guardrails en sesión | Sí (`InputGuardrailViolation`) | No implementado | **Parcial** — ver ajuste B1 |
| `transcript` min length en Form | 20 (LIDR) | 1 (tu router) | **Parcial** — ver ajuste A2 |
| Campos metadata | 4 campos base | + `explicit_constraints`, `rejected_options` | **Sí** (extensión útil) |

---

## Diferencias aceptables (no bloquean “hecho”)

1. **Prefijo `/api/v1`** — coherente con el estimador stateless del mismo proyecto.
2. **Respuesta enriquecida** — devolver `project_metadata` en JSON evita un `GET` extra para el panel Streamlit; alineado con criterio “metadata visible entre turnos”.
3. **Heurística + LLM extractor** — el material permite una u otra; tener ambas (merge en `session_estimation.py`) es válido y más robusto que solo regex.
4. **Recuperación de sesión en Streamlit** — si el API reinicia, crea sesión nueva y reintenta; mejora UX sin contradecir volatilidad documentada.

---

## Ajustes opcionales (solo si buscas paridad LIDR o pulir S5)

| ID | Prioridad | Ajuste | Motivo |
|----|-----------|--------|--------|
| A1 | Media | Exponer `project_type`, `detail_level`, `output_format` en `POST .../estimate` (Form) y en Streamlit | Paridad con [sessions.py LIDR S5](https://github.com/LIDR-academy/ai-engineering/blob/session_5/estimator/app/routers/sessions.py); hoy usas defaults `web_saas` / `medium` / `phases_table` |
| A2 | Baja | `transcript` `min_length=20` en endpoint sesión | Alinea validación con LIDR y material S4 |
| A3 | Baja | `POST /sessions` → `201 Created` | Cosmética HTTP |
| B1 | Baja | Guardrails de entrada en ruta sesión (si existen en stateless en tu línea S4+) | LIDR S5 los reutiliza; tu repo no tiene módulo `guardrails/` |
| B1 | — | **No recomendado ahora** si aún no hay guardrails en el proyecto | Implementar solo por paridad sin suite S4 previa |

**No recomendado como “cierre S5”:** mover código a `app/sessions/` + `app/attachments/` solo por estructura LIDR — refactor grande sin beneficio funcional.

---

## Checklist criterios de “hecho” (material)

- [x] `POST /sessions` crea sesión y devuelve `session_id`
- [x] `POST /sessions/{id}/estimate` multipart con transcripción y adjuntos
- [x] Coherencia multi-turno (tests + metadata en respuesta)
- [x] `project_metadata` actualizado entre turnos
- [x] Ventana deslizante respetada
- [x] README con Camino B y extracción de metadata
- [x] Tests Paso 7 en verde (incluidos en suite amplia actual)

---

## Verificación sugerida (regresión Sesión 5)

```bash
uv run pytest tests/test_sessions.py tests/test_sessions_endpoint.py \
  tests/test_session_estimation.py tests/test_session_integration.py \
  tests/test_attachments.py -q
```

Manual:

```bash
uv run uvicorn app.main:app --reload
uv run streamlit run streamlit_app.py
# Pestaña Conversación: ≥3 turnos, panel metadata, adjunto PDF opcional, "Nueva conversación"
```

---

## Relación con sesiones posteriores

| Sesión | Qué añade sobre S5 |
|--------|-------------------|
| S6 | `turn_observed`, stress evals, compresión/anchors/tier/ACB |
| S7 | `embedding_pipeline` (presupuestos JSON), independiente del chat |

Cerrar brechas de S6/S7 **no es requisito** para declarar S5 cumplida.

---

## Referencias

- Plan local ejecutado: [README.md](./README.md)
- Material: `IAENG/material/mat-sesion5.md`
- LIDR: [session_5/estimator](https://github.com/LIDR-academy/ai-engineering/tree/session_5/estimator)
- Sesión 4 previa: [../session-04/AJUSTES.md](../session-04/AJUSTES.md)
