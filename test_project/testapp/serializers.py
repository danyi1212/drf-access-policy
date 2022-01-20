from rest_framework import serializers

from rest_access_policy.field_access_mixin import FieldAccessMixin
from test_project.testapp.access_policies import ArticleAccessPolicy
from test_project.testapp.models import Article


class ArticleSerializer(FieldAccessMixin, serializers.ModelSerializer):

    class Meta:
        model = Article
        fields = ("id", "title", "body", "author", "published_at", "published_by", "created", "modified")
        access_policy = ArticleAccessPolicy
