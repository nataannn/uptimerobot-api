# Importações - trazendo as ferramentas necessárias
from flask import Flask, request, jsonify
import requests
import os
import json
import pandas as pd
from functools import wraps
from dotenv import load_dotenv

# Carrega as variáveis do .env (ex: a API key)
load_dotenv()

# Criando a aplicação Flask
app = Flask(__name__) # Ligando "motor" da API

# Pegando as chaves do env.
API_KEY = os.getenv("UPTIME_ROBOT_KEY")
API_KEY_SECRET = os.getenv("API_KEY_SECRET")

if not API_KEY:
    print("ERRO: Não encontrado UPTIME_ROBOT_KEY no .env")
    exit(1)
    
if not API_KEY_SECRET:
    print("ERRO: Não encontrado API_KEY_SECRET no .env")
    
# Função de autenticação
def require_api_key(f):
    # Função que verifica se o usuário usou a chave correta no header
    @wraps(f)
    def decorated(*args, **kwargs):
        # Pega o header X-API-KEY que o usuário enviou
        api_key_received = request.headers.get('X-API-KEY')
        
        if not api_key_received or api_key_received != API_KEY_SECRET:
            return jsonify({
                "error": "Acesso negado! Chave API inválida ou ausente.",
                "message": "Envie o header X-API-KEY com a chave correta."
            }), 401
            
        # Se a chave estiver certa, continua executando a rota normalmente
        return f(*args, **kwargs)
    return decorated

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
        "interval": data.get("interval", 300),
        "timeout": data.get("timeout", 30),
        "tagNames": data.get("tagNames", []),
        "successHttpResponseCodes": data.get("successHttpResponseCodes", ["2xx,3xx"]),
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
@require_api_key

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
            "tagNames": monitor.get("tagNames", []),
            "successHttpResponseCodes": monitor.get("successHttpResponseCodes", ["2xx, 3xx"]),
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

# Rota para importar monitores - lendo monitors.json e criando-os
@app.route('/import-monitors', methods=['GET'])
@require_api_key

def import_monitors():
    # Função irá ler o arquivo monitors.json e criará todos de uma vez.
    try:
        # Leitura
        with open('monitors.json', 'r', encoding='utf-8') as file:
            monitors = json.load(file)
            
        print(f"Encontrados {len(monitors)} monitors no arquivo.")
        
        # Reutilização da lógica do bulk-create
        resultados = []
        sucessos = 0
        
        for monitor in monitors:
            payload = {
                "friendlyName": monitor["friendlyName"],
                "url": monitor["url"],
                "type": "http",
                "interval": monitor.get("interval", 300),
                "timeout": monitor.get("timeout", 30),
                "tagNames": monitor.get("tagNames", []),
                "successHttpResponseCodes": monitor.get("successHttpResponseCodes", ["2xx", "3xx"]),
                "groupId": monitor.get("groupId", 0)
            }
            
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
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
                    resultados.append({
                        "status": "success",
                        "friendlyName": monitor['friendlyName'],
                        "monitor_id": result.get("id")
                    })
                    sucessos += 1
                else:
                    resultados.append({
                        "status": "error",
                        "friendlyName": monitor['friendlyName'],
                        "message": result.get("error") or result.get("message") or str(result)
                    })
            except Exception as e:
                resultados.append({
                    "status": "error",
                    "friendlyName": monitor['friendlyName'],
                    "message": str(e)
                })
        
        # Retornando resumo final
        return jsonify({
            "status": "finalizado",
            "total": len(monitors),
            "sucessos": sucessos,
            "falhas": len(monitors) - sucessos,
            "detalhes": resultados
        })

    except FileNotFoundError:
        return jsonify({
            "error": "Arquivo monitors.json não encontrado!"
        }), 404
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

# Rota de listagem dos monitores
@app.route('/monitors', methods=['GET'])
@require_api_key

def list_monitors():
    # Retornará todos os monitors cadastrados no UptimeRobot.
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(
            "https://api.uptimerobot.com/v3/monitors",
            headers=headers,
            timeout=15
        )
        
        result = response.json()

        if response.status_code == 200:
            monitors = result.get("data", [])
            
            formatted_monitors = []
            for monitor in monitors:
                formatted_monitors.append({
                    "id": monitor.get("id"),
                    "friendlyName": monitor.get("friendlyName"),
                    "url": monitor.get("url"),
                    "status": monitor.get("status"),
                    "interval": monitor.get("interval"),
                    "createDatetime": monitor.get("createDatetime")
                })
                
            return jsonify({
                "status": "success",
                "total": len(monitors),
                "monitors": formatted_monitors
            })
        else:
            return jsonify({
                "status":"error",
                "message": result.get("error") or result.get("message") or "Erro ao buscar monitores."
            }), response.status_code
        
    except Exception as e:
        return jsonify({
            "status":"error",
            "message":str(e)
        }), 500

# Rota para ler planilhas do excel e criar os monitors
@app.route('/import-from-excel', methods=['GET'])
@require_api_key
def import_from_excel():
    try:
        df = pd.read_csv('monitores.csv')

        print(f"Encontradas {len(df)} linhas no arquivo.")

        resultados = []
        sucessos = 0

        for index, row in df.iterrows():
            friendly_name = str(row['Nome']).strip()
            url = str(row['Endpoint']).strip()

            group_id = 0
            if 'Cliente' in df.columns and pd.notna(row['Cliente']):
                try:
                    group_id = int(row['Cliente'])
                except:
                    group_id = 0
            
            tags = []
            if 'Ambiente' in df.columns and pd.notna(row['Ambiente']):
                tags.append(str(row['Ambiente']).strip())

            payload = {
                "friendlyName": friendly_name,
                "url": url,
                "type": "http",
                "interval": 300,
                "timeout": 30,
                "successHttpResponseCodes": ["2xx", "3xx"],
                "tagNames": tags,
                "groupId": group_id
            }

            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }

            try:
                response = requests.post(
                    UPTIME_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=15
                )

                # === MELHORIA: Verifica se a resposta é JSON válido ===
                if response.status_code == 201:
                    result = response.json()
                    resultados.append({
                        "status": "success",
                        "friendlyName": friendly_name,
                        "monitor_id": result.get("id")
                    })
                    sucessos += 1
                else:
                    # Tenta pegar o erro real
                    try:
                        error_detail = response.json()
                    except:
                        error_detail = response.text[:500]  # mostra os primeiros 500 caracteres
                    resultados.append({
                        "status": "error",
                        "friendlyName": friendly_name,
                        "status_code": response.status_code,
                        "message": error_detail
                    })

            except Exception as e:
                resultados.append({
                    "status": "error",
                    "friendlyName": friendly_name,
                    "message": str(e)
                })

        return jsonify({
            "status": "finalizado",
            "total": len(df),
            "sucessos": sucessos,
            "falhas": len(df) - sucessos,
            "detalhes": resultados
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
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