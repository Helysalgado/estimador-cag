from app.config import settings
from app.prompts import render_estimation_prompt
from app.schemas.estimation import EstimationRequest, EstimationResponse
from app.services.cache import build_cache, make_key
from app.services.llm_wrapper import WrapperConfig, generate_sync, get_default_wrapper_config

PROMPT_VERSION = "v1"

cache = build_cache(
    redis_url=settings.REDIS_URL,
    cache_ttl_seconds=settings.CACHE_TTL_SECONDS,
)


def estimate_from_request(
    request: EstimationRequest,
    *,
    prompt_version: str = PROMPT_VERSION,
) -> EstimationResponse:
    """Generate an estimation from a typed request using Jinja prompts and Redis cache."""
    system_prompt, user_message = render_estimation_prompt(request, version=prompt_version)
    config: WrapperConfig = get_default_wrapper_config()
    cache_key = make_key(
        system_prompt=system_prompt,
        user_message=user_message,
        model=f"{config.provider}/{config.model}",
        max_tokens=config.max_tokens,
        thinking_budget=config.thinking_budget,
    )
    cached = cache.get(cache_key)
    if cached is not None:
        text = cached.get("text") or cached.get("estimation", "")
        version = cached.get("prompt_version", prompt_version)
        return EstimationResponse(text=text, prompt_version=version)

    result = generate_sync(
        system_prompt=system_prompt,
        user_message=user_message,
        config=config,
    )
    response = EstimationResponse(
        text=result["estimation"],
        prompt_version=prompt_version,
    )
    cache.set(
        cache_key,
        {
            "text": response.text,
            "prompt_version": response.prompt_version,
        },
    )
    return response
