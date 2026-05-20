VALID_STREAM_PAYLOAD = {
    "description": (
        "A web platform for order management with roles and admin panel "
        "delivered in ten weeks."
    ),
    "project_type": "web_saas",
    "detail_level": "medium",
    "output_format": "phases_table",
}


def test_estimate_stream_sse_events(client, monkeypatch):
    def fake_complete_stream(**kwargs):  # noqa: ANN003
        _ = kwargs
        yield "Hola "
        yield "stream"

    monkeypatch.setattr(
        "app.routers.estimations.complete_stream",
        fake_complete_stream,
    )

    with client.stream(
        "POST",
        "/api/v1/estimate/stream",
        json=VALID_STREAM_PAYLOAD,
    ) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())

    assert "event: status" in body
    assert "event: token" in body
    assert "event: complete" in body
    assert "Hola " in body
    assert "v1" in body


def test_estimate_stream_rejects_short_description(client):
    payload = {**VALID_STREAM_PAYLOAD, "description": "short"}
    response = client.post("/api/v1/estimate/stream", json=payload)
    assert response.status_code == 422


def test_estimate_stream_honours_prompt_version_query(client, monkeypatch):
    def fake_complete_stream(**kwargs):  # noqa: ANN003
        yield "x"

    monkeypatch.setattr(
        "app.routers.estimations.complete_stream",
        fake_complete_stream,
    )

    with client.stream(
        "POST",
        "/api/v1/estimate/stream?prompt_version=v2",
        json=VALID_STREAM_PAYLOAD,
    ) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())

    assert "event: complete" in body
    assert "prompt_version" in body
    assert "v2" in body
