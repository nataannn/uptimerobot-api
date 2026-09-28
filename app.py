"""
Entrypoint da aplicação. Mantido enxuto de propósito: só monta o app Flask e
registra as peças (config, logging, extensões, blueprints). A lógica de
negócio mora em services/ e routes/.
"""
import logging

from flasgger import Swagger
from flask import Flask

import config
from extensions import configure_logging, limiter, register_request_id
from routes.health import health_bp
from routes.monitors import monitors_bp
from utils import fail

config.validate_config()
configure_logging()
logger = logging.getLogger("uptimerobot-api")

app = Flask(__name__)

register_request_id(app)
limiter.init_app(app)

app.config["SWAGGER"] = {
    "title": "UptimeRobot API",
    "uiversion": 3,
    "specs_route": "/apidocs/",
}
Swagger(app, template={
    "securityDefinitions": {
        "ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-API-KEY"}
    }
})

app.register_blueprint(monitors_bp)
app.register_blueprint(health_bp)


@app.errorhandler(429)
def ratelimit_handler(e):
    return fail(f"Limite de requisições excedido: {e.description}", status_code=429)


@app.errorhandler(404)
def not_found_handler(_e):
    return fail("Rota não encontrada.", status_code=404)


if __name__ == "__main__":
    logger.info("API Flask com UptimeRobot v3 iniciada em http://localhost:5000 (debug=%s)", config.FLASK_DEBUG)
    app.run(host="0.0.0.0", port=5000, debug=config.FLASK_DEBUG)
