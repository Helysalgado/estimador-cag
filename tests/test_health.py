def test_health_returns_ok_schema(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "estimador-cag"
    assert data["version"] == "0.1.0"
