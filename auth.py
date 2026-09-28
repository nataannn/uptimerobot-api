"""Autenticação por API key estática (header X-API-KEY)."""
import hmac
from functools import wraps

from flask import request

from config import API_KEY_SECRET
from utils import fail


def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key_received = request.headers.get("X-API-KEY", "")

        # hmac.compare_digest evita timing attack (comparação de string normal
        # vaza quantos caracteres iniciais bateram, via tempo de execução).
        is_valid = bool(api_key_received) and hmac.compare_digest(api_key_received, API_KEY_SECRET)

        if not is_valid:
            return fail(
                "Acesso negado! Chave API inválida ou ausente.",
                status_code=401,
                hint="Envie o header X-API-KEY com a chave correta.",
            )

        return f(*args, **kwargs)
    return decorated
