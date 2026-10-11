"""
判题沙箱执行器（Windows 本地版）。

安全措施：
- subprocess 子进程隔离执行，CREATE_NO_WINDOW
- 超时控制：communicate(timeout) 超时后 psutil 递归 kill 进程树
- 内存近似限制：psutil 每 50ms 采样进程树 RSS 峰值（Windows 无 resource.setrlimit）
- 输出截断：stdout 上限 MAX_OUTPUT_BYTES，防止超大输出拖垮内存
- 每次判题使用独立临时目录，判完删除

已知局限（MVP）：无 cgroup/namespace 隔离、未封锁网络与文件系统访问，
适合教学/内网场景；生产建议 Docker 沙箱。
"""
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import psutil
from django.conf import settings

from .languages import get_language

MAX_OUTPUT_BYTES = 64 * 1024  # stdout 截断上限 64KB
MAX_STDERR_BYTES = 8 * 1024  # stderr 存储上限 8KB
MEMORY_SAMPLE_INTERVAL = 0.05  # 50ms

_CREATIONFLAGS = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def kill_process_tree(pid):
    """递归终止进程树（Windows 无进程组语义，用 psutil 实现）"""
    try:
        parent = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return
    for child in parent.children(recursive=True):
        try:
            child.kill()
        except psutil.NoSuchProcess:
            pass
    try:
        parent.kill()
    except psutil.NoSuchProcess:
        pass


class MemorySampler(threading.Thread):
    """后台采样进程树 RSS 峰值（KB）"""

    def __init__(self, pid):
        super().__init__(daemon=True)
        self._pid = pid
        self._stop_event = threading.Event()
        self.peak_rss_kb = 0

    def run(self):
        while not self._stop_event.is_set():
            try:
                parent = psutil.Process(self._pid)
                procs = [parent, *parent.children(recursive=True)]
            except psutil.NoSuchProcess:
                break
            total = 0
            for p in procs:
                try:
                    total += p.memory_info().rss
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            self.peak_rss_kb = max(self.peak_rss_kb, total // 1024)
            if self._stop_event.wait(MEMORY_SAMPLE_INTERVAL):
                break

    def stop(self):
        self._stop_event.set()


class CompileResult:
    def __init__(self, ok, stderr=""):
        self.ok = ok
        self.stderr = stderr


class RunResult:
    def __init__(self, status, stdout="", stderr="", time_used_ms=0, memory_used_kb=0):
        self.status = status
        self.stdout = stdout
        self.stderr = stderr
        self.time_used_ms = time_used_ms
        self.memory_used_kb = memory_used_kb


def prepare_workdir(submission_id):
    workdir = Path(settings.SANDBOX_DIR) / str(submission_id)
    workdir.mkdir(parents=True, exist_ok=True)
    return workdir


def write_source(workdir, language_key, code):
    lang = get_language(language_key) or get_language("python")
    source_path = workdir / lang["source_filename"]
    source_path.write_text(code, encoding="utf-8")
    return source_path


def compile_check(language_key, source_path):
    """语法/编译预检；解释型语言用 py_compile"""
    lang = get_language(language_key) or get_language("python")
    try:
        if lang.get("compile_cmd"):
            cmd = [part.format(source_path=str(source_path), workdir=str(source_path.parent)) for part in lang["compile_cmd"]]
            proc = subprocess.run(
                cmd, capture_output=True, timeout=15, creationflags=_CREATIONFLAGS
            )
        elif lang.get("compile_check") == "py_compile":
            proc = subprocess.run(
                [sys.executable, "-m", "py_compile", str(source_path)],
                capture_output=True, timeout=15, creationflags=_CREATIONFLAGS,
            )
        else:
            return CompileResult(True)
    except subprocess.TimeoutExpired:
        return CompileResult(False, "compile timed out")
    except Exception as exc:  # noqa: BLE001
        return CompileResult(False, f"compile failed: {exc}")

    stderr = proc.stderr.decode("utf-8", errors="replace")[:MAX_STDERR_BYTES]
    return CompileResult(proc.returncode == 0, stderr)


def normalize_output(text):
    """对比前规范化：统一换行、去除行尾空白与末尾空行"""
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def run_single_case(language_key, source_path, input_data, time_limit_ms, memory_limit_kb):
    """执行单个测试用例，返回 RunResult"""
    lang = get_language(language_key) or get_language("python")
    limit_seconds = time_limit_ms / 1000.0
    cmd = [part.format(source_path=str(source_path), workdir=str(source_path.parent)) for part in lang["run_cmd"]]

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(source_path.parent),
        creationflags=_CREATIONFLAGS,
    )
    sampler = MemorySampler(proc.pid)
    sampler.start()

    timed_out = False
    started = time.monotonic()
    try:
        stdout, stderr = proc.communicate(
            input=input_data.encode("utf-8", errors="replace"), timeout=limit_seconds
        )
    except subprocess.TimeoutExpired:
        timed_out = True
        kill_process_tree(proc.pid)
        try:
            stdout, stderr = proc.communicate(timeout=5)
        except Exception:  # noqa: BLE001
            stdout, stderr = b"", b""
    elapsed_ms = int((time.monotonic() - started) * 1000)
    sampler.stop()
    sampler.join(timeout=1)

    stdout_text = stdout.decode("utf-8", errors="replace") if stdout else ""
    output_truncated = len(stdout or b"") > MAX_OUTPUT_BYTES
    stdout_text = stdout_text[:MAX_OUTPUT_BYTES]
    stderr_text = (stderr.decode("utf-8", errors="replace") if stderr else "")[:MAX_STDERR_BYTES]
    memory_used_kb = sampler.peak_rss_kb

    if timed_out:
        return RunResult("time_limit_exceeded", stdout_text, stderr_text, elapsed_ms, memory_used_kb)
    if memory_used_kb > memory_limit_kb:
        return RunResult("memory_limit_exceeded", stdout_text, stderr_text, elapsed_ms, memory_used_kb)
    if proc.returncode != 0:
        return RunResult("runtime_error", stdout_text, stderr_text, elapsed_ms, memory_used_kb)
    if output_truncated:
        # 输出超限视为错误输出
        return RunResult("wrong_answer", stdout_text, "output too large (>64KB)", elapsed_ms, memory_used_kb)
    return RunResult("ok", stdout_text, stderr_text, elapsed_ms, memory_used_kb)
