# Paso 6 — README y entregable

> **Depende de:** Paso 5 (tests en verde).  
> **Siguiente:** Paso 7 (bonus, opcional).

## Objetivo

Documentar el nuevo flujo, limpiar código muerto y dejar la rama lista para review en la sesión en directo.

## Archivos a modificar

| Archivo | Acción |
|---------|--------|
| `README.md` | Contrato nuevo, curl, Streamlit, tests, estructura con `app/prompts/` |
| `.env.example` | `ESTIMATOR_API_BASE_URL`, modelos sugeridos |
| `app/context/examples.py` | Eliminar o marcar deprecated si ya no se usa |
| `docs/README.md` | Enlace a `docs/plans/session-04/` (opcional) |

## Contenido mínimo del README

1. **Descripción:** estimación desde formulario tipado, prompts versionados en Jinja2.
2. **Levantar:** Docker / uvicorn + Redis.
3. **Probar API:** ejemplo `curl` con los 4 campos.
4. **Streamlit:** `uv run streamlit run streamlit_app.py` + variable `ESTIMATOR_API_BASE_URL`.
5. **Tests:** `uv run pytest` y qué cubre cada archivo.
6. **Estructura del proyecto** (árbol con `app/prompts/`).
7. **Versionado de prompts:** cómo añadir `v2/` sin tocar router.

## Limpieza opcional

- [x] Quitar sección “chat conversacional” del README
- [x] Documentación SSE actualizada (formato LIDR)
- [x] Badge Jinja2 añadido

## Entregable sesión

- [x] Rama `pre-session-04` activa con todos los pasos 1–6
- [x] README actualizado
- [ ] (Opcional) captura o GIF del formulario

## Verificación final (checklist integración)

```bash
docker compose up -d redis   # si usas cache
uv run uvicorn app.main:app --reload --port 8000
uv run streamlit run streamlit_app.py
uv run pytest
```

- [x] `validate_structure.py` + `pytest` en verde
- [ ] Health `GET /health` OK (manual con API levantada)
- [ ] Formulario → estimación visible (manual)
- [ ] Segunda petición idéntica puede servir desde cache (opcional, manual)

## Antes de continuar

Confirma: **“Sesión 4 base completada”** o **“Podemos continuar con el Paso 7 (bonus)”** si quieres extensiones.
