def test_missing_api_key_is_rejected(client):
    resp = client.get("/monitors")
    assert resp.status_code == 401


def test_wrong_api_key_is_rejected(client):
    resp = client.get("/monitors", headers={"X-API-KEY": "chave-errada"})
    assert resp.status_code == 401


def test_health_does_not_require_api_key(client):
    resp = client.get("/health")
    assert resp.status_code == 200
