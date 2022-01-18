from django.contrib.auth.models import Group, User
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase


class ViewsTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.admin_group = Group.objects.create(name="admin")
        cls.dev_group = Group.objects.create(name="dev")

        cls.user = User.objects.create(username="test_user")
        cls.dev_user = User.objects.create(username="test_dev")
        cls.dev_user.groups.add(cls.dev_group)
        cls.admin_user = User.objects.create(username="test_admin")
        cls.admin_user.groups.add(cls.admin_group)

    def test_admin_can_get_logs(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(reverse("testapp:get-logs"), format="json")
        self.assertEqual(response.status_code, 200)

    def test_admin_can_delete_logs(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(reverse("testapp:delete-logs"), format="json")
        self.assertEqual(response.status_code, 200)

    def test_dev_can_get_logs(self):
        self.client.force_authenticate(user=self.dev_user)
        response = self.client.get(reverse("testapp:get-logs"), format="json")
        self.assertEqual(response.status_code, 200)

    def test_dev_cannot_delete_logs(self):
        self.client.force_authenticate(user=self.dev_user)
        response = self.client.delete(reverse("testapp:delete-logs"), format="json")
        self.assertEqual(response.status_code, 403)

    def test_anonymous_user_can_view_landing_page(self):
        response = self.client.get(reverse("testapp:get-landing-page"), format="json")
        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_can_view_landing_page(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("testapp:get-landing-page"), format="json")
        self.assertEqual(response.status_code, 200)
