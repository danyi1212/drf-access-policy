# Serializer Field Permissions

Policies may define `field_permissions` that can **dynamically restrict access** to certain serializer fields 
by modifying properties such as `read_only` and `write_only`.
The field statements are configured as a dictionary where each key refers to a field attribute, 
and the value is a list of Field Statements. Example:
```python
class MyPolicy(AccessPolicy):
    field_permissions = {
        "read_only": [
            {"principal": "*", "fields": "last_login"},
        ],
        "write_only": [
            FieldStatement(principal="admin", fields="password"),
        ],
    }
```

In the example above, we've set `last_login` as read-only for everyone, and `password` as write-only for superusers.

## Field Access Evaluation Logic

The logic is very similar to the [access policy evaluation logic](../policy_logic.md).

To determine which fields to restrict on the serializer, two steps are applied:
1. **Matching Statements**: A statement is applicable when the request user matches any of the statement's principals.
2. **Filtering**: A field is set to be modified if all the following:
   * Listed in any of the matching statement where effect is "deny".
   * Not listed in any of the matching statement where effect is "allow".
   * Listed in any of the matching statements. 

By default, fields listed in a matching statement get restricted, unless it is listed in a matching statement `allow`. 
Fields listed in a matching statement `deny` will get restricted regardless of `allow` statements.

## Restriction Application

The policy applies the restriction by modifying the serializer field's attributes.
For each key defined in the `field_permissions`, the matching fields get determined, 
and the attribute with name of the key get set as `True`.

To apply access policy on a serializer you need to inherit from `FieldAccessMixin` and set `access_policy` in the Meta.
```python
class MyPolicy(AccessPolicy):
    fields_permissions = {
        "read_only": [
            {"principal": "*", "fields": "username"},
            {"principal": "admin", "fields": "username", "effect": "allow"},
        ]
    }

    
class MySerializer(ModelSerializer):

    class Meta:
        model = User
        fields = ("id", "username", "email")
        access_policy = MyPolicy
```

Or also using policy object

```python
class MySerializer(ModelSerializer):

    class Meta:
        model = User
        fields = ("id", "username", "email")
        access_policy = AccessPolicy(fields_permissions={
            "read_only": [
                {"principal": "*", "fields": "username"},
                {"principal": "admin", "fields": "username", "effect": "allow"},
            ]
        })
```

:warning: **Note:** Field permissions can only enable `read_only`, `write_only` or any other attribute. 
They can **never disable** an existing `read_only=True` already configured on a serializer field.