from django.db.models import Q

from rest_access_policy import AccessPolicy


class ArticleAccessPolicy(AccessPolicy):
    statements = [
        {"principal": "*", "action": "<safe_methods>"},
        {"principal": "group:editors", "action": "publish", "effect": "allow"},
        {"principal": "authenticated", "action": "*", "condition": "user_must_be:author", "effect": "allow"},
        {"principal": "admin", "action": "*", "effect": "allow"},
    ]
    field_permissions = {
        "read_only": [
            {"principal": "*", "fields": ["author", "published_at", "published_by", "created", "modified"]},
            {"principal": "admin", "fields": "published_by", "effect": "allow"},
        ],
    }

    @classmethod
    def scope_queryset(cls, request, qs):
        if not request.user.is_authenticated:
            return qs.filter(published_at__isnull=False)
        elif not request.user.groups.filter(name="editors").exists():
            return qs.filter(Q(author=request.user) | Q(published_at__isnull=False))
        else:
            return qs


class LogsAccessPolicy(AccessPolicy):
    statements = [
        {"principal": "group:admin", "action": "*", "effect": "allow"},
        {"principal": "group:dev", "action": "get_logs", "effect": "allow"},
        {"principal": "group:dev", "action": "delete_logs", "effect": "deny"},
    ]


class LandingPageAccessPolicy(AccessPolicy):
    statements = [
        {"principal": ["anonymous", "authenticated"], "action": "*", "effect": "allow"},
    ]
