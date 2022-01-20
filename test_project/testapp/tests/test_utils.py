# pylint: disable=attribute-defined-outside-init
from unittest.mock import patch, MagicMock

from django.contrib.auth.models import User, Group
from django.test import TestCase, override_settings
from rest_framework.decorators import api_view
from rest_framework.viewsets import ModelViewSet

from rest_access_policy import AccessPolicyException
from rest_access_policy.utils import get_view_action, check_condition, get_reusable_condition, \
    check_condition_expression
from test_project.global_access_conditions import is_a_func
from test_project.testapp.tests.utils import FakeRequest, FakeViewSet, TestPolicy


class UtilsTests(TestCase):

    def setUp(self):
        User.objects.all().delete()
        Group.objects.all().delete()

    def test_get_view_action_from_function_based_view(self):
        @api_view(["GET"])
        def my_view(request):
            return ""

        view_instance = my_view.cls()
        result = get_view_action(view_instance)
        self.assertEqual(result, "my_view")

    def test_get_view_action_from_class_based_view(self):
        class UserViewSet(ModelViewSet):
            pass

        view_instance = UserViewSet()
        view_instance.action = "create"

        result = get_view_action(view_instance)
        self.assertEqual(result, "create")


class ReusableConditionTests(TestCase):

    def tearDown(self):
        super().tearDown()
        get_reusable_condition.cache_clear()

    @override_settings(DRF_ACCESS_POLICY={"reusable_conditions": "test_project.global_access_conditions"})
    def test_get_condition(self):
        method = get_reusable_condition("is_a_func")
        self.assertEqual(method, is_a_func)

    def test_missing_setting(self):
        method = get_reusable_condition("is_a_func")
        self.assertEqual(method, None)

    @override_settings(DRF_ACCESS_POLICY={})
    def test_setting_missing_key(self):
        method = get_reusable_condition("is_a_func")
        self.assertEqual(method, None)

    @override_settings(DRF_ACCESS_POLICY={"reusable_conditions": True})
    def test_setting_incorrect_type(self):
        method = get_reusable_condition("is_a_func")
        self.assertEqual(method, None)

    @override_settings(DRF_ACCESS_POLICY={"reusable_conditions": ["test_project.global_access_conditions"]})
    def test_setting_list(self):
        method = get_reusable_condition("is_a_func")
        self.assertEqual(method, is_a_func)

    @override_settings(DRF_ACCESS_POLICY={"reusable_conditions": "test_project.global_access_conditions"})
    def test_get_reusable_conditions_not_callable(self):
        method = get_reusable_condition("not_a_func")
        self.assertEqual(method, None)


class ConditionTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="test_user")
        cls.request = FakeRequest(cls.user)
        cls.view = FakeViewSet()
        cls.policy = TestPolicy()
        cls.action = "create"

    def call_condition(self, condition: str):
        return check_condition(self.policy, condition, self.request, self.view, self.action)

    def call_condition_expression(self, condition: str):
        return check_condition_expression(self.policy, condition, self.request, self.view, self.action)

    def test_condition_result(self):
        result = self.call_condition("simple_condition")
        self.assertTrue(result)

    @patch("test_project.testapp.tests.utils.TestPolicy.simple_condition", return_value=True)
    def test_condition_is_called(self, mock: MagicMock):
        self.call_condition("simple_condition")
        mock.assert_called_once_with(self.request, self.view, self.action)

    @override_settings(DRF_ACCESS_POLICY={"reusable_conditions": "test_project.global_access_conditions"})
    @patch("test_project.global_access_conditions.simple_condition", return_value=True)
    @patch("test_project.testapp.tests.utils.TestPolicy.simple_condition", return_value=True)
    def test_condition_override_reusable(self, mock_local: MagicMock, mock_reusable: MagicMock):
        self.call_condition("simple_condition")
        mock_reusable.assert_not_called()
        mock_local.assert_called_once_with(self.request, self.view, self.action)

    def test_condition_return_non_boolean(self):
        with self.assertRaises(AccessPolicyException) as context:
            self.call_condition("non_boolean")

        self.assertTrue("Received invalid value" in str(context.exception))
        self.assertTrue("Hi mom" in str(context.exception))
        self.assertTrue("str" in str(context.exception))
        self.assertTrue("non_boolean" in str(context.exception))

    def test_condition_does_not_exist(self):
        with self.assertRaises(AccessPolicyException) as context:
            self.call_condition("does_not_exist")

        self.assertTrue("Unable to find condition" in str(context.exception))
        self.assertTrue("does_not_exist" in str(context.exception))

    def test_condition_not_callable(self):
        with self.assertRaises(AccessPolicyException) as context:
            self.call_condition("not_a_func")

        self.assertTrue("Unable to find condition" in str(context.exception))
        self.assertTrue("not_a_func" in str(context.exception))

    @patch("test_project.testapp.tests.utils.TestPolicy.with_arg", return_value=True)
    def test_condition_with_arg(self, mock: MagicMock):
        self.call_condition("with_arg:test")
        mock.assert_called_once_with(self.request, self.view, self.action, "test")

    def test_condition_with_arg_not_expected(self):
        with self.assertRaises(TypeError) as context:
            self.call_condition("simple_condition:test")

        self.assertTrue("4 positional arguments but 5 were given" in str(context.exception))
        self.assertTrue("simple_condition()" in str(context.exception))

    def test_condition_raise_exception(self):
        with self.assertRaises(ValueError) as context:
            self.call_condition("with_error")

        self.assertEqual("Condition Error", str(context.exception))

    @override_settings(DRF_ACCESS_POLICY={"reusable_conditions": "test_project.global_access_conditions"})
    @patch("test_project.global_access_conditions.is_a_cat", return_value=True)
    def test_condition_in_reusable_module(self, mock: MagicMock):
        self.call_condition("is_a_cat:Garfield")
        mock.assert_called_once_with(self.request, self.view, self.action, "Garfield")

    def test_condition_expression_and(self):
        result = self.call_condition_expression("is_true and is_false")
        self.assertEqual(result, False)

    def test_condition_expression_or(self):
        result = self.call_condition_expression("is_true or is_false")
        self.assertEqual(result, True)

    def test_condition_expression_not(self):
        result = self.call_condition_expression("is_true and not is_false")
        self.assertEqual(result, True)

    def test_condition_expression_not_not(self):
        result = self.call_condition_expression("not not is_true")
        self.assertEqual(result, True)

    def test_condition_expression_parenthesis(self):
        result = self.call_condition_expression("not (is_true and is_false)")
        self.assertEqual(result, True)

    @patch("test_project.testapp.tests.utils.TestPolicy.is_cloudy", return_value=True)
    def test_condition_expression_order(self, mock: MagicMock):
        result = self.call_condition_expression("is_false and not is_true or is_cloudy")
        self.assertEqual(result, True)
        mock.assert_called_once_with(self.request, self.view, self.action)

    @patch("test_project.testapp.tests.utils.TestPolicy.is_cloudy", return_value=True)
    def test_condition_expression_skip_unneeded(self, mock: MagicMock):
        result = self.call_condition_expression("is_true or is_cloudy")
        self.assertEqual(result, True)
        mock.assert_not_called()

    @patch("test_project.testapp.tests.utils.TestPolicy.with_arg", return_value=True)
    def test_condition_expression_with_arg(self, mock: MagicMock):
        result = self.call_condition_expression("is_true and with_arg:test")
        self.assertEqual(result, True)
        mock.assert_called_once_with(self.request, self.view, self.action, "test")

    @patch("rest_access_policy.parsing.boolOperand")
    def test_parser_not_used_for_regular_condition(self, mock):
        result = self.call_condition("simple_condition")
        self.assertEqual(result, True)
        mock.assert_not_called()
