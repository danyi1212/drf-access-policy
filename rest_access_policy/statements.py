import re
from abc import ABC
from dataclasses import dataclass
from typing import Union, Sequence, TYPE_CHECKING, Set
try:
    # support for python pre 3.8
    from typing import Literal
    EffectTypeHint = Literal["allow", "deny"]
except ImportError:
    EffectTypeHint = str


from django.contrib.auth.models import AnonymousUser

from rest_access_policy.utils import check_condition, check_condition_expression

if TYPE_CHECKING:
    from rest_access_policy.access_policy import AccessPolicy

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


@dataclass(frozen=True)
class BaseStatement(ABC):
    """
    Generic policy statement
    """
    principal: Union[str, Sequence[str]]

    def get_principals(self) -> Set[str]:
        return {self.principal} if isinstance(self.principal, str) else set(self.principal)

    def get_group_names_from_principals(self, group_prefix: str) -> Sequence[str]:
        """
        Get all groups names from principal
        :param group_prefix: Policy's group prefix for principals
        :return: List of group names
        """
        regex = re.compile(f"^{group_prefix}(.+)$")
        for principal in self.get_principals():
            match = regex.match(principal)
            if match:
                yield match.group(1)

    def match_principal(self, policy: "AccessPolicy", request, view, action: str) -> bool:
        principals = self.get_principals()
        user = getattr(request, "user", AnonymousUser())
        get_user_group_values = getattr(policy, "get_user_group_values", None)  # for legacy compatability

        return (
            "*" in principals
            or ("admin" in principals and user.is_superuser)
            or ("staff" in principals and user.is_staff)
            or ("authenticated" in principals and not user.is_anonymous)
            or ("anonymous" in principals and user.is_anonymous)
            or ("active" in principals and user.is_active)
            or ("disabled" in principals and not user.is_active and not user.is_anonymous)
            or (f"{policy.id_prefix}{user.pk}" in principals)
            or (callable(get_user_group_values) and user
                and any(f"{policy.group_prefix}{user_role}" in principals
                        for user_role in get_user_group_values(user)))
            or (not get_user_group_values and user
                and policy.is_member_in_group(
                    user, list(self.get_group_names_from_principals(policy.group_prefix))
                ))
        )


@dataclass(frozen=True)
class Statement(BaseStatement):
    """
    Access Statement for determining permission to view
    """
    action: Union[str, Sequence[str]]
    effect: EffectTypeHint = None
    condition: Union[str, Sequence[str]] = None
    condition_expression: Union[str, Sequence[str]] = None

    @classmethod
    def from_dict(cls, statement: dict) -> "Statement":
        for key in ("principal", "action"):
            if key not in statement:
                raise KeyError(f"Access Policy Statement must specify \"{key}\" value.")

        return cls(**statement)

    def __post_init__(self):
        if self.effect not in {None, "allow", "deny"}:
            raise ValueError(f"Statement effect must be either \"allow\" or \"deny\" (not \"{self.effect}\")")

    def get_actions(self) -> Set[str]:
        return {self.action} if isinstance(self.action, str) else set(self.action)

    def get_conditions(self) -> Sequence[str]:
        if not self.condition:
            return tuple()
        elif isinstance(self.condition, str):
            return self.condition,
        else:
            return self.condition

    def get_condition_expressions(self) -> Sequence[str]:
        if not self.condition_expression:
            return tuple()
        elif isinstance(self.condition_expression, str):
            return self.condition_expression,
        else:
            return self.condition_expression

    def match_action(self, policy: "AccessPolicy", request, view, action: str) -> bool:
        actions = self.get_actions()

        return (
            "*" in actions
            or action in actions
            or f"<method:{request.method.lower()}>" in actions
            or "<safe_methods>" in actions and request.method in SAFE_METHODS
        )

    def match_condition(self, policy: "AccessPolicy", request, view, action: str) -> bool:
        return all(
            check_condition(policy, condition, request, view, action)
            for condition in self.get_conditions()
        )

    def match_condition_expression(self, policy: "AccessPolicy", request, view, action: str) -> bool:
        return all(
            check_condition_expression(policy, condition, request, view, action)
            for condition in self.get_condition_expressions()
        )

    def evaluate(self, policy: "AccessPolicy", request, view, action: str) -> bool:
        return (
            self.match_principal(policy, request, view, action)
            and self.match_action(policy, request, view, action)
            and self.match_condition(policy, request, view, action)
            and self.match_condition_expression(policy, request, view, action)
        )


@dataclass(frozen=True)
class FieldStatement(BaseStatement):
    """
    Field Statement for modifying serializer fields.
    """
    fields: Union[str, Sequence[str]]
    effect: EffectTypeHint = None

    @classmethod
    def from_dict(cls, statement: dict) -> "FieldStatement":
        for key in ("principal", "fields"):
            if key not in statement:
                raise KeyError(f"Access Policy Serializer Statement must specify \"{key}\" value.")

        return cls(**statement)

    def get_fields(self) -> Set[str]:
        return {self.fields} if isinstance(self.fields, str) else set(self.fields)

    def match_field(self, field_name: str) -> bool:
        fields = self.get_fields()
        return (
            "*" in fields
            or field_name in fields
        )
