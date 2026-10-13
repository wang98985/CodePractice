# 后端镜像：Django + Gunicorn（判题 worker 复用同一镜像）
# 构建上下文为仓库根目录，故路径以 backend/ 开头
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Shanghai

WORKDIR /app

# PyMySQL 为纯 Python 驱动，无需 mysql 客户端库与编译工具链
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt \
        -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY backend/ /app/
# 构建期收集静态文件，确保 WhiteNoise 在 gunicorn 启动前即可扫描到 STATIC_ROOT；
# 否则运行期再执行 collectstatic 需重启 backend 才会生效
RUN mkdir -p /app/staticfiles /tmp/oj_sandbox \
    && SECRET_KEY=build-only python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", \
     "-b", "0.0.0.0:8000", "-w", "2", "--timeout", "120", "--access-logfile", "-"]