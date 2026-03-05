FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# 环境变量由 docker-compose.yml 通过 env_file / environment 注入，无需复制 .env
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
