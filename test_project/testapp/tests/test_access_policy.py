# pylint: disable=protected-access
from typing import List
from unittest.mock import patch, MagicMock

from django.contrib.auth.models import Group, User
from django.test import TestCase

from rest_access_policy.access_policy import AccessPolicy, AccessEnforcement
from rest_access_policy.statements import Statement
from test_project.testapp.tests.utils import FakeRequest, FakeViewSet


class PolicyEvaluationTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="test_user")
        cls.view = FakeViewSet()
        cls.request = FakeRequest(cls.user)
        cls.action = "create"

    def evaluate_policy(self, policy: AccessPolicy):
        return policy._evaluate_statements(self.request, self.view, self.action)

    def test_all_match(self):
        policy = AccessPolicy(statements=[
            {"principal": "*", "action": "create"},
            {"principal": f"id:{self.user.pk}", "action": "*"},
        ])
        result = self.evaluate_policy(policy)
        self.assertTrue(result)

    def test_not_all_match(self):
        policy = AccessPolicy(statements=[
            {"principal": "*", "action": "create"},
            {"principal": "staff", "action": "*"},
            {"principal": "is_authenticated", "action": "*"},
        ])
        result = self.evaluate_policy(policy)
        self.assertFalse(result)

    def test_no_statements(self):
        policy = AccessPolicy(statements=[])
        result = self.evaluate_policy(policy)
        self.assertFalse(result)

    def test_deny_matched(self):
        policy = AccessPolicy(statements=[
            {"principal": "*", "action": "create", "effect": "allow"},
            {"principal": "*", "action": "*", "effect": "deny"},
            {"principal": "*", "action": "*"},
        ])
        result = self.evaluate_policy(policy)
        self.assertFalse(result)

    def test_allow_matched(self):
        policy = AccessPolicy(statements=[
            {"principal": "*", "action": "create", "effect": "allow"},
            {"principal": "*", "action": "take_out_the_trash"},
            {"principal": "staff", "action": "*", "effect": "deny"},
        ])
        result = self.evaluate_policy(policy)
        self.assertTrue(result)

    def test_all_default_matched(self):
        policy = AccessPolicy(statements=[
            {"principal": "*", "action": "create"},
            {"principal": "*", "action": "take_out_the_trash", "effect": "allow"},
            {"principal": "staff", "action": "*", "effect": "deny"},
        ])
        result = self.evaluate_policy(policy)
        self.assertTrue(result)

    def test_not_all_default_matched(self):
        policy = AccessPolicy(statements=[
            {"principal": "*", "action": "create"},
            {"principal": "*", "action": "get"},
            {"principal": "*", "action": "take_out_the_trash", "effect": "allow"},
            {"principal": "staff", "action": "*", "effect": "deny"},
        ])
        result = self.evaluate_policy(policy)
        self.assertFalse(result)

    def test_not_default_remained(self):
        policy = AccessPolicy(statements=[
            {"principal": "*", "action": "take_out_the_trash", "effect": "allow"},
            {"principal": "staff", "action": "*", "effect": "deny"},
        ])
        result = self.evaluate_policy(policy)
        self.assertFalse(result)

    @patch("rest_access_policy.statements.Statement.evaluate", return_value=True)
    def test_no_unnecessary_evaluations_when_deny(self, mock: MagicMock):
        policy = AccessPolicy(statements=[
            {"principal": "*", "action": "create", "effect": "allow"},
            {"principal": "*", "action": "*", "effect": "deny"},
            {"principal": "*", "action": "*"},
        ])
        self.evaluate_policy(policy)
        mock.assert_called_once_with(policy, self.request, self.view, self.action)

    @patch("rest_access_policy.statements.Statement.evaluate", return_value=True)
    def test_no_unnecessary_evaluations_when_allow(self, mock: MagicMock):
        policy = AccessPolicy(statements=[
            {"principal": "*", "action": "create", "effect": "allow"},
            {"principal": "*", "action": "take_out_the_trash"},
        ])
        self.evaluate_policy(policy)
        mock.assert_called_once_with(policy, self.request, self.view, self.action)


class AccessPolicyTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.group = Group.objects.create(name="test_group")
        cls.user = User.objects.create(username="test_user")
        cls.user.groups.add(cls.group)
        cls.view = FakeViewSet()
        cls.request = FakeRequest(cls.user)
        cls.action = "create"

    def test_normalize_statements(self):
        class MyPolicy(AccessPolicy):
            statements = [Statement(principal="group:admin", action="*")]

        policy = AccessPolicy(statements=[
            {"principal": "*", "action": "create", "effect": "allow"},
            Statement(principal="*", action="create", effect="deny"),
            AccessPolicy(statements=[
                {"principal": "staff", "action": "create", "effect": "allow"},
                Statement(principal="*", action="create"),
            ]),
            MyPolicy,
            {"principal": "authenticated", "action": "create"},
        ])
        statements = list(policy._get_statements(self.request, self.view))
        self.assertEqual(statements, [
            Statement(principal="*", action="create", effect="allow"),
            Statement(principal="*", action="create", effect="deny"),
            Statement(principal="staff", action="create", effect="allow"),
            Statement(principal="*", action="create"),
            Statement(principal="group:admin", action="*"),
            Statement(principal="authenticated", action="create"),
        ])

    def test_invalid_statement_object(self):
        policy = AccessPolicy("test_policy", statements=[
            {"principal": "*", "action": "create", "effect": "allow"},
            [Statement(principal="*", action="create", effect="deny")]
        ])
        with self.assertRaises(ValueError) as context:
            list(policy._get_statements(self.request, self.view))

        self.assertTrue("list" in str(context.exception))
        self.assertTrue("index 1" in str(context.exception))
        self.assertTrue("AccessPolicy (id=test_policy)" in str(context.exception))

    def test_policy_get_user_group_values(self):
        # for backward compatability
        class TestPolicy(AccessPolicy):
            def get_user_group_values(self, user) -> List[str]:
                return list(user.groups.values_list("name", flat=True))

        policy = TestPolicy(statements=[{'principal': "group:test_group", 'action': "*"}])
        with patch.object(policy, "get_user_group_values", wraps=policy.get_user_group_values) as mock:
            result = policy._evaluate_statements(self.request, self.view, self.action)
            self.assertTrue(result)

        mock.assert_called_once_with(self.user)

        policy = TestPolicy(statements=[{'principal': "group:does_not_exist", 'action': "*"}])
        with patch.object(policy, "is_member_in_group") as mock:
            result = policy._evaluate_statements(self.request, self.view, self.action)
            self.assertFalse(result)

        mock.assert_not_called()

    @patch("rest_access_policy.access_policy.AccessPolicy.is_member_in_group", return_value=True)
    def test_policy_is_member_in_group(self, mock: MagicMock):
        policy = AccessPolicy(statements=[
            {'principal': "group:test_group", 'action': "*"}
        ])
        result = policy._evaluate_statements(self.request, self.view, self.action)
        self.assertTrue(result)
        mock.assert_called_once_with(self.user, ["test_group"])

    @patch("rest_access_policy.access_policy.AccessPolicy.is_member_in_group", return_value=True)
    def test_group_prefix(self, mock: MagicMock):
        class TestPolicy(AccessPolicy):
            group_prefix = "role:"
            statements = [
                {'principal': "role:test_group", 'action': "*"}
            ]
        policy = TestPolicy()
        result = policy._evaluate_statements(self.request, self.view, self.action)
        self.assertTrue(result)
        mock.assert_called_once_with(self.user, ["test_group"])

    def test_id_prefix(self):
        class TestPolicy(AccessPolicy):
            id_prefix = "uuid:"
            statements = [
                {'principal': f"uuid:{self.user.pk}", 'action': "*"}
            ]
        policy = TestPolicy()
        result = policy._evaluate_statements(self.request, self.view, self.action)
        self.assertTrue(result)

    def test_has_permission(self):
        policy = AccessPolicy(statements=[{"principal": "*", "action": "create", "effect": "allow"}])
        with patch.object(policy, "_evaluate_statements", wraps=policy._evaluate_statements) as mock:
            policy.has_permission(self.request, self.view)

        mock.assert_called_once_with(self.request, self.view, self.action)
        self.assertEqual(getattr(self.request, "access_enforcement", None),
                         AccessEnforcement(action=self.action, allowed=True))

    def test_has_permission_with_different_requests(self):
        policy = AccessPolicy(statements=[
            {"action": "get", "principal": "group:hr", "effect": "allow"},
            {"action": "*", "principal": "group:admin", "effect": "allow"},
        ])
        fred = User.objects.create(username="fred")
        fred.groups.add(Group.objects.create(name="admin"))

        jane = User.objects.create(username="jane")
        jane.groups.add(Group.objects.create(name="hr"))

        self.assertTrue(policy.has_permission(FakeRequest(user=fred), self.view))
        self.assertFalse(policy.has_permission(FakeRequest(user=jane), self.view))

    def test_has_permission_with_anonymous_request(self):
        policy = AccessPolicy(statements=[{"action": "*", "principal": "anonymous"}])
        self.assertTrue(policy.has_permission(FakeRequest(user=None), self.view))

    def test_has_permission_with_anonymous_request_deny(self):
        policy = AccessPolicy(statements=[{"action": "*", "principal": "authenticated"}])
        self.assertFalse(policy.has_permission(FakeRequest(user=None), self.view))
