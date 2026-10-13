#!/usr/bin/env bash
# 一键部署 / 运维脚本（在服务器 deploy/ 目录下执行）
# 用法：
#   ./deploy.sh up          构建并启动全部服务
#   ./deploy.sh migrate     执行数据库迁移
#   ./deploy.sh collect     收集 Django 静态文件
#   ./deploy.sh superuser   创建超级管理员（admin / admin123456）
#   ./deploy.sh ps          查看容器状态
#   ./deploy.sh logs [svc]  查看日志
#   ./deploy.sh restart     重启全部服务
#   ./deploy.sh down        停止并移除容器（保留数据卷）
set -euo pipefail
cd "$(dirname "$0")"

COMPOSE="docker compose -f docker-compose.prod.yml --env-file .env.prod"

case "${1:-up}" in
  up)        $COMPOSE up -d --build ;;
  migrate)   $COMPOSE exec -T backend python manage.py migrate ;;
  collect)   $COMPOSE exec -T backend python manage.py collectstatic --noinput
             # WhiteNoise 在进程启动时扫描 STATIC_ROOT，运行期收集后需重启 backend 才生效
             docker restart oj-backend >/dev/null && echo "已重启 backend" ;;
  superuser)
    $COMPOSE exec -T -e DJANGO_SUPERUSER_PASSWORD="${2:-admin123456}" backend \
      python manage.py createsuperuser --noinput --username "${3:-admin}" --email "${4:-admin@example.com}"
    ;;
  shell)     $COMPOSE exec backend python manage.py shell ;;
  ps)        $COMPOSE ps ;;
  logs)      $COMPOSE logs -f --tail=100 ${2:-} ;;
  restart)   $COMPOSE restart ;;
  down)      $COMPOSE down ;;
  *)         sed -n '2,14p' "$0" ;;
esac