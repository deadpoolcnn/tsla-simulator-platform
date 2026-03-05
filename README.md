# TSLA Simulator Platform

前后端分离的期权回测平台

## 项目结构

```
.
├── backend/          # FastAPI 后端
├── frontend/         # React 前端
└── docker-compose.yml
```

## 快速启动

```bash
# 1. 启动所有服务
docker-compose up -d

# 2. 后端 API 文档
http://localhost:8000/docs

# 3. 前端页面
http://localhost:5173
```

## 开发模式

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```
