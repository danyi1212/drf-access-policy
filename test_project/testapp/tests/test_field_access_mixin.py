# pylint: disable=protected-access
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.fields import IntegerField
from rest_framework.serializers import Serializer, ModelSerializer

from rest_access_policy import AccessPolicy
from rest_access_policy.field_access_mixin import FieldAccessMixin
from rest_access_policy.statements import FieldStatement
from test_project.testapp.models import Article
from test_project.testapp.tests.utils import TestPolicy, FakeRequest, TestSerializer


class FieldAccessMixinTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="test_user")
        cls.request = FakeRequest(cls.user)

    def test_meta_access_policy_as_class(self):
        class MySerializer(FieldAccessMixin, Serializer):
            class Meta:
                access_policy = AccessPolicy

        serializer = MySerializer()
        self.assertTrue(isinstance(serializer.access_policy, AccessPolicy))

    def test_meta_access_policy_as_subclass(self):
        class MySerializer(FieldAccessMixin, Serializer):
            class Meta:
                access_policy = TestPolicy

        serializer = MySerializer()
        self.assertTrue(isinstance(serializer.access_policy, AccessPolicy))

    def test_meta_access_policy_as_object(self):
        class MySerializer(FieldAccessMixin, Serializer):
            class Meta:
                access_policy = AccessPolicy()

        serializer = MySerializer()
        self.assertTrue(isinstance(serializer.access_policy, AccessPolicy))

    def test_meta_access_policy_as_none(self):
        class MySerializer(FieldAccessMixin, Serializer):
            class Meta:
                access_policy = None

        with self.assertRaises(ValueError) as context:
            MySerializer()

        self.assertEqual("Must set Meta.access_policy for FieldAccessMixin", str(context.exception),)

    def test_meta_access_policy_invalid_type(self):
        class MySerializer(FieldAccessMixin, Serializer):
            class Meta:
                access_policy = "hello world"

        with self.assertRaises(ValueError) as context:
            MySerializer()

        self.assertEqual("MySerializer.Meta.access_policy must be an AccessPolicy or subclass", str(context.exception),)

    def test_meta_access_policy_missing(self):
        class MySerializer(FieldAccessMixin, Serializer):
            pass

        with self.assertRaises(ValueError) as context:
            MySerializer()

        self.assertEqual("Must set Meta.access_policy for FieldAccessMixin", str(context.exception))

    def test_policy_field_permissions_missing_request_context(self):
        class MySerializer(FieldAccessMixin, Serializer):
            class Meta:
                access_policy = AccessPolicy(field_permissions={
                    "read_only": [
                        {"principal": "*", "fields": "*"},
                    ],
                })

        with self.assertRaises(KeyError) as context:
            MySerializer()

        self.assertEqual(
            "'Unable to find request in serializer context on MySerializer (required for FieldAccessMixin)'",
            str(context.exception),
        )

    def test_policy_field_permissions_empty_request_context(self):
        class MySerializer(FieldAccessMixin, Serializer):
            class Meta:
                access_policy = AccessPolicy(field_permissions={
                    "read_only": [
                        {"principal": "*", "fields": "*"},
                    ],
                })

        with self.assertRaises(KeyError) as context:
            MySerializer(context={"request": None})

        self.assertEqual(
            "'Unable to find request in serializer context on MySerializer (required for FieldAccessMixin)'",
            str(context.exception),
        )

    def test_policy_field_permissions_statements(self):
        class MyPolicy(AccessPolicy):
            field_permissions = {"read_only": [
                FieldStatement(principal="group:admin", fields="*", effect="allow"),
            ]}

        class MySerializer(FieldAccessMixin, Serializer):
            class Meta:
                access_policy = AccessPolicy(field_permissions={
                    "read_only": [
                        {"principal": "*", "fields": "*"},
                        FieldStatement(principal="test_principal", fields="test_field"),
                        AccessPolicy(field_permissions={"read_only": [
                            {"principal": "other_policy", "fields": "*"},
                        ]}),
                        MyPolicy,
                    ],
                })

        serializer = MySerializer(context={"request": self.request})
        statements = serializer._get_statements("read_only")
        self.assertEqual(
            list(statements),
            [
                FieldStatement(principal="*", fields="*"),
                FieldStatement(principal="test_principal", fields="test_field"),
                FieldStatement(principal="other_policy", fields="*"),
                FieldStatement(principal="group:admin", fields="*", effect="allow"),
            ],
        )

    def test_policy_field_permissions_statements_incorrect_type(self):
        class MySerializer(FieldAccessMixin, Serializer):
            class Meta:
                access_policy = AccessPolicy(field_permissions={
                    "read_only": [
                        {"*"},
                    ],
                })

        with self.assertRaises(ValueError) as context:
            MySerializer(context={"request": self.request})

        self.assertTrue("Invalid field permissions statement" in str(context.exception))
        self.assertTrue("set" in str(context.exception))
        self.assertTrue("AccessPolicy" in str(context.exception))
        self.assertTrue("read_only" in str(context.exception))
        self.assertTrue("index 0" in str(context.exception))


class FieldAccessMixinFieldsTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="test_user")
        cls.admin = User.objects.create_user(username="test_admin", is_superuser=True)

    def test_default_effect_combine(self):
        class MySerializer(TestSerializer):
            class Meta:
                access_policy = AccessPolicy(field_permissions={
                    "read_only": [
                        {"principal": "*", "fields": "password"},
                        {'principal': "anonymous", 'fields': ["name", "username"]},
                    ],
                })

        serializer = MySerializer(context={"request": FakeRequest()})
        fields = serializer._get_fields_from_statements("read_only")
        field_names = {f.field_name for f in fields}
        self.assertEqual(field_names, {"password", "name", "username"})

    def test_allow_effect_skipped(self):
        class MySerializer(TestSerializer):
            class Meta:
                access_policy = AccessPolicy(field_permissions={
                    "read_only": [
                        {"principal": "*", "fields": ["name", "username"]},
                        {"principal": "authenticated", "fields": "name", "effect": "allow"},
                    ],
                })

        serializer = MySerializer(context={"request": FakeRequest(self.user)})
        fields = serializer._get_fields_from_statements("read_only")
        field_names = {f.field_name for f in fields}
        self.assertEqual(field_names, {"username"})

    def test_deny_effect_remains(self):
        class MySerializer(TestSerializer):
            class Meta:
                access_policy = AccessPolicy(field_permissions={
                    "read_only": [
                        {"principal": "*", "fields": ["name", "username"]},
                        {"principal": "authenticated", "fields": "name", "effect": "deny"},
                        {"principal": "admin", "fields": "*", "effect": "allow"},
                    ],
                })

        serializer = MySerializer(context={"request": FakeRequest(self.admin)})
        fields = serializer._get_fields_from_statements("read_only")
        field_names = {f.field_name for f in fields}
        self.assertEqual(field_names, {"name"})

    def test_default_effect_all(self):
        class MySerializer(TestSerializer):
            class Meta:
                access_policy = AccessPolicy(field_permissions={
                    "read_only": [
                        {"principal": "*", "fields": "*"},
                    ],
                })

        serializer = MySerializer(context={"request": FakeRequest()})
        fields = serializer._get_fields_from_statements("read_only")
        field_names = {f.field_name for f in fields}
        self.assertEqual(field_names, {"username", "name", "email", "password"})

    def test_allow_effect_all(self):
        class MySerializer(TestSerializer):
            class Meta:
                access_policy = AccessPolicy(field_permissions={
                    "read_only": [
                        {"principal": "*", "fields": ["username", "name"]},
                        {"principal": "authenticated", "fields": "*", "effect": "allow"},
                    ],
                })

        serializer = MySerializer(context={"request": FakeRequest(self.user)})
        fields = serializer._get_fields_from_statements("read_only")
        field_names = {f.field_name for f in fields}
        self.assertEqual(field_names, set())

    def test_deny_effect_all(self):
        class MySerializer(TestSerializer):
            class Meta:
                access_policy = AccessPolicy(field_permissions={
                    "read_only": [
                        {"principal": "*", "fields": ["username", "name"]},
                        {"principal": "authenticated", "fields": "*", "effect": "allow"},
                        {"principal": "anonymous", "fields": "*", "effect": "deny"},
                    ],
                })

        serializer = MySerializer(context={"request": FakeRequest()})
        fields = serializer._get_fields_from_statements("read_only")
        field_names = {f.field_name for f in fields}
        self.assertEqual(field_names, {"name", "username", "email", "password"})


class FieldAccessMixinApplyTests(TestCase):

    def test_keep_existing_read_only(self):
        class MySerializer(TestSerializer):
            id = IntegerField(read_only=True)

            class Meta:
                access_policy = AccessPolicy(field_permissions={
                    "read_only": [
                        {'principal': "anonymous", 'fields': ["id"], "effect": "allow"},
                    ],
                })
        serializer = MySerializer(context={"request": FakeRequest(None)})
        self.assertTrue(serializer.fields["id"].read_only)

    def test_keep_existing_read_only_model(self):
        class MySerializer(ModelSerializer):
            class Meta:
                model = Article
                fields = ("id", "title", "body", "author")
                read_only_fields = ("title", "author")
                access_policy = AccessPolicy(field_permissions={
                    "read_only": [
                        {'principal': "anonymous", 'fields': ["id"], "effect": "allow"},
                    ],
                })
        serializer = MySerializer(context={"request": FakeRequest(None)})
        self.assertTrue(serializer.fields["id"].read_only)
        self.assertTrue(serializer.fields["title"].read_only)
        self.assertTrue(serializer.fields["author"].read_only)

    def test_set_read_only_fields(self):
        class MySerializer(TestSerializer):
            class Meta:
                access_policy = AccessPolicy(field_permissions={
                    "read_only": [
                        {'principal': "anonymous", 'fields': "*"},
                    ],
                })
        serializer = MySerializer(context={"request": FakeRequest(None)})
        self.assertTrue(all(f.read_only for f in serializer.fields.values()))

    def test_set_write_only_fields(self):
        class MySerializer(TestSerializer):
            class Meta:
                access_policy = AccessPolicy(field_permissions={
                    "write_only": [
                        {'principal': "anonymous", 'fields': "*"},
                    ],
                })
        serializer = MySerializer(context={"request": FakeRequest(None)})
        self.assertTrue(all(f.write_only for f in serializer.fields.values()))
