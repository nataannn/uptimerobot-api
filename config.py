"""Configuração central da aplicação: variáveis de ambiente e constantes."""
import logging
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("uptimerobot-api")

UPTIME_ROBOT_KEY = os.getenv("UPTIME_ROBOT_KEY")
API_KEY_SECRET = os.getenv("API_KEY_SECRET")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

# Quantos monitores criar/atualizar em paralelo nas rotas de lote.
# Mantido moderado de propósito para não estourar o rate limit da UptimeRobot.
BULK_MAX_WORKERS = int(os.getenv("BULK_MAX_WORKERS", "8"))

UPTIME_API_BASE = "https://api.uptimerobot.com/v3"
UPTIME_MONITORS_URL = f"{UPTIME_API_BASE}/monitors"
UPTIME_ACCOUNT_URL = f"{UPTIME_API_BASE}/account"

ALL_REGIONS = ["na", "eu", "as", "oc"]  # North America, Europe, Asia, Australia


def validate_config():
    """Falha rápido e alto se a configuração obrigatória estiver ausente."""
    if not UPTIME_ROBOT_KEY:
        logger.error("ERRO: Não encontrado UPTIME_ROBOT_KEY no .env")
        raise SystemExit(1)

    if not API_KEY_SECRET:
        logger.error("ERRO: Não encontrado API_KEY_SECRET no .env")
        raise SystemExit(1)
