"""
Cliente para a API v3 da UptimeRobot.

Centraliza tudo que antes estava espalhado pelo app.py:
- reuso de conexão (requests.Session) em vez de abrir uma nova por chamada
- retry automático com backoff exponencial em 429/5xx
- paginação por cursor
"""
import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import UPTIME_ACCOUNT_URL, UPTIME_MONITORS_URL

logger = logging.getLogger("uptimerobot-api")


class UptimeRobotClient:
    def __init__(self, api_key, timeout=15, max_retries=3):
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()

        retry = Retry(
            total=max_retries,
            backoff_factor=1.0,  # 1s, 2s, 4s entre tentativas
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PATCH"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_maxsize=20, pool_connections=20)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _headers(self, json_body=True):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "User-Agent": "UptimeRobot-Flask-API/2.0",
        }
        if json_body:
            headers["Content-Type"] = "application/json"
        return headers

    @staticmethod
    def _parse(response):
        try:
            body = response.json()
        except ValueError:
            body = {"raw": response.text[:500]}
        return response.status_code, body

    def create_monitor(self, payload):
        response = self.session.post(
            UPTIME_MONITORS_URL, json=payload, headers=self._headers(), timeout=self.timeout
        )
        return self._parse(response)

    def patch_monitor(self, monitor_id, payload):
        response = self.session.patch(
            f"{UPTIME_MONITORS_URL}/{monitor_id}", json=payload, headers=self._headers(), timeout=self.timeout
        )
        return self._parse(response)

    def get_all_monitors(self, page_size=50, max_pages=50):
        """Busca TODOS os monitores lidando com a paginação por cursor da v3."""
        monitors = []
        url = UPTIME_MONITORS_URL
        params = {"limit": page_size}
        page = 0

        while url and page < max_pages:
            response = self.session.get(
                url, headers=self._headers(json_body=False), params=params, timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()

            page_items = result.get("data", [])
            monitors.extend(page_items)
            logger.info("Página %d: %d monitores (acumulado: %d)",
                        page + 1, len(page_items), len(monitors))

            # A v3 entrega o link completo da próxima página em 'nextLink'.
            next_link = result.get("nextLink")
            if next_link:
                url = next_link
                params = {}
            else:
                url = None

            page += 1

        logger.info("TOTAL coletado: %d monitores", len(monitors))
        return monitors

    def ping_account(self):
        """Usado pelo /health para checar se a key ainda é válida de verdade."""
        response = self.session.get(
            UPTIME_ACCOUNT_URL, headers=self._headers(json_body=False), timeout=self.timeout
        )
        return self._parse(response)
