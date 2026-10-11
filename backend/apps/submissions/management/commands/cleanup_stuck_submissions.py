"""清理僵尸提交：将 judging 超过 10 分钟的提交置为 system_error"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.judge.verdicts import Verdict
from apps.submissions.models import Submission


class Command(BaseCommand):
    help = "将长时间停留在 judging 状态的僵尸提交置为 system_error"

    def add_arguments(self, parser):
        parser.add_argument("--minutes", type=int, default=10, help="判定阈值（分钟）")

    def handle(self, *args, **options):
        threshold = timezone.now() - timedelta(minutes=options["minutes"])
        stuck = Submission.objects.filter(
            status=Verdict.JUDGING, created_at__lt=threshold
        )
        count = stuck.update(
            status=Verdict.SYSTEM_ERROR,
            error_message="judge timeout: submission stuck in judging",
            finished_at=timezone.now(),
        )
        self.stdout.write(self.style.SUCCESS(f"清理完成，共处理 {count} 条僵尸提交"))
