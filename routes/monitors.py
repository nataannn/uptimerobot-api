"""Rotas de criação, listagem e importação de monitores."""
import json
import logging
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from flask import Blueprint, request
from pydantic import ValidationError
from requests.exceptions import HTTPError

from auth import require_api_key
from config import BULK_MAX_WORKERS, UPTIME_ROBOT_KEY
from extensions import limiter
from schemas import MonitorIn, RegionsUpdateIn
from services.uptimerobot_client import UptimeRobotClient
from utils import fail, ok

logger = logging.getLogger("uptimerobot-api")
monitors_bp = Blueprint("monitors", __name__)

# Um client por processo: reusa conexões (pool) e a política de retry configurada.
client = UptimeRobotClient(UPTIME_ROBOT_KEY)


def _build_payload(monitor: MonitorIn):
    return {
        "friendlyName": monitor.friendlyName,
        "url": monitor.url,
        "type": "http",
        "interval": monitor.interval,
        "timeout": monitor.timeout,
        "tagNames": monitor.tagNames,
        "successHttpResponseCodes": monitor.successHttpResponseCodes,
        "groupId": monitor.groupId,
        "regionData": {"REGION": monitor.regions},
    }


def create_monitor_item(raw_monitor):
    """
    Cria um único monitor a partir de um dict de entrada.
    Nunca lança exceção: sempre retorna um dict de resultado padronizado,
    para que um item malformado não derrube o lote inteiro.
    """
    friendly_name = raw_monitor.get("friendlyName") if isinstance(raw_monitor, dict) else None

    try:
        monitor = MonitorIn(**raw_monitor)
    except ValidationError as e:
        return {
            "status": "error",
            "friendlyName": friendly_name or "(sem nome)",
            "message": "; ".join(err["msg"] for err in e.errors()),
        }

    try:
        payload = _build_payload(monitor)
        status_code, result = client.create_monitor(payload)

        if status_code == 201:
            return {
                "status": "success",
                "friendlyName": monitor.friendlyName,
                "monitor_id": result.get("id"),
            }
        return {
            "status": "error",
            "friendlyName": monitor.friendlyName,
            "status_code": status_code,
            "message": result.get("error") or result.get("message") or str(result),
        }
    except Exception as e:
        return {"status": "error", "friendlyName": monitor.friendlyName, "message": str(e)}


def create_monitors_parallel(monitors):
    """Cria vários monitores em paralelo (pool limitado) em vez de um por vez em série."""
    with ThreadPoolExecutor(max_workers=BULK_MAX_WORKERS) as pool:
        return list(pool.map(create_monitor_item, monitors))


@monitors_bp.route("/create-monitor", methods=["POST"])
@require_api_key
@limiter.limit("30 per minute")
def create_monitor():
    """
    Cria um monitor HTTP na UptimeRobot.
    ---
    tags: [monitors]
    security: [{ApiKeyAuth: []}]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [friendlyName, url]
          properties:
            friendlyName: {type: string}
            url: {type: string}
            interval: {type: integer, default: 300}
            timeout: {type: integer, default: 30}
            tagNames: {type: array, items: {type: string}}
            groupId: {type: integer, default: 0}
            regions: {type: array, items: {type: string}}
    responses:
      201: {description: Monitor criado}
      400: {description: Payload inválido}
      401: {description: API key ausente ou inválida}
    """
    data = request.get_json(silent=True) or {}

    try:
        monitor = MonitorIn(**data)
    except ValidationError as e:
        return fail("Payload inválido.", errors=e.errors(include_url=False, include_context=False))

    payload = _build_payload(monitor)
    status_code, result = client.create_monitor(payload)

    if status_code == 201:
        return ok(
            status_code=201,
            message="Monitor criado com sucesso.",
            monitor_id=result.get("id"),
            friendlyName=monitor.friendlyName,
        )
    return fail(
        result.get("error", result.get("message", "Erro desconhecido.")),
        status_code=status_code,
        details=result,
    )


@monitors_bp.route("/bulk-create", methods=["POST"])
@require_api_key
@limiter.limit("10 per minute")
def bulk_create():
    """
    Cria vários monitores de uma vez (em paralelo).
    ---
    tags: [monitors]
    security: [{ApiKeyAuth: []}]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: array
          items: {type: object}
    responses:
      200: {description: Resumo do lote}
      400: {description: Corpo inválido}
    """
    monitors = request.get_json(silent=True)

    if not monitors or not isinstance(monitors, list):
        return fail("Você deve enviar uma lista de monitors.")

    resultados = create_monitors_parallel(monitors)
    sucessos = sum(1 for r in resultados if r["status"] == "success")

    return ok(
        total=len(monitors),
        sucessos=sucessos,
        falhas=len(monitors) - sucessos,
        detalhes=resultados,
    )


@monitors_bp.route("/import-monitors", methods=["GET"])
@require_api_key
@limiter.limit("10 per minute")
def import_monitors():
    """
    Lê monitors.json (raiz do projeto) e cria todos os monitores nele em paralelo.
    ---
    tags: [monitors]
    security: [{ApiKeyAuth: []}]
    responses:
      200: {description: Resumo do lote}
      404: {description: Arquivo não encontrado}
    """
    try:
        with open("monitors.json", "r", encoding="utf-8") as file:
            monitors = json.load(file)
    except FileNotFoundError:
        return fail("Arquivo monitors.json não encontrado!", status_code=404)
    except json.JSONDecodeError as e:
        return fail(f"monitors.json não é um JSON válido: {e}", status_code=400)

    logger.info("Encontrados %d monitors no arquivo.", len(monitors))
    resultados = create_monitors_parallel(monitors)
    sucessos = sum(1 for r in resultados if r["status"] == "success")

    return ok(
        total=len(monitors),
        sucessos=sucessos,
        falhas=len(monitors) - sucessos,
        detalhes=resultados,
    )


@monitors_bp.route("/import-from-excel", methods=["GET"])
@require_api_key
@limiter.limit("10 per minute")
def import_from_excel():
    """
    Lê monitores.csv (raiz do projeto) e cria todos os monitores nele em paralelo.
    ---
    tags: [monitors]
    security: [{ApiKeyAuth: []}]
    responses:
      200: {description: Resumo do lote}
      400: {description: Erro lendo o CSV}
    """
    try:
        df = pd.read_csv("monitores.csv")
    except FileNotFoundError:
        return fail("Arquivo monitores.csv não encontrado!", status_code=404)
    except Exception as e:
        return fail(str(e), status_code=400)

    logger.info("Encontradas %d linhas no arquivo.", len(df))

    raw_monitors = []
    for _, row in df.iterrows():
        group_id = 0
        if "Cliente" in df.columns and pd.notna(row["Cliente"]):
            try:
                group_id = int(row["Cliente"])
            except (TypeError, ValueError):
                group_id = 0

        tags = []
        if "Ambiente" in df.columns and pd.notna(row["Ambiente"]):
            tags.append(str(row["Ambiente"]).strip())

        raw_monitors.append({
            "friendlyName": str(row["Nome"]).strip(),
            "url": str(row["Endpoint"]).strip(),
            "tagNames": tags,
            "groupId": group_id,
        })

    resultados = create_monitors_parallel(raw_monitors)
    sucessos = sum(1 for r in resultados if r["status"] == "success")

    return ok(
        total=len(raw_monitors),
        sucessos=sucessos,
        falhas=len(raw_monitors) - sucessos,
        detalhes=resultados,
    )


@monitors_bp.route("/monitors", methods=["GET"])
@require_api_key
def list_monitors():
    """
    Lista todos os monitores da conta (percorre todas as páginas).
    ---
    tags: [monitors]
    security: [{ApiKeyAuth: []}]
    responses:
      200: {description: Lista de monitores}
      502: {description: Falha ao consultar a UptimeRobot}
    """
    try:
        monitors = client.get_all_monitors()
    except HTTPError as e:
        status = e.response.status_code if e.response is not None else 502
        return fail(f"Erro ao buscar monitores: {e}", status_code=status)
    except Exception as e:
        return fail(str(e), status_code=500)

    formatted = [{
        "id": m.get("id"),
        "friendlyName": m.get("friendlyName"),
        "url": m.get("url"),
        "status": m.get("status"),
        "interval": m.get("interval"),
        "createDatetime": m.get("createDatetime"),
    } for m in monitors]

    return ok(total=len(monitors), monitors=formatted)


def _patch_region(monitor, regions):
    monitor_id = monitor.get("id")
    friendly_name = monitor.get("friendlyName")
    try:
        status_code, result = client.patch_monitor(monitor_id, {"regionData": {"REGION": regions}})
        if status_code == 200:
            return {"status": "success", "monitor_id": monitor_id, "friendlyName": friendly_name, "regions": regions}
        return {
            "status": "error",
            "monitor_id": monitor_id,
            "friendlyName": friendly_name,
            "status_code": status_code,
            "message": result,
        }
    except Exception as e:
        return {"status": "error", "monitor_id": monitor_id, "friendlyName": friendly_name, "message": str(e)}


@monitors_bp.route("/set-regions-all", methods=["POST"])
@require_api_key
@limiter.limit("5 per minute")
def set_regions_all():
    """
    Aplica as regiões (na, eu, as, oc por padrão) em TODOS os monitores via PATCH.
    ---
    tags: [monitors]
    security: [{ApiKeyAuth: []}]
    parameters:
      - in: body
        name: body
        required: false
        schema:
          type: object
          properties:
            regions: {type: array, items: {type: string}}
            dry_run: {type: boolean, default: false}
    responses:
      200: {description: Resumo da operação, ou preview se dry_run=true}
      400: {description: Regiões inválidas}
    """
    body = request.get_json(silent=True) or {}
    try:
        params = RegionsUpdateIn(**body)
    except ValidationError as e:
        return fail("Payload inválido.", errors=e.errors(include_url=False, include_context=False))

    try:
        monitors = client.get_all_monitors()
    except Exception as e:
        return fail(f"Falha ao listar monitores: {e}", status_code=500)

    logger.info("Encontrados %d monitores.", len(monitors))

    if params.dry_run:
        return ok(
            dry_run=True,
            total=len(monitors),
            regions_a_aplicar=params.regions,
            monitores=[{"id": m.get("id"), "friendlyName": m.get("friendlyName")} for m in monitors],
        )

    with ThreadPoolExecutor(max_workers=BULK_MAX_WORKERS) as pool:
        resultados = list(pool.map(lambda m: _patch_region(m, params.regions), monitors))

    sucessos = sum(1 for r in resultados if r["status"] == "success")

    return ok(
        total=len(monitors),
        sucessos=sucessos,
        falhas=len(monitors) - sucessos,
        regions_aplicadas=params.regions,
        detalhes=resultados,
    )
