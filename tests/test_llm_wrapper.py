import pytest

from app.services.llm_wrapper import WrapperConfig, generate_sync, stream_events


class _Message:
    def __init__(self, content: str):
        self.content = content


class _Choice:
    def __init__(self, content: str):
        self.message = _Message(content)
        self.delta = _Message(content)


class _Response:
    def __init__(self, content: str):
        self.choices = [_Choice(content)]
        self.usage = type("Usage", (), {"prompt_tokens": 11, "completion_tokens": 22})()


def test_generate_sync_uses_fallback_on_recoverable_error(monkeypatch):
    state = {"calls": 0}

    def fake_completion(**kwargs):  # noqa: ANN003
        state["calls"] += 1
        if state["calls"] == 1:
            err = RuntimeError("rate limit")
            setattr(err, "status_code", 429)
            raise err
        assert kwargs["model"] == "anthropic/claude-3-haiku-20240307"
        return _Response("Estimación fallback")

    monkeypatch.setattr("app.services.llm_wrapper.completion", fake_completion)
    result = generate_sync(
        system_prompt="sys",
        user_message="msg",
        config=WrapperConfig(
            provider="openai",
            model="gpt-4o-mini",
            fallback_provider="anthropic",
            fallback_model="claude-3-haiku-20240307",
        ),
    )
    assert result["provider"] == "anthropic"
    assert "fallback" in result["estimation"].lower()
    assert result["meta"]["fallback_used"] is True


class _AsyncStream:
    def __init__(self, parts):
        self._parts = parts

    def __aiter__(self):
        async def generator():
            for part in self._parts:
                chunk = type("Chunk", (), {"choices": [_Choice(part)]})()
                yield chunk

        return generator()


@pytest.mark.anyio
async def test_stream_events_emits_token_and_done(monkeypatch):
    async def fake_acompletion(**kwargs):  # noqa: ANN003
        assert kwargs["stream"] is True
        return _AsyncStream(["Hola ", "mundo"])

    monkeypatch.setattr("app.services.llm_wrapper.acompletion", fake_acompletion)
    events = []
    async for item in stream_events(
        system_prompt="sys",
        user_message="msg",
        config=WrapperConfig(provider="openai", model="gpt-4o-mini"),
    ):
        events.append(item)
    assert any(e["event"] == "token" for e in events)
    assert events[-1]["event"] == "done"
