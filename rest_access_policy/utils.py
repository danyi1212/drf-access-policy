import re
from functools import lru_cache, wraps
from importlib import import_module
from typing import Optional, Callable, TYPE_CHECKING, Set, Sequence

from django.conf import settings
from pyparsing import infixNotation, opAssoc

from rest_access_policy.exceptions import AccessPolicyException
from rest_access_policy.parsing import boolOperand, ConditionOperand, BoolNot, BoolAnd, BoolOr

if TYPE_CHECKING:
    from rest_access_policy.access_policy import AccessPolicy


@lru_cache()
def get_reusable_condition(method_name: str) -> Optional[Callable]:
    """
    Search and import reusable conditions
    :param method_name: Name of condition method
    :return: Condition Function
    """
    if not hasattr(settings, "DRF_ACCESS_POLICY"):
        return None

    module_paths = settings.DRF_ACCESS_POLICY.get("reusable_conditions")
    if not isinstance(module_paths, (str, list, tuple, set)):
        return None

    module_paths = [module_paths] if isinstance(module_paths, str) else module_paths
    for module_path in module_paths:
        module = import_module(module_path)

        if hasattr(module, method_name) and callable(getattr(module, method_name)):
            return getattr(module, method_name)


def get_condition_method(policy: "AccessPolicy", method_name: str) -> Callable:
    """
    Search for condition method.
    First search for method on policy, fallback to reusable conditions.
    :param policy: Access Policy object
    :param method_name: Name of condition method
    :return: Condition Function
    """
    if hasattr(policy, method_name) and callable(getattr(policy, method_name)):
        return getattr(policy, method_name)

    method = get_reusable_condition(method_name)
    if not method:
        raise AccessPolicyException(
            f"Unable to find condition method \"{method_name}\". Condition must be a method on the access policy "
            f"or a function defined in a module listed on the \"reusable_conditions\" setting."
        )

    return method


def check_condition(policy: "AccessPolicy", condition: str, request, view, action: str) -> bool:
    """
    Evaluate a custom context condition.
    Condition can contain an argument that will be passed to the method (e.g. `<method_name>:<arg_value>`)
    :param policy: Access Policy object
    :param condition: Condition string
    :param request: Current request
    :param view: Policy view
    :param action: View action
    :return: Condition method result (True if matched)
    """
    parts = condition.split(":", 1)
    method_name = parts[0]
    arg = parts[1] if len(parts) == 2 else None
    method = get_condition_method(policy, method_name)

    if arg is not None:
        result = method(request, view, action, arg)
    else:
        result = method(request, view, action)

    if isinstance(result, bool):
        return result
    else:
        raise AccessPolicyException(
            f"Received invalid value \"{result}\" (type {type(result)}) from condition \"{condition}\". "
            f"Conditions must return a boolean value (True/False)."
        )


def check_condition_expression(policy, condition: str, request, view, action: str) -> bool:
    """
    Evaluate an expression of conditions containing boolean operators.
    :param policy: Access Policy object
    :param condition: Condition expression string
    :param request: Current request
    :param view: Policy view
    :param action: View action
    :return: Condition expression result
    """
    boolOperand.setParseAction(
        lambda token: ConditionOperand(
            token,
            check_cond_fn=lambda cond: check_condition(policy, cond, request, view, action)
        )
    )
    bool_expr = infixNotation(
        boolOperand,
        [
            ("not", 1, opAssoc.RIGHT, BoolNot),
            ("and", 2, opAssoc.LEFT, BoolAnd),
            ("or", 2, opAssoc.LEFT, BoolOr),
        ],
    )

    return bool(bool_expr.parseString(condition)[0])


def get_view_action(view) -> str:
    """
    If a Class-Based view, the name of the method.
    If a function view, the name of the function.
    """
    if hasattr(view, "action"):
        if hasattr(view, "action_map"):
            return view.action or list(view.action_map.values())[0]
        else:
            return view.action
    elif hasattr(view, "__class__"):
        return view.__class__.__name__
    else:
        raise AccessPolicyException("Could not determine action of request")


def object_level_condition(default=False, raise_exception=False):
    """
    Injects view.get_object() as parameter for condition.

    @object_level_condition()
    def user_must_be(self, request, view, obj, arg):
        return getattr(obj, arg) == request.user

    :param default: default result when view.get_object() is not accessible.
    :param raise_exception: propagate exception raised by view.get_object()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, view, action, *args) -> bool:
            try:
                obj = view.get_object()
            except Exception as e:
                obj = default
                if raise_exception:
                    raise e

            return func(request, view, action, obj, *args)

        return wrapper

    return decorator
