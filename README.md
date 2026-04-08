# UptimeRobot API

API simples em Flask para criar e gerenciar monitors no UptimeRobot v3.

Projeto desenvolvido como primeiro trabalho oficial como DevOps.

---

## Instalação

1. Clone o repositório:
   git clone https://github.com/SEU_USUARIO/uptimerobot-api.git
   cd uptimerobot-api

2. Instale as dependências:
   pip install -r requirements.txt

---

## Configuração

Crie um arquivo chamado `.env` na raiz do projeto com o seguinte conteúdo:

UPTIME_ROBOT_KEY=sua_chave_principal_do_uptimerobot
API_KEY_SECRET=sua_chave_secreta_da_api_aqui

---

## Como rodar

python app.py

A API vai ficar disponível em http://localhost:5000

---

## Endpoints

Todas as rotas (exceto /health) precisam do header:
X-API-Key: sua_chave_secreta_da_api_aqui

- GET  /health                  → Teste se a API está rodando
- POST /create-monitor          → Cria um único monitor
- POST /bulk-create             → Cria vários monitors de uma vez
- GET  /import-monitors         → Lê o arquivo monitors.json e cria todos
- GET  /monitors                → Lista todos os monitors da conta

---

## Como usar o monitors.json

Crie o arquivo `monitors.json` na raiz do projeto e coloque os endpoints que deseja monitorar.

Depois basta chamar a rota GET /import-monitors.

---

Feito por Natan - Abril 2026