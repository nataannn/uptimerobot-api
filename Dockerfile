# Dockerfile - UptimeRobot API

# Imagem oficial e leve do Python
FROM python:3.11-slim

# Diretório de trabalho
WORKDIR /app

# Cópia de requerimetos
COPY requirements.txt .

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o resto do código
COPY . .

# Expõe porta que API irá utilizar
EXPOSE 5000

# Comando que irá rodar quando o container iniciar
CMD ["python", "app.py"]