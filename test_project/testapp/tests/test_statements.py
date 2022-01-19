from itertools import product
from typing import List, Dict
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User, Group
from django.test import TestCase

from rest_access_policy.statements import Statement, FieldStatement
from test_project.testapp.tests.utils import FakeRequest, FakeViewSet, TestPolicy


class StatementCreationTests(TestCase):

    def setUp(self):
        User.objects.all().delete()
        Group.objects.all().delete()

    def test_normalization(self):
        single_value_statement = Statement(
            principal="test_principal",
            action="test_action",
            condition="test_condition",
            condition_expression="test_condition_expression",
        )
        multi_value_statement = Statement(
            principal=["test_principal"],
            action=["test_action"],
            condition=["test_condition"],
            condition_expression=["test_condition_expression"],
        )
        self.assertEqual(single_value_statement.get_principals(), multi_value_statement.get_principals())
        self.assertEqual(single_value_statement.get_actions(), multi_value_statement.get_actions())
        self.assertEqual(
            tuple(single_value_statement.get_conditions()),
            tuple(multi_value_statement.get_conditions()),
        )
        self.assertEqual(
            tuple(single_value_statement.get_condition_expressions()),
            tuple(multi_value_statement.get_condition_expressions()),
        )

    def test_get_group_names_from_principals(self):
        statement = Statement(action="*",
                              principal=["custom:group1", "custom:group2", "not_custom:group3", "custom-group4"])
        groups = statement.get_group_names_from_principals("custom:")
        self.assertEqual(list(sorted(groups)), ["group1", "group2"])

    def test_empty_condition(self):
        statement = Statement(principal="", action="", condition="", condition_expression="")
        self.assertEqual(statement.get_conditions(), tuple())
        self.assertEqual(statement.get_condition_expressions(), tuple())

    def test_from_dict(self):
        statement = Statement.from_dict({
            "principal": "test_principal",
            "action": "test_action",
            "condition": "test_condition",
            "condition_expression": "test_condition_expression",
        })
        self.assertEqual(statement.principal, "test_principal")
        self.assertEqual(statement.action, "test_action")
        self.assertEqual(statement.condition, "test_condition")
        self.assertEqual(statement.condition_expression, "test_condition_expression")

    def test_from_dict_missing_principal(self):
        with self.assertRaises(KeyError) as context:
            Statement.from_dict({"action": "test_action"})

        self.assertEqual("'Access Policy Statement must specify \"principal\" value.'", str(context.exception))

    def test_from_dict_missing_action(self):
        with self.assertRaises(KeyError) as context:
            Statement.from_dict({"principal": "test_principal"})

        self.assertEqual("'Access Policy Statement must specify \"action\" value.'", str(context.exception))

    def test_from_dict_invalid_effect(self):
        with self.assertRaises(ValueError) as context:
            Statement.from_dict({
                "principal": "test_principal",
                "action": "test_action",
                "effect": "not_allowed",
            })
        self.assertTrue("not_allow" in str(context.exception))
        self.assertTrue("allow" in str(context.exception))
        self.assertTrue("deny" in str(context.exception))

    def test_field_statement_from_dict(self):
        statement = FieldStatement.from_dict({
            "principal": "test_principal",
            "fields": "test_field",
        })
        self.assertEqual(statement.principal, "test_principal")
        self.assertEqual(statement.fields, "test_field")
        self.assertEqual(statement.get_fields(), {"test_field"})

    def test_field_statement_missing_fields(self):
        with self.assertRaises(KeyError) as context:
            FieldStatement.from_dict({"principal": "test_principal"})

        self.assertEqual("'Access Policy Serializer Statement must specify \"fields\" value.'", str(context.exception))


class StatementMatchTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="test_user")
        cls.disabled = User.objects.create_user(username="test_disabled", is_active=False)
        cls.staff = User.objects.create_user(username="test_staff", is_staff=True)
        cls.superuser = User.objects.create_user(username="test_superuser", is_superuser=True)

        cls.group = Group.objects.create(name="test_group")
        cls.group2 = Group.objects.create(name="test_group2")
        cls.user.groups.add(cls.group, cls.group2)
        cls.superuser.groups.add(cls.group, cls.group2)

        cls.view = FakeViewSet()
        cls.policy = TestPolicy()
        cls.action = "create"

    def assert_match_principals(self, statement: Statement, results: List[bool]):
        for index, user in enumerate([self.superuser, self.staff, self.user, self.disabled, None]):
            title = ["Super", "Staff", "Regular", "Disabled", "Anonymous"][index]
            expected = 'pass' if results[index] else 'not pass'
            with self.subTest(title, expected=expected):
                self.assertEqual(
                    results[index],
                    statement.match_principal(self.policy, FakeRequest(user), self.view, self.action),
                    msg=f"{title} User should {expected} for statement principal \"{statement.principal}\""
                )

    def assert_match_actions(self, statement: Statement, result: bool, actions: List[str], methods: List[str]):
        expected = 'pass' if result else 'not pass'
        for method, action in product(methods, actions):
            with self.subTest(method=method, action=action, expected=expected):
                self.assertEqual(
                    result,
                    statement.match_action(self.policy, FakeRequest(self.user, method), FakeViewSet(), action),
                    msg=f"{action} User should {expected} for statement action \"{statement.action}\""
                )

    def test_match_principal_all(self):
        statement = Statement(principal="*", action="*")
        self.assert_match_principals(statement, [True, True, True, True, True])

    def test_match_principal_admin(self):
        statement = Statement(principal="admin", action="*")
        self.assert_match_principals(statement, [True, False, False, False, False])

    def test_match_principal_staff(self):
        statement = Statement(principal="staff", action="*")
        self.assert_match_principals(statement, [False, True, False, False, False])

    def test_match_principal_anonymous(self):
        statement = Statement(principal="anonymous", action="*")
        self.assert_match_principals(statement, [False, False, False, False, True])

    def test_match_principal_authenticated(self):
        statement = Statement(principal="authenticated", action="*")
        self.assert_match_principals(statement, [True, True, True, True, False])

    def test_match_principal_active(self):
        statement = Statement(principal="active", action="*")
        self.assert_match_principals(statement, [True, True, True, False, False])

    def test_match_principal_disabled(self):
        statement = Statement(principal="disabled", action="*")
        self.assert_match_principals(statement, [False, False, False, True, False])

    def test_match_principal_id(self):
        statement = Statement(principal=f"id:{self.user.pk}", action="*")
        self.assert_match_principals(statement, [False, False, True, False, False])

    def test_match_principal_group(self):
        statement = Statement(principal="group:test_group", action="*")
        self.assert_match_principals(statement, [True, False, True, False, False])

    def test_match_principal_group_multiple(self):
        statement = Statement(principal=["group:test_group", "group:test_group2"], action="*")
        self.assert_match_principals(statement, [True, False, True, False, False])

    def test_match_action_all(self):
        statement = Statement(principal="*", action="*")
        self.assert_match_actions(statement, True,
                                  actions=["post", "custom"],
                                  methods=["GET", "HEAD", "OPTIONS", "POST"])

    def test_match_action_custom(self):
        statement = Statement(principal="*", action="custom")
        self.assert_match_actions(statement, True, actions=["custom"], methods=["GET", "HEAD", "OPTIONS", "POST"])
        self.assert_match_actions(statement, False, actions=["post"], methods=["GET", "HEAD", "OPTIONS", "POST"])

    def test_match_action_method(self):
        statement = Statement(principal="*", action="<method:post>")
        self.assert_match_actions(statement, True, actions=["post", "custom"], methods=["POST"])
        self.assert_match_actions(statement, False, actions=["post", "custom"], methods=["GET"])

    def test_match_action_safe_method(self):
        statement = Statement(principal="*", action="<safe_methods>")
        self.assert_match_actions(statement, True, actions=["post", "custom"], methods=["GET", "HEAD", "OPTIONS"])
        self.assert_match_actions(statement, False, actions=["post", "custom"], methods=["POST"])

    def test_match_condition(self):
        statement = Statement(principal="*", action="*", condition="simple_condition")
        self.assertTrue(statement.match_condition(self.policy, FakeRequest(), self.view, self.action))

    def test_match_condition_false(self):
        statement = Statement(principal="*", action="*", condition="false_condition")
        self.assertFalse(statement.match_condition(self.policy, FakeRequest(), self.view, self.action))

    def test_match_condition_multiple(self):
        statement = Statement(principal="*", action="*", condition=["simple_condition", "false_condition"])
        self.assertFalse(statement.match_condition(self.policy, FakeRequest(), self.view, self.action))

    def test_match_condition_expression(self):
        statement = Statement(principal="*", action="*", condition_expression="is_true or is_false")
        self.assertTrue(statement.match_condition_expression(self.policy, FakeRequest(), self.view, self.action))

    def test_match_condition_expression_false(self):
        statement = Statement(principal="*", action="*", condition_expression="is_true and is_false")
        self.assertFalse(statement.match_condition_expression(self.policy, FakeRequest(), self.view, self.action))

    def test_match_condition_expression_multiple(self):
        statement = Statement(principal="*", action="*", condition_expression=["not is_true", "not is_false"])
        self.assertFalse(statement.match_condition_expression(self.policy, FakeRequest(), self.view, self.action))


class StatementEvaluationTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="test_user")
        cls.request = FakeRequest(cls.user)
        cls.view = FakeViewSet()
        cls.policy = TestPolicy()
        cls.action = "create"

    def patch_statement(self, statement: Statement) -> Dict[str, MagicMock]:
        mocks = {}
        for method in "match_principal", "match_action", "match_condition", "match_condition_expression":
            patcher = patch(f"rest_access_policy.statements.Statement.{method}", wraps=getattr(statement, method))
            mocks[method] = patcher.start()
            self.addCleanup(patcher.stop)

        return mocks

    def assert_called(self, mock: MagicMock, should_call: bool):
        if should_call:
            mock.assert_called_with(self.policy, self.request, self.view, self.action)
        else:
            mock.assert_not_called()

    def assert_evaluation_order(self, statement: Statement, expected_result: bool, call_principal: bool,
                                call_action: bool, call_condition: bool, call_condition_expression: bool):
        mocks = self.patch_statement(statement)
        result = statement.evaluate(self.policy, self.request, self.view, self.action)
        self.assertEqual(result, expected_result)
        self.assert_called(mocks["match_principal"], call_principal)
        self.assert_called(mocks["match_action"], call_action)
        self.assert_called(mocks["match_condition"], call_condition)
        self.assert_called(mocks["match_condition_expression"], call_condition_expression)

    def test_evaluate(self):
        statement = Statement(principal="*", action="*")
        self.assert_evaluation_order(statement, True, True, True, True, True)

    def test_evaluate_order_principal(self):
        statement = Statement(principal="staff", action="*")
        self.assert_evaluation_order(statement, False, True, False, False, False)

    def test_evaluate_order_action(self):
        statement = Statement(principal="*", action="other")
        self.assert_evaluation_order(statement, False, True, True, False, False)

    def test_evaluate_order_condition(self):
        statement = Statement(principal="*", action="*", condition='is_false')
        self.assert_evaluation_order(statement, False, True, True, True, False)

    def test_evaluate_order_condition_expression(self):
        statement = Statement(principal="*", action="*", condition_expression='not is_true')
        self.assert_evaluation_order(statement, False, True, True, True, True)
