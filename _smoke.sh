#!/usr/bin/env bash
# Atlas 部署冒烟测试 (demo 模式)
set -u
WEB=http://127.0.0.1:8080
BACKEND=http://127.0.0.1:8000
echo "=== 1) 等待 web(nginx) 就绪 ==="
for i in $(seq 1 30); do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$WEB/" -m 3)
  [ "$code" = "200" ] && { echo "web / -> $code"; break; }
  sleep 2
done
echo "=== 2) 直接打 backend /health ==="
curl -s "$BACKEND/health" -m 5; echo
echo "=== 3) 直接打 backend /ready (查 DB+Qdrant+Redis) ==="
curl -s "$BACKEND/ready" -m 5; echo
echo "=== 4) 经 nginx /api/health 反代 ==="
curl -s "$WEB/api/health" -m 5; echo
echo "=== 5) 容器状态 ==="
docker compose ps
