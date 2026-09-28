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


def _mock_single_page(rsps):
    rsps.add(
        responses.GET,
        UPTIME_MONITORS_URL,
        json={"data": [
            {"id": 1, "friendlyName": "Site Ação", "url": "https://a.com", "status": "UP",
             "createDateTime": "2026-04-08T10:00:00Z", "apiKey": "segredo",
             "tags": [{"id": 1, "name": "production", "color": "blue"}, {"id": 2, "name": "cliente-x", "color": "red"}]},
            {"id": 2, "friendlyName": "=HYPERLINK(\"x\")", "url": "https://b.com", "status": "DOWN"},
        ], "nextLink": None},
        status=200,
    )


def test_export_json(client, auth_headers):
    with responses.RequestsMock() as rsps:
        _mock_single_page(rsps)
        resp = client.get("/monitors/export?format=json", headers=auth_headers)

    assert resp.status_code == 200
    assert resp.mimetype == "application/json"
    assert "attachment" in resp.headers["Content-Disposition"]
    data = resp.get_json()
    assert len(data) == 2
    assert data[0]["friendlyName"] == "Site Ação"
    assert data[0]["tagNames"] == ["production", "cliente-x"]
    assert data[0]["createDateTime"] == "2026-04-08T10:00:00Z"
    assert data[1]["tagNames"] == []
    # campos sensíveis da API nunca podem vazar no export
    assert "apiKey" not in data[0]


def test_export_csv(client, auth_headers):
    with responses.RequestsMock() as rsps:
        _mock_single_page(rsps)
        resp = client.get("/monitors/export?format=csv", headers=auth_headers)

    assert resp.status_code == 200
    assert resp.mimetype == "text/csv"
    text = resp.get_data(as_text=True)
    assert text.startswith("\ufeffid,friendlyName,url")
    assert "Site Ação" in text
    assert "production, cliente-x" in text
    # célula com fórmula precisa sair neutralizada
    assert "'=HYPERLINK" in text


def test_export_invalid_format(client, auth_headers):
    resp = client.get("/monitors/export?format=xml", headers=auth_headers)
    assert resp.status_code == 400


def test_export_requires_api_key(client):
    resp = client.get("/monitors/export")
    assert resp.status_code == 401
