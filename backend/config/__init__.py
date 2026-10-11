import pymysql

# PyMySQL 伪装为 MySQLdb，通过 Django 的 mysqlclient 版本检测
pymysql.version_info = (1, 4, 6, "final", 0)
pymysql.install_as_MySQLdb()

from .celery import app as celery_app  # noqa: E402, F401

__all__ = ("celery_app",)
