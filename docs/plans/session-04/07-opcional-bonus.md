# Paso 7 — Bonus (opcional)

> **Depende de:** Paso 6 completado.  
> **Solo si hay tiempo antes del directo.**

## 7.1 Versionado real (`prompt_version=v2`)

- Duplicar `app/prompts/estimation/v1/` → `v2/` con variación deliberada (tono, ejemplos, reglas).
- Query param en router: `POST /api/v1/estimate?prompt_version=v2`
- Pasar `version` a `render_estimation_prompt(request, version=...)`
- Devolver `prompt_version` dinámico en `EstimationResponse`
- Tests: render v2 distinto de v1 en al menos un string clave

## 7.2 Contexto de proyectos similares

```python
class ReferenceProject(BaseModel):
    name: str
    description: str
    estimated_weeks: int | None = None

class EstimationRequest(BaseModel):
    ...
    reference_projects: list[ReferenceProject] | None = None
```

- En `system.j2` o `user.j2`:

```jinja2
{% if reference_projects %}
{% for ref in reference_projects %}
...
{% endfor %}
{% endif %}
```

- Tests: con lista presente el render incluye un nombre de proyecto; sin lista, bloque ausente.

## 7.3 Logging del prompt renderizado

- Añadir `structlog` al loader
- En cada `render_estimation_prompt`, emitir evento con `version` y hash SHA256 de `system+user`
- Configurar según `APP_ENV` en `config.py`

## Verificación bonus

- [ ] Tests nuevos para la extensión elegida
- [ ] `pytest` sigue en verde
- [ ] README menciona la feature

## Antes de cerrar

No es obligatorio para la sesión base. Confirma si implementamos algún bonus o cerramos en Paso 6.
