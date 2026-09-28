def test_health_basic(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "success"


def test_health_deep_ok(client):
    import responses

    from config import UPTIME_ACCOUNT_URL

    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, UPTIME_ACCOUNT_URL, json={"data": {}}, status=200)
        resp = client.get("/health?deep=true")

    assert resp.status_code == 200
    assert resp.get_json()["status"] == "success"


def test_health_deep_upstream_down(client):
    import responses

    from config import UPTIME_ACCOUNT_URL

    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, UPTIME_ACCOUNT_URL, json={"error": "unauthorized"}, status=401)
        resp = client.get("/health?deep=true")

    assert resp.status_code == 503
    assert resp.get_json()["status"] == "error"
