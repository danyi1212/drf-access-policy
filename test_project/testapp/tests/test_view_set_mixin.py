from typing import List

from django.test import TestCase
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.viewsets import ViewSet

from rest_access_policy import AccessViewSetMixin, AccessPolicy
from test_project.testapp.tests.utils import TestPolicy


class AccessViewSetTests(TestCase):

    def assert_permissions(self, first: List[BasePermission], second: List[BasePermission]):
        self.assertEqual([type(x) for x in first], [type(x) for x in second])
        self.assertTrue(any(isinstance(x, BasePermission) for x in first))
        self.assertTrue(any(isinstance(x, BasePermission) for x in second))

    def test_access_policy_as_class(self):
        class MyViewSet(AccessViewSetMixin, ViewSet):
            access_policy = AccessPolicy

        view = MyViewSet()
        self.assert_permissions(view.get_permissions(), [AccessPolicy(), AllowAny()])

    def test_access_policy_as_subclass(self):
        class MyViewSet(AccessViewSetMixin, ViewSet):
            access_policy = TestPolicy

        view = MyViewSet()
        self.assert_permissions(view.get_permissions(), [TestPolicy(), AllowAny()])

    def test_access_policy_as_object(self):
        class MyViewSet(AccessViewSetMixin, ViewSet):
            access_policy = TestPolicy()

        view = MyViewSet()
        self.assert_permissions(view.get_permissions(), [TestPolicy(), AllowAny()])

    def test_without_access_policy(self):
        class MyViewSet(AccessViewSetMixin, ViewSet):
            pass

        with self.assertRaises(ValueError) as context:
            MyViewSet()

        self.assertEqual("MyViewSet.access_policy must be an AccessPolicy or subclass", str(context.exception))

    def test_access_policy_as_none(self):
        class MyViewSet(AccessViewSetMixin, ViewSet):
            access_policy = None

        with self.assertRaises(ValueError) as context:
            MyViewSet()

        self.assertEqual("MyViewSet.access_policy must be an AccessPolicy or subclass", str(context.exception))

    def test_access_policy_incorrect_type(self):
        class MyViewSet(AccessViewSetMixin, ViewSet):
            access_policy = "hello world"

        with self.assertRaises(ValueError) as context:
            MyViewSet()

        self.assertEqual("MyViewSet.access_policy must be an AccessPolicy or subclass", str(context.exception))

    def test_permission_classes_not_modified(self):
        class MyViewSet(AccessViewSetMixin, ViewSet):
            access_policy = AccessPolicy

        view = MyViewSet()
        self.assertEqual(view.permission_classes, [AllowAny])
        self.assertEqual(MyViewSet.permission_classes, [AllowAny])

    def test_permission_classes_access_policy_as_class(self):
        class MyViewSet(ViewSet):
            permission_classes = [AccessPolicy]

        view = MyViewSet()
        self.assert_permissions(view.get_permissions(), [AccessPolicy()])

    def test_permission_classes_access_policy_as_subclass(self):
        class MyViewSet(ViewSet):
            permission_classes = [TestPolicy]

        view = MyViewSet()
        self.assert_permissions(view.get_permissions(), [TestPolicy()])

    def test_permission_classes_access_policy_as_object(self):
        class MyViewSet(ViewSet):
            permission_classes = [AccessPolicy()]

        view = MyViewSet()
        self.assert_permissions(view.get_permissions(), [AccessPolicy()])
