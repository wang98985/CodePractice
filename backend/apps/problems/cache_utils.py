"""题目列表缓存工具。

公开题目列表（/api/problems/）查询频繁但结果基本不变，用缓存避免高频查库。
失效策略：把版本号存在缓存里，任何写操作只需自增版本号，即可让所有旧缓存键
整体失效——无需按前缀批量删除（Django 原生 RedisCache 不支持 delete_pattern）。
"""
from django.core.cache import cache

# 缓存版本号（永不自动过期），任何写操作自增它即可让旧列表缓存全部作废
_LIST_VERSION_KEY = "problems:list:version"
# 列表缓存有效期（秒）
PROBLEM_LIST_CACHE_TTL = 300


def _list_version():
    return cache.get(_LIST_VERSION_KEY, 1)


def problem_list_cache_key(query_string):
    """按「版本号 + 原始查询串」生成缓存键，天然区分分页/筛选参数。"""
    return f"problems:list:v{_list_version()}:{query_string}"


def invalidate_problem_list_cache():
    """题目发生增删改后调用，令所有已缓存的列表结果失效。"""
    cache.set(_LIST_VERSION_KEY, _list_version() + 1, None)