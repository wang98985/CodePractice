"""Celery 判题任务：从 RabbitMQ 消费 submission_id 并执行判题"""
import shutil

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.db import close_old_connections
from django.utils import timezone

from .languages import get_language
from .runner import (
    compile_check,
    normalize_output,
    prepare_workdir,
    run_single_case,
    write_source,
)
from .verdicts import TERMINAL_STATUSES, Verdict


def _judge(submission_id):
    from apps.submissions.models import Submission

    submission = (
        Submission.objects.select_related("problem").get(pk=submission_id)
    )
    problem = submission.problem

    submission.status = Verdict.JUDGING
    submission.total_cases = problem.test_cases.count()
    submission.save(update_fields=["status", "total_cases"])

    workdir = prepare_workdir(submission_id)
    try:
        lang = get_language(submission.language) or get_language("python")
        source_path = write_source(workdir, submission.language, submission.code)

        # ① 编译/语法预检
        compile_result = compile_check(submission.language, source_path)
        if not compile_result.ok:
            submission.status = Verdict.COMPILE_ERROR
            submission.error_message = compile_result.stderr
            submission.finished_at = timezone.now()
            submission.save(update_fields=["status", "error_message", "finished_at"])
            return

        # ② 逐用例执行（遇错即停）
        multiplier = lang.get("time_multiplier", 1)
        time_limit_ms = problem.time_limit_ms * multiplier
        passed = 0
        max_time = 0
        max_memory = 0
        final_status = Verdict.ACCEPTED
        error_message = ""

        for case in problem.test_cases.all():
            result = run_single_case(
                submission.language,
                source_path,
                case.input_data,
                time_limit_ms,
                problem.memory_limit_kb,
            )
            max_time = max(max_time, result.time_used_ms)
            max_memory = max(max_memory, result.memory_used_kb)

            if result.status == "ok":
                if normalize_output(result.stdout) == normalize_output(case.expected_output):
                    passed += 1
                    continue
                final_status = Verdict.WRONG_ANSWER
            else:
                final_status = {
                    "time_limit_exceeded": Verdict.TIME_LIMIT_EXCEEDED,
                    "memory_limit_exceeded": Verdict.MEMORY_LIMIT_EXCEEDED,
                    "runtime_error": Verdict.RUNTIME_ERROR,
                }.get(result.status, Verdict.SYSTEM_ERROR)
                error_message = result.stderr

            submission.passed_cases = passed
            submission.time_used_ms = max_time
            submission.memory_used_kb = max_memory
            submission.error_message = error_message
            submission.status = final_status
            submission.finished_at = timezone.now()
            submission.save(
                update_fields=[
                    "passed_cases", "time_used_ms", "memory_used_kb",
                    "error_message", "status", "finished_at",
                ]
            )
            return

        # ③ 全部通过
        submission.passed_cases = passed
        submission.time_used_ms = max_time
        submission.memory_used_kb = max_memory
        submission.status = Verdict.ACCEPTED
        submission.finished_at = timezone.now()
        submission.save(
            update_fields=[
                "passed_cases", "time_used_ms", "memory_used_kb",
                "status", "finished_at",
            ]
        )
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


@shared_task(bind=True, max_retries=1, name="judge.run_submission")
def run_submission(self, submission_id):
    close_old_connections()
    from apps.submissions.models import Submission

    try:
        _judge(submission_id)
    except Exception as exc:  # noqa: BLE001
        if self.request.retries < 1:
            try:
                raise self.retry(exc=exc, countdown=2)
            except MaxRetriesExceededError:
                pass
        submission = Submission.objects.filter(pk=submission_id).first()
        if submission and submission.status not in TERMINAL_STATUSES:
            submission.status = Verdict.SYSTEM_ERROR
            submission.error_message = f"judge crashed: {exc}"[:2000]
            submission.finished_at = timezone.now()
            submission.save(
                update_fields=["status", "error_message", "finished_at"]
            )
