from django.urls import path, include
from rest_framework.routers import DefaultRouter

from test_project.testapp.views import delete_logs, get_logs, get_landing_page, ArticleViewSet, ArticleViewSetWithMixin

router = DefaultRouter()
router.register(r"articles/mixin/", ArticleViewSet, basename="articles-mixin")
router.register(r"articles/no_mixin/", ArticleViewSetWithMixin, basename="articles-no-mixin")

app_name = "testapp"
urlpatterns = [
    path("delete-logs/", delete_logs, name="delete-logs"),
    path("get-logs/", get_logs, name="get-logs"),
    path("get-landing-page/", get_landing_page, name="get-landing-page"),
    *router.urls,
]
