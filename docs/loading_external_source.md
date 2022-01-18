# Loading Statements from External Source

If you don't want your policy statements hardcoded into the classes, you can load them from an external data source: 
a great step because you can change access rules without redeploying code. 

You can do this by overriding methods on your access policy:
* `get_policy_statements(self, request, view)` -> Get access statements (instead of `AccessPolicy.statements`)
* `get_fields_statements(self, key)` -> Get field statements for a key, aka. field attribute (instead of `AccessPolicy.field_permissions`)

Example:
```python
class UserAccessPolicy(AccessPolicy):
    id = 'user-policy'

    def get_policy_statements(self, request, view) -> list:
        # implement your way of getting statements
        statements = data_api.load_json(self.id)
        return json.loads(statements)
    
    def get_fields_statements(self, key: str) -> list:
        # implement your way of getting statements
        statements = data_api.load_json(self.id)
        return json.loads(statements)
```

You probably want to only define this method once on your own custom subclass of `AccessPolicy`, from which all your other access policies inherit.
