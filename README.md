# UptimeRobot API

API simples em Flask para criar monitors no UptimeRobot v3.

Projeto criado no primeiro dia como DevOps.

## Como instalar

1. Clone o repositório:
   git clone https://github.com/SEU_USUARIO/uptimerobot-api.git
   cd uptimerobot-api

2. Instale as dependências:
   pip install -r requirements.txt

## Configuração

Crie um arquivo chamado .env na pasta do projeto com este conteúdo:

UPTIME_ROBOT_KEY=sua_chave_muito_longa_aqui

## Como rodar

python app.py

A API vai ficar disponível em http://localhost:5000

## Endpoints

1. Testar se está funcionando:
   GET /health

2. Criar um monitor:
   POST /create-monitor

Exemplo de JSON para enviar:
{
  "friendly_name": "Teste Produção",
  "url": "https://google.com",
  "interval": 300
}

## Próximos passos

- Criar vários monitors de uma vez (bulk)
- Listar todos os monitors
- Docker

Feito por Natan - Abril 2026