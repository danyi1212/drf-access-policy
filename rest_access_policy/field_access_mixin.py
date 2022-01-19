# pylint: disable=protected-access, not-callable
from typing import Iterator, Type, Union, Set, Any

from rest_framework.fields import Field
from rest_framework.request import Request

from rest_access_policy.access_policy import AccessPolicy
from rest_access_policy.statements import FieldStatement


class FieldAccessMixin:

    def __init__(self, *args, **kwargs):
        self.serializer_context = kwargs.get("context", {})
        super().__init__(*args, **kwargs)

        for attribute in self.access_policy.field_permissions.keys():
            self._set_fields_attribute_from_policy(attribute, True)

    @property
    def access_policy(self) -> AccessPolicy:
        """ Get serializer's access policy from Meta """
        meta = getattr(self, "Meta", None)
        access_policy: Union[AccessPolicy, Type[AccessPolicy]] = getattr(meta, "access_policy", None)
        if access_policy is None:
            raise ValueError("Must set Meta.access_policy for FieldAccessMixin")

        if isinstance(access_policy, AccessPolicy):
            return access_policy

        if not (isinstance(access_policy, type) and issubclass(access_policy, AccessPolicy)):
            raise ValueError(f"{self.__class__.__name__}.Meta.access_policy must be an AccessPolicy or subclass")

        return access_policy()

    @property
    def request(self) -> Request:
        """
        Get request from serializer context
        """
        request = self.serializer_context.get("request")
        if not request:
            raise KeyError(f"Unable to find request in serializer context on {self.__class__.__name__} "
                           f"(required for FieldAccessMixin)")

        return request

    def _get_statements(self, key: str) -> Iterator[FieldStatement]:
        return self.access_policy._get_field_statements(key)

    def _get_fields_from_statements(self, key: str) -> Set[Field]:
        """
        Get all fields that should be modified
        :param key: Fields matching specific key (aka. serializer field attribute)
        :return: Set of fields matching the statements
        """
        grouped_fields = {"deny": set(), "allow": set(), "default": set()}
        for statement in self._get_statements(key):
            if statement.match_principal(self.access_policy, self.request, None, ""):
                effect = statement.effect or "default"
                grouped_fields[effect] = grouped_fields[effect].union(statement.get_fields())

        if "*" in grouped_fields["deny"]:
            return set(self.fields.values())
        if "*" in grouped_fields["allow"]:
            grouped_fields["default"] = set()
        if "*" in grouped_fields["default"]:
            grouped_fields["default"] = set(self.fields.keys())

        matched_fields = {*grouped_fields["deny"], *(grouped_fields["default"] - grouped_fields["allow"])}
        return {
            field for name, field in self.fields.items()
            if name in matched_fields
        }

    def _set_fields_attribute_from_policy(self, attribute: str, value: Any) -> None:
        """
        Set attribute to value for all fields matching policy statements
        :param attribute: Field's attribute to modify
        :param value: The value to set for matching fields
        """
        for field in self._get_fields_from_statements(attribute):
            if hasattr(field, attribute):
                setattr(field, attribute, value)
