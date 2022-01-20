from django.conf.urls import include
from django.urls import path


urlpatterns = [
    path("test_app/", include("test_project.testapp.urls"))
]
