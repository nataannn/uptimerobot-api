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
        "timeout": data.get("timeout", 30),
        "tagNames": data["tagNames"],
        "successHttpResponseCodes": data["successHttpResponseCodes"],
        "groupId": data.get("groupId", 0)
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
    
# Rota para o bulk_create
@app.route('/bulk-create', methods=['POST'])
def bulk_create():
    # Irá receber uma lista de monitores e criar eles automaticamente
    
    # Pega dados enviados no corpo da requisição em JSON
    monitors = request.get_json()
    
    # Validação
    if not monitors or not isinstance(monitors, list):
        return jsonify({
            "error": "Você deve enviar uma lista de monitors."
        }), 400
        
    # Variáveis para guardar resultados
    resultados = []
    sucessos = 0
    
    # Loop de execução para cada monitor da lista
    for monitor in monitors:
        
        # Payload
        payload = {
            "friendlyName": monitor["friendlyName"],
            "url": monitor["url"],
            "type": "http",
            "interval": monitor.get("interval", 300),
            "timeout": monitor.get("timeout", 30),
            "tagNames": monitor["tagNames"],
            "successHttpResponseCodes": monitor["successHttpResponseCodes"],
            "groupId": monitor.get("groupId", 0)   
        }
        
        # Headers
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Tentativa de criação do monitor
        try:
            response = requests.post(
                UPTIME_API_URL,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            result = response.json()
            
            if response.status_code == 201:
                resultados.append({
                    "status":"success",
                    "friendlyName": monitor["friendlyName"],
                    "monitor_id": result.get("id")
                })
                sucessos += 1
            else:
                resultados.append({
                    "status":"error",
                    "friendlyName":monitor["friendlyName"],
                    "message": result.get("error") or result.get("message")
                })
        except Exception as e:
            resultados.append({
                "status":"error",
                "friendlyName": monitor["friendlyName"],
                "message": str(e)
            })
    
    # Resumo da operação
    return jsonify({
        "status":"Finalizado.",
        "total": len(monitors),
        "sucessos": sucessos,
        "falhas": len(monitors) - sucessos,
        "detalhes": resultados
    }), 200
    
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