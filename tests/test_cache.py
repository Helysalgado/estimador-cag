from app.services.cache import RedisCache, make_key


def test_make_key_is_deterministic():
    key1 = make_key(
        system_prompt="sys",
        user_message="msg",
        model="openai/gpt-4o-mini",
        max_tokens=300,
        thinking_budget=None,
    )
    key2 = make_key(
        system_prompt="sys",
        user_message="msg",
        model="openai/gpt-4o-mini",
        max_tokens=300,
        thinking_budget=None,
    )
    assert key1 == key2
    assert key1.startswith("estimation:v1:")


def test_make_key_changes_when_model_changes():
    key1 = make_key("sys", "msg", "openai/gpt-4o-mini", 300, None)
    key2 = make_key("sys", "msg", "anthropic/claude-3-haiku-20240307", 300, None)
    assert key1 != key2


def test_redis_cache_set_get_with_fake_client(monkeypatch):
    class FakeRedis:
        def __init__(self):
            self.store = {}

        def get(self, key):
            return self.store.get(key)

        def set(self, name, value, ex):
            self.store[name] = value
            self.last_ex = ex

    fake = FakeRedis()
    monkeypatch.setattr("app.services.cache.Redis.from_url", lambda *args, **kwargs: fake)
    local_cache = RedisCache(redis_url="redis://test:6379/0", default_ttl_seconds=86400)
    local_cache.set("a", {"ok": True})
    assert fake.last_ex == 86400
    assert local_cache.get("a") == {"ok": True}
