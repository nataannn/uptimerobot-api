"""Healthcheck — antes era um JSON estático, agora testa a conectividade real."""
from flask import Blueprint, request

from config import UPTIME_ROBOT_KEY
from services.uptimerobot_client import UptimeRobotClient
from utils import fail, ok

health_bp = Blueprint("health", __name__)
_client = UptimeRobotClient(UPTIME_ROBOT_KEY, timeout=5, max_retries=1)


@health_bp.route("/health", methods=["GET"])
def health():
    """
    Healthcheck da API. Por padrão é leve (não bate na UptimeRobot);
    passe ?deep=true para validar também a key contra a API real.
    ---
    tags: [health]
    parameters:
      - in: query
        name: deep
        type: boolean
        required: false
    responses:
      200: {description: API (e opcionalmente a UptimeRobot) respondendo}
      503: {description: Dependência externa indisponível}
    """
    if request.args.get("deep", "").lower() != "true":
        return ok(message="API rodando com UptimeRobot v3.", version="v3")

    try:
        status_code, _ = _client.ping_account()
    except Exception as e:
        return fail(f"Falha ao contatar a UptimeRobot: {e}", status_code=503)

    if status_code == 200:
        return ok(message="API e UptimeRobot respondendo.", version="v3")

    return fail("UptimeRobot respondeu com erro — a key pode estar inválida.", status_code=503, uptimerobot_status=status_code)
