import responses

from config import UPTIME_MONITORS_URL


def test_create_monitor_missing_fields(client, auth_headers):
    resp = client.post("/create-monitor", json={"friendlyName": "Site sem URL"}, headers=auth_headers)
    assert resp.status_code == 400
    assert resp.get_json()["status"] == "error"


def test_create_monitor_invalid_url(client, auth_headers):
    resp = client.post(
        "/create-monitor",
        json={"friendlyName": "Site", "url": "nao-e-uma-url"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_create_monitor_success(client, auth_headers):
    with responses.RequestsMock() as rsps:
        rsps.add(responses.POST, UPTIME_MONITORS_URL, json={"id": 123}, status=201)
        resp = client.post(
            "/create-monitor",
            json={"friendlyName": "Site OK", "url": "https://example.com"},
            headers=auth_headers,
        )

    assert resp.status_code == 201
    body = resp.get_json()
    assert body["status"] == "success"
    assert body["monitor_id"] == 123


def test_bulk_create_mixed_results(client, auth_headers):
    payload = [
        {"friendlyName": "Válido", "url": "https://example.com"},
        {"friendlyName": "Sem URL"},
    ]

    with responses.RequestsMock() as rsps:
        rsps.add(responses.POST, UPTIME_MONITORS_URL, json={"id": 1}, status=201)
        resp = client.post("/bulk-create", json=payload, headers=auth_headers)

    body = resp.get_json()
    assert resp.status_code == 200
    assert body["total"] == 2
    assert body["sucessos"] == 1
    assert body["falhas"] == 1


def test_bulk_create_requires_list(client, auth_headers):
    resp = client.post("/bulk-create", json={"not": "a list"}, headers=auth_headers)
    assert resp.status_code == 400


def test_list_monitors_paginates(client, auth_headers):
    first_page = {
        "data": [{"id": 1, "friendlyName": "A"}],
        "nextLink": "https://api.uptimerobot.com/v3/monitors?cursor=abc",
    }
    second_page = {"data": [{"id": 2, "friendlyName": "B"}], "nextLink": None}

    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, UPTIME_MONITORS_URL, json=first_page, status=200)
        rsps.add(responses.GET, "https://api.uptimerobot.com/v3/monitors?cursor=abc", json=second_page, status=200)
        resp = client.get("/monitors", headers=auth_headers)

    body = resp.get_json()
    assert resp.status_code == 200
    assert body["total"] == 2
