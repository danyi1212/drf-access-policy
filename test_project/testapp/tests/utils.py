from typing import Optional

from django.contrib.auth.models import User, AnonymousUser
from rest_framework.fields import CharField
from rest_framework.serializers import Serializer

from rest_access_policy import AccessPolicy
from rest_access_policy.field_access_mixin import FieldAccessMixin


class FakeRequest(object):
    def __init__(self, user: Optional[User] = None, method: str = "GET"):
        self.user = user or AnonymousUser()
        self.method = method


class FakeViewSet(object):
    def __init__(self, action: str = "create"):
        self.action = action


class TestPolicy(AccessPolicy):
    not_a_func = ""

    def simple_condition(self, request, view, action):
        return True

    def false_condition(self, request, view, action):
        return False

    def non_boolean(self, request, view, action):
        return "Hi mom"

    def with_arg(self, request, view, action, arg):
        return True

    def with_error(self, request, view, action):
        raise ValueError("Condition Error")

    def is_true(self, request, view, action):
        return True

    def is_false(self, request, view, action):
        return False

    def is_cloudy(self, request, view, action):
        return True


class TestSerializer(FieldAccessMixin, Serializer):
    name = CharField()
    username = CharField()
    email = CharField()
    password = CharField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
