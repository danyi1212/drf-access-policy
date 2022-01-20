# pylint: disable=unused-argument
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from rest_access_policy import AccessViewSetMixin
from test_project.testapp.access_policies import ArticleAccessPolicy, LogsAccessPolicy, LandingPageAccessPolicy
from test_project.testapp.models import Article
from test_project.testapp.serializers import ArticleSerializer


class ArticleViewSetWithMixin(AccessViewSetMixin, viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    access_policy = ArticleAccessPolicy()

    def get_queryset(self):
        return self.access_policy.scope_queryset(self.request, super().get_queryset())

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        article = self.get_object()
        article.published_at = timezone.now()
        article.published_by = request.user
        article.save()
        return Response(self.get_serializer(article).data)


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = (ArticleAccessPolicy,)

    def get_queryset(self):
        return ArticleAccessPolicy.scope_queryset(self.request, super().get_queryset())

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        article = self.get_object()
        article.published_at = timezone.now()
        article.published_by = request.user
        article.save()
        return Response(self.get_serializer(article).data)


@api_view(["GET"])
@permission_classes((LogsAccessPolicy,))
def get_logs(request):
    return Response({"status": "OK"})


@api_view(["DELETE"])
@permission_classes((LogsAccessPolicy,))
def delete_logs(request):
    return Response({"status": "OK"})


@api_view(["GET"])
@permission_classes((LandingPageAccessPolicy,))
def get_landing_page(request):
    return Response({"status": "OK"})
