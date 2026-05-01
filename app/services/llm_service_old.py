from openai import OpenAI
from app.config import settings
from app.context.examples import ESTIMATION_EXAMPLES


def _build_system_prompt() -> str:
    """
    Construye el system prompt con:
    - rol del modelo
    - instrucciones claras
    - ejemplos (few-shot)
    """

    intro = (
        "Eres un experto en estimación de proyectos de software. "
        "Tu tarea es analizar una transcripción de reunión con un cliente "
        "y generar una estimación estructurada basada en ejemplos previos.\n\n"
        "Debes seguir el mismo formato que los ejemplos.\n"
        "Sé claro, estructurado y realista en tiempos y recursos.\n"
        "Debes verificar que el total de horas sea consistente con la duración estimada y el tamaño del equipo. Si no lo es, ajusta la duración o el equipo."
        "Si el cliente menciona un plazo, evalúa si es realista y ajusta la estimación en consecuencia."
        "Debes siempre validar que la estimación sea coherente entre horas, equipo y duración. Incluye una sección de evaluación del plazo."
    )

    examples_text = "\n\n=== EJEMPLOS DE REFERENCIA ===\n"

    for i, example in enumerate(ESTIMATION_EXAMPLES, start=1):
        examples_text += f"\n--- Ejemplo {i} ---\n"
        examples_text += f"Resumen:\n{example['meeting_summary']}\n\n"
        examples_text += f"Estimación:\n{example['estimation']}\n"

    return intro + examples_text


def estimate_project(meeting_transcript: str) -> str:
    """
    Genera una estimación a partir de la transcripción de una reunión.
    """

    # Validación de provider
    if settings.LLM_PROVIDER != "openai":
        raise ValueError("Solo OpenAI está implementado actualmente")

    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY es requerida para usar OpenAI")

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    system_prompt = _build_system_prompt()

    user_prompt = (
        "A continuación tienes la transcripción de una reunión con un cliente.\n"
        "Genera una estimación siguiendo el formato de los ejemplos.\n\n"
        f"Transcripción:\n{meeting_transcript}"
    )

    response = client.responses.create(
        model=settings.LLM_MODEL,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_output_tokens=800,
    )

    return response.output_text


