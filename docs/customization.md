# Customizing User Group / Role Values

If you aren't using Django's built-in auth app, you may need to define a custom way to retrieve the role/group names to which the user belongs.

You can override the `is_member_in_group` method on your policy and implement there your logic. 

In the example below, the user model has a many-to-many relationship named "roles", 
which specify their name in a field called "title".
```python
class UserAccessPolicy(AccessPolicy):
    # ... other properties and methods ...

    def is_member_in_group(self, user: User, groups: List[str]) -> bool:
        return user.roles.filter(title__in=groups).exists()
```

You can also still define the **legacy method** called `get_user_group_values` on your policy class.
It should provide all possible group names for a user.
```python
class UserAccessPolicy(AccessPolicy):
    # ... other properties and methods ...

    def get_user_group_values(self, user) -> List[str]:
        return list(user.roles.values_list("title", flat=True))
```

# Customizing Principal Prefixes

By default, the prefixes to identify the type of principle (user or group) are "id:" and "group:", respectively. 
You can customize this by setting these properties on your policy class:
```python
class FriendRequestPolicy(AccessPolicy):
    group_prefix = "role:"
    id_prefix = "staff_id:"

    # ... the rest of you policy definition ...
```
