# Re-Usable Conditions / Permissions

You can re-use conditions across policies by defining them globally in a module and point to it via the settings.
In this setting you can also provide a `List` of paths to search in multiple modules. 

```python
# in your project settings.py

DRF_ACCESS_POLICY = {"reusable_conditions": ["myproject.global_access_conditions"]}
```

```python
# in myproject.global_access_conditions.py

def is_the_weather_nice(request, view, action: str) -> bool:
    data = weather_api.load_today()
    return data["temperature"] > 68

def user_must_be(self, request, view, action, field: str) -> bool:
    account = view.get_object()
    return getattr(account, field) == request.user
```

The searching for condition methods specified in the `condition` or `condition_expression` properties is done first for 
methods with **matching names on the policy**, and then by the order of modules defined in the `reusable_conditions`
setting.
