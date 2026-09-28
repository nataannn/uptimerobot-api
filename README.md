# UptimeRobot API

API em Flask para gerenciar monitors no UptimeRobot v3 (criação individual, em lote, importação via JSON/CSV e aplicação de regiões em massa).

Projeto desenvolvido como primeiro trabalho oficial como DevOps.

---

## Instalação

```
git clone https://github.com/nataannn/uptimerobot-api.git
cd uptimerobot-api
pip install -r requirements.txt
```

Para desenvolvimento (testes + lint), instale também:

```
pip install -r requirements-dev.txt
```

---

## Configuração

Crie o arquivo `.env` na raiz do projeto:

```
UPTIME_ROBOT_KEY=sua_chave_principal_do_uptimerobot
API_KEY_SECRET=sua_chave_secreta_da_api_aqui

# Opcionais
FLASK_DEBUG=false          # nunca true em produção
BULK_MAX_WORKERS=8         # paralelismo das rotas de lote (create/import/set-regions)
```

---

## Como rodar

Modo normal (dev, servidor do Flask):
```
python app.py
```

Modo Docker (produção, via gunicorn):
```
docker-compose up --build
```

A API fica em http://localhost:5000

Documentação interativa (Swagger UI) em http://localhost:5000/apidocs/

---

## Endpoints principais

Todas as rotas (exceto `/health`) exigem o header `X-API-KEY`.

| Rota | Método | Descrição |
|---|---|---|
| `/health` | GET | Healthcheck. Use `?deep=true` para validar a key contra a UptimeRobot de verdade. |
| `/create-monitor` | POST | Cria um monitor. |
| `/bulk-create` | POST | Cria uma lista de monitors em paralelo. |
| `/import-monitors` | GET | Lê `monitors.json` na raiz e cria todos em paralelo. |
| `/import-from-excel` | GET | Lê `monitores.csv` na raiz e cria todos em paralelo. |
| `/monitors` | GET | Lista todos os monitors (percorre todas as páginas). |
| `/monitors/export?format=csv\|json` | GET | Baixa todos os monitors como arquivo `.csv` ou `.json`. |
| `/set-regions-all` | POST | Aplica regiões (`na`, `eu`, `as`, `oc`) em todos os monitors. Aceita `dry_run: true`. |

Respostas seguem sempre o formato `{"status": "success" | "error", ...}`.

---

## Arquitetura

```
app.py                     # entrypoint: monta o Flask app e registra tudo
config.py                  # variáveis de ambiente e constantes
auth.py                    # autenticação via X-API-KEY
extensions.py              # logging estruturado, request_id, rate limiting
schemas.py                 # validação de entrada (Pydantic)
utils.py                   # envelope de resposta padronizado
services/uptimerobot_client.py   # cliente HTTP p/ UptimeRobot (pool + retry)
routes/monitors.py         # rotas de criação/listagem/importação
routes/health.py           # rota de healthcheck
tests/                     # suíte pytest
```

---

## Testes e lint

```
pytest
ruff check .
```

Rodam automaticamente no CI (GitHub Actions) a cada push/PR.

---

## Docker

Para parar:
```
docker-compose down
```

O container roda como usuário não-root, expõe um `HEALTHCHECK` nativo e usa `gunicorn` (não o servidor de desenvolvimento do Flask).

---

Feito por Natan - Abril 2026
