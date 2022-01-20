# pylint: disable=not-callable
from typing import Type, Union

from rest_access_policy.access_policy import AccessPolicy


class AccessViewSetMixin:
    access_policy: Union[AccessPolicy, Type[AccessPolicy]] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not (isinstance(self.access_policy, AccessPolicy)
                or isinstance(self.access_policy, type) and issubclass(self.access_policy, AccessPolicy)):
            raise ValueError(f"{self.__class__.__name__}.access_policy must be an AccessPolicy or subclass")

    def get_permissions(self):
        """
        Inject access policy to view's permissions
        :return: List of permission objects
        """
        access_policy = self.access_policy if isinstance(self.access_policy, AccessPolicy) else self.access_policy()
        return [access_policy, *super().get_permissions()]
