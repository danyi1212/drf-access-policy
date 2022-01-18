# Policy Evaluation Logic

To determine whether access to a request is granted, two steps are applied:
1. **Matching Statements**: A statement is applicable to the current request if all the following:
   * The request user matches any of the statement's principals.
   * The name of the method/function matches any of its actions.
   * All conditions evaluate to true.
2. **Evaluating**: Access is granted if all the following:
   * None of the matching statement's effect is "deny". 
   * Any of the matching statement's effect of "allow".
   * All the statements matched.
   
By default, all requests are denied. Requests are implicitly denied if no `Allow` statements are found, 
and they are explicitly denied if any `Deny` statements are found. `Deny` statements *trump* `Allow` statements.

## Example
Consider the following access policy and `ViewSet`.

```python
class ArticleAccessPolicy(AccessPolicy):
    statements = [
        {
            "action": ["list", "retrieve"],
            "principal": "*",
            "effect": "allow"
        },
        {
            "action": "publish",
            "principal": "group:editor",
            "effect": "allow"            
        }
    ]


class ArticleViewSet(ModelViewSet):
    permission_classes = (ArticleAccessPolicy, )

    @action(method="POST")
    def publish(self, request, *args, **kwargs):
        pass
```

A user in the group `sales` is allowed to `list` and `retrieve` articles because of the first statement. 
They cannot `publish` because all access is implicitly denied, 
however uses in the group `editor` can `publish` due to the second statement.