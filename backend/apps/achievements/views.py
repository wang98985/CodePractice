from django.db.models import Count, Q
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.judge.verdicts import Verdict
from apps.submissions.models import Submission

from .models import ACHIEVEMENTS, UserAchievement


def compute_metrics(user):
    """一次性聚合用户的提交数据，得到各成就指标当前值"""
    stats = Submission.objects.filter(user=user).aggregate(
        ac_problems=Count(
            "problem_id", filter=Q(status=Verdict.ACCEPTED), distinct=True
        ),
        total_submissions=Count("id"),
        easy_ac=Count(
            "problem_id",
            filter=Q(status=Verdict.ACCEPTED, problem__difficulty="easy"),
            distinct=True,
        ),
        medium_ac=Count(
            "problem_id",
            filter=Q(status=Verdict.ACCEPTED, problem__difficulty="medium"),
            distinct=True,
        ),
        hard_ac=Count(
            "problem_id",
            filter=Q(status=Verdict.ACCEPTED, problem__difficulty="hard"),
            distinct=True,
        ),
    )
    return {key: stats[key] or 0 for key in stats}


class AchievementListView(APIView):
    """我的成就徽章

    GET /api/achievements/ →
    {
      "summary": {"unlocked": 2, "total": 8},
      "achievements": [
        {code, name, description, category, metric, target, current, unlocked, unlocked_at}
      ]
    }

    采用懒解锁：每次查询时按当前数据判断，达标即写入 UserAchievement（幂等）。
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        metrics = compute_metrics(user)
        unlocked = {a.code: a for a in UserAchievement.objects.filter(user=user)}

        items = []
        for spec in ACHIEVEMENTS:
            code = spec["code"]
            target = spec["target"]
            current = metrics.get(spec["metric"], 0)
            record = unlocked.get(code)
            if record is None and current >= target:
                record, _ = UserAchievement.objects.get_or_create(user=user, code=code)
                unlocked[code] = record
            items.append(
                {
                    "code": code,
                    "name": spec["name"],
                    "description": spec["description"],
                    "category": spec["category"],
                    "metric": spec["metric"],
                    "target": target,
                    "current": current,
                    "unlocked": record is not None,
                    "unlocked_at": record.unlocked_at if record else None,
                }
            )

        return Response(
            {
                "summary": {"unlocked": sum(1 for x in items if x["unlocked"]), "total": len(items)},
                "achievements": items,
            }
        )
