"""Logging estruturado, request_id por requisição e rate limiting."""
import json
import logging
import uuid

from flask import g, request
from flask_limiter import Limiter


class RequestIdLogFilter(logging.Filter):
    """Injeta o request_id da requisição atual (quando existe) em todo log record."""

    def filter(self, record):
        try:
            record.request_id = getattr(g, "request_id", "-")
        except RuntimeError:
            # fora de um contexto de aplicação/requisição (ex: import, startup)
            record.request_id = "-"
        return True


class JsonFormatter(logging.Formatter):
    """Formata cada linha de log como JSON, pronto pra um agregador (ELK/Datadog/etc.)."""

    def format(self, record):
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging():
    logger = logging.getLogger("uptimerobot-api")
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RequestIdLogFilter())

    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def _rate_limit_key():
    """Limita por API key quando presente, senão cai pro IP remoto."""
    api_key = request.headers.get("X-API-KEY")
    return api_key if api_key else (request.remote_addr or "anonymous")


limiter = Limiter(key_func=_rate_limit_key, default_limits=["120 per minute"])


def register_request_id(app):
    @app.before_request
    def _assign_request_id():
        incoming = request.headers.get("X-Request-ID")
        g.request_id = incoming or uuid.uuid4().hex[:12]

    @app.after_request
    def _echo_request_id(response):
        response.headers["X-Request-ID"] = getattr(g, "request_id", "-")
        return response
