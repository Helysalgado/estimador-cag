# Planes de implementación — Sesión 4 (estimador-cag)

Esta carpeta contiene los planes **paso a paso** para migrar `estimador-cag` al estado objetivo de la [Sesión 4 — estimator](https://github.com/LIDR-academy/ai-engineering/tree/session_4/estimator):

- **Frontend:** formulario tipado (ya no chat).
- **Backend:** contrato Pydantic estrecho + prompts en **Jinja2 versionados**.
- **Base conservada:** wrapper LiteLLM, Redis cache, Docker, CI.

## Cómo usar estos planes

1. Lee `00-contexto-y-objetivo.md` una sola vez.
2. Ejecuta **un paso a la vez** en orden numérico.
3. Al terminar cada paso, ejecuta la sección **Verificación** del plan correspondiente.
4. **No avances al siguiente paso** hasta confirmar explícitamente que podemos continuar (en el chat con el agente o en tu revisión).

## Orden de los pasos

| Paso | Archivo | Resumen |
|------|---------|---------|
| 0 | [00-contexto-y-objetivo.md](./00-contexto-y-objetivo.md) | Visión, alcance, decisiones pendientes |
| 1 | [01-schemas-y-contrato.md](./01-schemas-y-contrato.md) | Enums + `EstimationRequest` / `EstimationResponse` |
| 2 | [02-prompts-jinja2-loader.md](./02-prompts-jinja2-loader.md) | `app/prompts/`, templates v1, `render_estimation_prompt` |
| 3 | [03-refactor-endpoint-servicio.md](./03-refactor-endpoint-servicio.md) | Router + `llm_service` + cache + stream opcional |
| 4 | [04-streamlit-cliente-http.md](./04-streamlit-cliente-http.md) | Formulario + `POST` al API |
| 5 | [05-tests.md](./05-tests.md) | Schemas, prompts, endpoint, ajustes cache/stream |
| 6 | [06-readme-y-entregable.md](./06-readme-y-entregable.md) | README, rama `pre-session-04`, prueba manual |
| 7 | [07-opcional-bonus.md](./07-opcional-bonus.md) | v2, `reference_projects`, structlog (opcional) |

## Estado del progreso

Marca aquí conforme avances (o pídele al agente que lo actualice):

- [x] Paso 0 — Contexto leído y decisiones cerradas
- [x] Paso 1 — Schemas
- [x] Paso 2 — Prompts Jinja2
- [x] Paso 3 — Endpoint y servicio
- [x] Paso 4 — Streamlit
- [x] Paso 5 — Tests
- [x] Paso 6 — README y entregable
- [x] Paso 7 — Bonus (opcional)

## Referencias

- Repositorio LIDR: [ai-engineering/session_4/estimator](https://github.com/LIDR-academy/ai-engineering/tree/session_4/estimator)
- Metaprompt Fase 1 local (solo formulario, sin Jinja): ver historial del proyecto / `prompt_cursor_sesion_4_fase_1_estimador_cag.md`

## Rama sugerida

```bash
git checkout -b pre-session-04
```
