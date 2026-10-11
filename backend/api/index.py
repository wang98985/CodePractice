# Vercel Python Serverless 入口：把 Django WSGI app 适配到 Vercel runtime
import os
import sys
from io import BytesIO
from pathlib import Path

# 确保项目根目录在 sys.path 中
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402
django.setup()

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()


def handler(request):
    """Vercel Python runtime 入口：request -> Django -> response"""
    method = request.method or "GET"
    path = request.path or "/"
    headers = request.headers or {}

    # 构建 WSGI environ
    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path.split("?")[0],
        "QUERY_STRING": path.split("?", 1)[1] if "?" in path else "",
        "SERVER_NAME": headers.get("host", "localhost"),
        "SERVER_PORT": "443",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "wsgi.version": (1, 0),
        "wsgi.url_scheme": headers.get("x-forwarded-proto", "https"),
        "wsgi.input": BytesIO(request.body or b""),
        "wsgi.errors": sys.stderr,
        "wsgi.multithread": False,
        "wsgi.multiprocess": False,
        "wsgi.run_once": False,
    }

    # 把 HTTP 头加入 environ
    content_length = None
    for key, value in headers.items():
        key_upper = key.upper().replace("-", "_")
        if key_upper == "CONTENT_LENGTH":
            content_length = value
            environ["CONTENT_LENGTH"] = value
        elif key_upper == "CONTENT_TYPE":
            environ["CONTENT_TYPE"] = value
        else:
            environ[f"HTTP_{key_upper}"] = value

    if content_length is None:
        body = request.body or b""
        environ["CONTENT_LENGTH"] = str(len(body))

    # 调用 Django WSGI
    status_line = []
    response_headers = []
    exc_info = []

    def start_response(status, headers, exc_info_=None):
        status_line.append(status)
        response_headers.extend(headers)
        if exc_info_:
            exc_info.append(exc_info_)

    body_iter = application(environ, start_response)
    body = b"".join(body_iter)

    # 解析状态码
    status_code = int(status_line[0].split(" ", 1)[0]) if status_line else 500

    # 构建 Vercel response
    resp_headers = {}
    for h_key, h_val in response_headers:
        if h_key.lower() in ("content-encoding", "transfer-encoding", "connection"):
            continue  # Vercel 会处理这些
        resp_headers[h_key] = h_val

    return {
        "status": status_code,
        "headers": resp_headers,
        "body": body,
    }
