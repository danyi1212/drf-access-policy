# Object-Level Permissions / Custom Conditions

What about object-level permissions? 
You can easily check object-level access in a custom condition that's evaluated to determine whether the statement takes effect. 
This condition is passed the `view` instance, so you can get the model instance with a call to `view.get_object()`. 
You can even reference multiple conditions, to keep your access methods focused and testable, as well as parametrize these conditions with arguments.

```python hl_lines="14 25"
class AccountAccessPolicy(AccessPolicy):
    statements = [
        ## ... other statements ...
        {
            "action": ["withdraw"],
            "principal": ["*"],
            "effect": "allow",
            "condition": ["balance_is_positive", "user_must_be:owner"]
        },
        {
            "action": ["upgrade_to_gold_status"],
            "principal": ["*"],
            "effect": "allow",
            "condition": ["user_must_be:account_advisor"]
        }
        ## ... other statements ...
    ]

    def balance_is_positive(self, request, view, action) -> bool:
        account = view.get_object()
        return account.balance > 0

    def user_must_be(self, request, view, action, field: str) -> bool:
        account = view.get_object()
        return getattr(account, field) == request.user
```

Notice how we're re-using the `user_must_be` method by parameterizing it with the model field that should be equal for 
the user of the request: the statement will only be effective if this condition passes.

You can also utilize a utility decorator for making an object-level condition, that performs `view.get_object()` and 
pass the object as an argument to the condition function.

When `view.get_object()` does not exist or fails, the condition is evaluated as False. 
This can be changed using `default=True`. 
You can also allow the exception to propagate by setting `raise_exception=True`.

```python
from rest_access_policy.utils import object_level_condition


@object_level_condition(default=True)
def user_must_be(request, view, action, obj, arg):
    return getattr(obj, arg) == request.user
```

If you have multiple custom methods defined on the policy, you can construct boolean expressions to combine them. 
The syntax is the same as Python's boolean expressions.

Note that the `condition_expression` element is used instead of `condition`.

```python
class AccountAccessPolicy(AccessPolicy):
    statements = [
        {
            "action": ["freeze"],
            "principal": ["*"],
            "effect": "allow",
            "condition_expression": ["(is_request_from_account_owner or is_FBI_request)"]
        },
    ]

    def is_FBI_request(self, request, view, action) -> bool:
        return is_request_from_fbi(request)

    def is_request_from_account_owner(self, request, view, action) -> bool:
        return account.owner == request.user
```
