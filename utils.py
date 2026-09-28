"""Envelope de resposta padronizado — antes cada rota inventava seu próprio formato."""
from flask import jsonify


def ok(status_code=200, **fields):
    body = {"status": "success"}
    body.update(fields)
    return jsonify(body), status_code


def fail(message, status_code=400, **fields):
    body = {"status": "error", "message": message}
    body.update(fields)
    return jsonify(body), status_code
