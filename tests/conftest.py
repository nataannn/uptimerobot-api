import os

# Precisa ser setado ANTES de importar app/config, senão config.validate_config()
# derruba o processo (comportamento correto em produção, mas ruim em teste).
os.environ.setdefault("UPTIME_ROBOT_KEY", "test-uptime-key")
os.environ.setdefault("API_KEY_SECRET", "test-secret")

import pytest  # noqa: E402

from app import app as flask_app  # noqa: E402


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    flask_app.config["RATELIMIT_ENABLED"] = False
    with flask_app.test_client() as c:
        yield c


@pytest.fixture
def auth_headers():
    return {"X-API-KEY": "test-secret"}
