# UptimeRobot API

API em Flask para criar monitors no UptimeRobot v3.

Projeto desenvolvido como primeiro trabalho oficial como DevOps.

---

## Instalação

git clone https://github.com/SEU_USUARIO/uptimerobot-api.git
cd uptimerobot-api
pip install -r requirements.txt

---

## Configuração

Crie o arquivo .env na raiz do projeto:

UPTIME_ROBOT_KEY=sua_chave_principal_do_uptimerobot
API_KEY_SECRET=sua_chave_secreta_da_api_aqui

---

## Como rodar

Modo normal:
python app.py

Modo Docker:
docker-compose up --build

A API fica em http://localhost:5000

---

## Endpoints principais

Todas as rotas (exceto /health) precisam do header X-API-Key

- GET  /health
- POST /create-monitor
- POST /bulk-create
- GET  /import-monitors
- GET  /monitors

---

## Docker

Para parar:
docker-compose down

---

Feito por Natan - Abril 2026