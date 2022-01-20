from functools import wraps
from typing import List

from django.contrib.auth.models import Group, User
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from test_project.testapp.models import Article


def for_each_view():
    def decorator(test_func):
        @wraps(test_func)
        def wrapper(self: "ArticleViewSetTests"):
            for view_path in self.views_path:
                with self.subTest(view=view_path):
                    test_func(self, view_path)

        return wrapper

    return decorator


@override_settings(DRF_ACCESS_POLICY={"reusable_conditions": "test_project.global_access_conditions"})
class ArticleViewSetTests(APITestCase):
    views_path = ["testapp:articles-mixin", "testapp:articles-no-mixin"]

    @classmethod
    def setUpTestData(cls):
        cls.editors_group = Group.objects.create(name="editors")
        cls.user = User.objects.create(username="test_user")
        cls.editor = User.objects.create(username="test_editor")
        cls.editor.groups.add(cls.editors_group)
        cls.admin = User.objects.create(username="test_admin", is_superuser=True)
        cls.admin.groups.add(cls.editors_group)

        cls.articles: List[Article] = Article.objects.bulk_create(
            Article(author=user, title=f"Article #{user.pk}{i}", body="Hello World!")
            for i in range(10)
            for user in [cls.user, cls.editor, cls.admin]
        )
        Article.objects.filter(author=cls.editor).update(published_by=cls.editor, published_at=timezone.now())

    @for_each_view()
    def test_create_as_anonymous(self, view_path):
        response = self.client.post(reverse(f"{view_path}-list"), {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, msg=response.data)

    @for_each_view()
    def test_list_as_anonymous(self, view_path):
        # Tests scope_query
        response = self.client.get(reverse(f"{view_path}-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(len(response.data), 10)

    @for_each_view()
    def test_list_as_user(self, view_path):
        # Tests scope_query
        self.client.force_login(self.user)
        response = self.client.get(reverse(f"{view_path}-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(len(response.data), 20)

    @for_each_view()
    def test_list_as_editor(self, view_path):
        # Tests scope_query
        self.client.force_login(self.editor)
        response = self.client.get(reverse(f"{view_path}-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(len(response.data), 30)

    @for_each_view()
    def test_edit_as_user(self, view_path):
        self.client.force_login(self.user)
        response = self.client.patch(reverse(f"{view_path}-detail", kwargs=dict(pk=2)), {"title": "Hi mom."})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, msg=response)

    @for_each_view()
    def test_edit_as_author(self, view_path):
        self.client.force_login(self.user)
        response = self.client.patch(reverse(f"{view_path}-detail", kwargs=dict(pk=1)), {"title": "Hi mom."})
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response)

    @for_each_view()
    def test_edit_as_editor(self, view_path):
        self.client.force_login(self.editor)
        response = self.client.patch(reverse(f"{view_path}-detail", kwargs=dict(pk=1)), {"title": "Hi mom."})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, msg=response.data)

    @for_each_view()
    def test_publish_as_user(self, view_path):
        self.client.force_login(self.user)
        response = self.client.post(reverse(f"{view_path}-publish", kwargs=dict(pk=2)), {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, msg=response)

    @for_each_view()
    def test_publish_as_author(self, view_path):
        self.client.force_login(self.user)
        response = self.client.post(reverse(f"{view_path}-publish", kwargs=dict(pk=1)), {})
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response)

    @for_each_view()
    def test_publish_as_editor(self, view_path):
        self.client.force_login(self.editor)
        response = self.client.post(reverse(f"{view_path}-publish", kwargs=dict(pk=1)), {})
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

    @for_each_view()
    def test_create_article(self, view_path):
        self.client.force_login(self.user)
        response = self.client.post(reverse(f"{view_path}-list"), {
            "title": "My Article",
            "body": "Hello World!",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, msg=response.data)

    @for_each_view()
    def test_create_article_read_only_fields(self, view_path):
        self.client.force_login(self.editor)
        response = self.client.post(reverse(f"{view_path}-list"), {
            "title": "My Article",
            "body": "Hello World!",
            "published_by": self.user.pk,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, msg=response.data)
        self.assertNotEqual(response.data.get("published_by"), self.user.pk)
        self.assertEqual(response.data.get("published_by"), None)

    @for_each_view()
    def test_create_article_read_only_fields_admin(self, view_path):
        self.client.force_login(self.admin)
        response = self.client.post(reverse(f"{view_path}-list"), {
            "title": "My Article",
            "body": "Hello World!",
            "published_by": self.user.pk,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, msg=response.data)
        self.assertEqual(response.data.get("published_by"), self.user.pk)
        self.assertNotEqual(response.data.get("published_by"), None)
