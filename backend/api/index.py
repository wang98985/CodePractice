# Vercel Python Serverless 入口
# Vercel Python runtime 会自动探测本文件中的 WSGI 可调用对象 `app` 并接管请求
import os
import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中（api/ 的上一级即 backend/）
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.core.wsgi import get_wsgi_application  # noqa: E402

app = get_wsgi_application()
