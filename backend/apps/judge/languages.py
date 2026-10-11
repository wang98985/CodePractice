"""
语言注册表：判题引擎支持的语言定义。
新增语言（如 C/C++/Java）只需在 LANGUAGE_REGISTRY 中补充条目：
- source_filename: 源码文件名
- compile_cmd:     编译命令（None 表示解释执行；占位符 {source_path} {workdir}）
- run_cmd:         运行命令（占位符 {source_path} {workdir}）
- compile_check:   解释型语言的语法预检方式（"py_compile"）
- time_multiplier: 时间限制放大系数（解释型语言建议 2）
"""
import sys

PYTHON = {
    "name": "Python 3",
    "source_filename": "main.py",
    "compile_cmd": None,
    "compile_check": "py_compile",
    "run_cmd": [sys.executable, "{source_path}"],
    "time_multiplier": 2,
}

LANGUAGE_REGISTRY = {
    "python": PYTHON,
    # ---- 预留扩展（未启用）----
    # "cpp": {
    #     "name": "C++17",
    #     "source_filename": "main.cpp",
    #     "compile_cmd": ["g++", "-O2", "-std=c++17", "{source_path}", "-o", "{workdir}\\main.exe"],
    #     "compile_check": None,
    #     "run_cmd": ["{workdir}\\main.exe"],
    #     "time_multiplier": 1,
    # },
    # "java": {
    #     "name": "Java 17",
    #     "source_filename": "Main.java",
    #     "compile_cmd": ["javac", "{source_path}"],
    #     "compile_check": None,
    #     "run_cmd": ["java", "-cp", "{workdir}", "Main"],
    #     "time_multiplier": 2,
    # },
}


def get_language(key):
    return LANGUAGE_REGISTRY.get(key)
