def test_estimate_uses_mocked_llm(client, monkeypatch):
    def fake_estimate(_transcription: str) -> dict:
        return {
            "estimation": "## Estimación de prueba\n\n**Total: 10 horas**",
            "model": "gpt-4o-mini",
            "provider": "openai",
            "timestamp": "2026-01-01T00:00:00",
        }

    monkeypatch.setattr(
        "app.routers.estimations.estimate_project",
        fake_estimate,
    )

    response = client.post(
        "/api/v1/estimate",
        json={
            "transcription": (
                "Cliente pide un MVP de catálogo web con login, panel básico, "
                "roles y exportación de reportes en 8 semanas."
            )
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "Estimación de prueba" in body["estimation"]
    assert body["model"]
    assert body["provider"]
    assert body["timestamp"]
