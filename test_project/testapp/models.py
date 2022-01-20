from django.contrib.auth import get_user_model
from django.db import models


class Article(models.Model):
    title = models.CharField(max_length=64)
    body = models.CharField(max_length=256)

    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="articles")
    published_at = models.DateTimeField(null=True, default=None)
    published_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, related_name="published_articles",
                                     null=True, default=None)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
