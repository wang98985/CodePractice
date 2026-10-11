import django_filters

from .models import Problem


class ProblemFilterSet(django_filters.FilterSet):
    difficulty = django_filters.CharFilter(field_name="difficulty")
    tag = django_filters.CharFilter(field_name="tags__name")

    class Meta:
        model = Problem
        fields = ["difficulty", "tag"]
