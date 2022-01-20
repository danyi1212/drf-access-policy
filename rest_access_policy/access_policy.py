# pylint: disable=protected-access, no-self-use, unused-argument
from dataclasses import dataclass
from inspect import isclass
from typing import Union, Sequence, Iterator, List, Dict, Type

from django.db.models import QuerySet
from rest_framework import permissions

from rest_access_policy.statements import Statement, FieldStatement
from rest_access_policy.utils import get_view_action


PolicyAccessStatement = Union[Statement, "AccessPolicy", Type["AccessPolicy"], dict]
PolicyFieldStatement = Union[FieldStatement, "AccessPolicy", Type["AccessPolicy"], dict]


@dataclass(frozen=True)
class AccessEnforcement:
    action: str
    allowed: bool


class AccessPolicy(permissions.BasePermission):
    statements: Sequence[PolicyAccessStatement] = []
    field_permissions: Dict[str, Sequence[PolicyFieldStatement]] = {}
    id = None
    group_prefix = "group:"
    id_prefix = "id:"

    def __init__(self, policy_id: str = None, statements: Sequence[PolicyAccessStatement] = None,
                 field_permissions: Dict[str, Sequence[Union[FieldStatement, dict]]] = None):
        if policy_id:
            self.id = policy_id

        if statements:
            self.statements = statements

        if field_permissions:
            self.field_permissions = field_permissions

    @classmethod
    def scope_queryset(cls, request, qs: QuerySet) -> QuerySet:
        """
        Filter view queryset to include only allowed rows.
        :param request: Current request
        :param qs: View queryset
        :return: Scoped queryset
        """
        return qs.none()

    def is_member_in_group(self, user, groups: List[str]) -> bool:
        """
        Whether a user is a member in one of the provided groups.
        Used to determine matching for statement's participant values starting with the group prefix.
        :param user: The user being checked
        :param groups: List of group names
        :return: True if the user is a member in any of the groups
        """
        return user.groups.filter(name__in=groups).exists()

    def has_permission(self, request, view) -> bool:
        """
        Whether request should be allowed or denied.
        :param request: Current request
        :param view: View checked by this policy
        :return: Boolean
        """
        action = get_view_action(view)
        allowed = self._evaluate_statements(request, view, action)
        request.access_enforcement = AccessEnforcement(action=action, allowed=allowed)
        return allowed

    def get_policy_statements(self, request, view) -> Sequence[PolicyAccessStatement]:
        """
        Get all statements for this policy.
        :param request: Current request
        :param view: View checked by this policy
        :return: Sequence of access statements
        """
        return self.statements

    def get_field_statements(self, key: str) -> Sequence[PolicyFieldStatement]:
        """
        Get field statements for a specific key.
        :param key: Policy field key (aka. serializer field attribute)
        :return: Sequence of field statements
        """
        return self.field_permissions[key]

    def _get_statements(self, request, view) -> Iterator[Statement]:
        """
        Unify access statements to be Statement objects.
        :param request: Current request
        :param view: View checked by this policy
        :return: Generator of access statements
        :raises ValueError: A statement is not valid or incorrect type
        """
        for index, statement in enumerate(self.get_policy_statements(request, view)):
            if isinstance(statement, Statement):
                yield statement
            elif isinstance(statement, dict):
                yield Statement.from_dict(statement)
            elif isinstance(statement, AccessPolicy):
                yield from statement._get_statements(request, view)
            elif isclass(statement) and issubclass(statement, AccessPolicy):
                yield from statement()._get_statements(request, view)
            else:
                raise ValueError(f"Invalid statement object type \"{type(statement)}\", "
                                 f"in policy {self} at index {index}")

    def _get_field_statements(self, key: str) -> Iterator[FieldStatement]:
        """
        Unify field statements to be FieldStatement objects.
        :param key: Policy field key (aka. serializer field attribute)
        :return: Generator of field statements
        :raises ValueError: A statement is not valid or incorrect type
        """
        for index, statement in enumerate(self.get_field_statements(key)):
            if isinstance(statement, FieldStatement):
                yield statement
            elif isinstance(statement, dict):
                yield FieldStatement.from_dict(statement)
            elif isinstance(statement, AccessPolicy):
                yield from statement._get_field_statements(key)
            elif isclass(statement) and issubclass(statement, AccessPolicy):
                yield from statement()._get_field_statements(key)
            else:
                raise ValueError(f"Invalid field permissions statement object type \"{type(statement)}\", "
                                 f"in policy {self} for \"{key}\" at index {index}")

    def _evaluate_statements(self, request, view, action: str) -> bool:
        """
        Evaluate access statements to determine if to allow or deny request access.
        :param request: Current request
        :param view: Policy view
        :param action: View action
        :return: Boolean if to allow or deny access
        """
        grouped_statements = {"deny": [], "allow": [], "default": []}
        for statement in self._get_statements(request, view):
            grouped_statements[statement.effect or "default"].append(statement)

        # Empty statements
        if not any(grouped_statements.values()):
            return False

        # No "deny" match
        if any(statement.evaluate(self, request, view, action)
               for statement in grouped_statements["deny"]):
            return False

        # One "allow" match
        if any(statement.evaluate(self, request, view, action)
               for statement in grouped_statements["allow"]):
            return True

        # All default effect match
        return grouped_statements["default"] and all(
            statement.evaluate(self, request, view, action)
            for statement in grouped_statements["default"]
        )

    def __call__(self, *args, **kwargs) -> "AccessPolicy":
        # When access policy is given as object to DRF view.permission_classes, it attempts to convert it to an object
        # by calling it with no arguments (usually it calls the __init__ for it is as a class)
        # This is a fix to allow the access policy to be provided as an object to the DRF view
        return self

    def __repr__(self):
        if self.id:
            return f"{self.__class__.__name__} (id={self.id})"
        else:
            return self.__class__.__name__
