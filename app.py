# Importações - trazendo as ferramentas necessárias
from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

# Carrega as variáveis do .env (ex: a API key)
load_dotenv()

# Criando a aplicação Flask
app = Flask(__name__) # Ligando "motor" da API

# Pegando a chave secreta do .env
API_KEY = os.getenv("UPTIME_ROBOT_KEY")

if not API_KEY:
    print("ERRO: Crie o arquivo .env com UPTIME_ROBOT_KEY")
    exit(1)

# Base URL API v3
UPTIME_API_URL = "https://api.uptimerobot.com/v3/monitors"


# Rota para criar o monitor
@app.route('/create-monitor', methods=['POST'])
def create_monitor():
    
    # Criando monitor usando a API do UptimeRobot v3 (RESTful)
    data = request.get_json()

    if not data or not data.get("friendlyName") or not data.get("url"):
        return jsonify({"error": "Os campos friendlyName e url são obrigatórios!"}), 400
    
    # Payload ( adicionar tags posteriormente '07/04/2026' )
    payload = {
        "friendlyName": data["friendlyName"],
        "url": data["url"],
        "type": "http",
        "interval": data.get("interval", 60),
        "timeout": data.get("timeout", 30)
    }

    # Headers
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "UptimeRobot-Flask-API/1.0"
    }

    try:
        response = requests.post(
            UPTIME_API_URL,
            json=payload,
            headers=headers,
            timeout=10
        )

        result = response.json()

        if response.status_code == 201:
            return jsonify({
                "status": "success",
                "message": "Monitor criado com sucesso.",
                "monitor_id": result.get("id"), 
                "friendlyName": data["friendlyName"]
            }), 201
        else:
            return jsonify({
                "status": "error",
                "message": result.get("error", result.get("message", "Erro desconhecido.")),
                "details": result
            }), response.status_code
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Rota de saúde
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "API rodando com UptimeRobot v3.",
        "version": "v3"
    })

# Inicia o servidor
if __name__ == '__main__':
    print("API Flask com UptimeRobot v3 iniciada em http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)