#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "=== 企业融资智能获客系统 一键启动 ==="

# 后端
echo "[1/2] 启动后端 (FastAPI :8001)..."
cd "$ROOT/backend"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 &
BACKEND_PID=$!
echo "  后端 PID: $BACKEND_PID"

# 前端
echo "[2/2] 启动前端 (Next.js :3000)..."
cd "$ROOT/frontend"
npm install --silent 2>/dev/null
npm run dev -- -p 3000 &
FRONTEND_PID=$!
echo "  前端 PID: $FRONTEND_PID"

echo ""
echo "=== 启动完成 ==="
echo "前端: http://localhost:3000"
echo "后端: http://localhost:8001/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
