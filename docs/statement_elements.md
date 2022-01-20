# Statement Elements

Policies are made up of many statements that together determine **who** can do **what** with your application and under what **conditions**.

There are two types of statements:
* **Access Statements**: Specified in `AccessPolicy.statements`
* **Field Permission Statements**: Specified in `AccessPolicy.field_permissions`

Statements listed in either of them can be written as dictionaries or `Statement` objects. Example:

```python
from rest_access_policy.access_policy import AccessPolicy
from rest_access_policy.statements import Statement, FieldStatement


class MyPolicy(AccessPolicy):
    statements = [
        Statement(principal="authenticated", action="post"),
        {"principal": "authenticated", "action": "post"},
    ]
    field_permissions = {"read_only": [
        FieldStatement(principal="admin", fields="*", effect="allow"),
        {'principal': "admin", 'fields': "*", 'effect': "allow"},
    ]}
```

## Access Statements

### principal _(required)_

<table>
    <tr>
        <td><b>Description</b></td>
        <td>
            Should match the user of the current request by identifying a group they belong to or their user ID.
        </td>
    </tr>
    <tr>
        <td><b>Special Values</b></td>
        <td>
            <ul>
                <li>
                    <code>"*"</code> (any user)
                </li>
                <li>
                    <code>"admin"</code> (user.is_superuser)
                </li>
                <li>
                    <code>"staff"</code> (user.is_staff)
                </li>
                <li>
                    <code>"active"</code> (user.is_active)
                </li>
                <li>
                    <code>"disabled"</code> (not user.is_active)
                </li>
                <li>
                    <code>"authenticated"</code> (not user.is_anonymous)
                </li>
                <li>
                    <code>"anonymous"</code> (user.is_anonymous)
                </li>
            </ul>
        </td>
    </tr>
    <tr>
        <td><b>Type</b></td>
        <td> <code>str | List[str]</code> </td>
    </tr>
    <tr>
        <td><b>Formats</b></td>
        <td>
            <ul>
                <li>
                   Match by group with <code>"group:{name}"</code>
                </li>
                <li>
                   Match by ID with <code>"id:{id}" </code>
                </li>
            </ul>      
        </td>
    </tr>
    <tr>
        <td><b>Examples</b></td>
        <td>
            <ul>
                <li>
                   <code>["group:admins", "id:9322"]</code>
                </li>
                <li>
                   <code>"id:5352"</code>
                </li>
                <li>
                    <code>["anonymous"]</code> 
                </li>
            </ul>
        </td>
    </tr>
</table>

### action _(required)_
<table>
    <tr>
        <td><b>Description</b></td>
        <td>
            The action or actions that the statement applies to. 
            The value should match the name of a view set method or the name of the view function.<br>
            Alternatively, you can use placeholders to match the current request's HTTP method.
        </td>
    </tr>
    <tr>
        <td><b>Type</b></td>
        <td><code>str | List[str]</code></td>
    </tr>
    <tr>
        <td><b>Special Values</b></td>
        <td>
            <ul>
                <li>
                    <code>"*"</code> (any action)
                </li>
                <li>
                    <code>"&lt;safe_methods&gt;"</code> (a read-only HTTP request: HEAD, GET, OPTIONS)
                </li>
                <li>
                    <code>"&lt;method:get|head|options|delete|put|patch|post&gt;"</code> (match a specific HTTP method)
                </li>
            </ul>
        </td>
    </tr>
    <tr>
        <td><b>Examples</b></td>
        <td>
            <ul>
                <li>
                    <code>["list", "destroy", "create"]</code>
                </li>
                <li>
                    <code>"&lt;safe_methods&gt;"</code> <br>
                </li>
                <li>
                     <code>["&lt;method:post&gt;"]</code>
                </li>
            </ul>
        </td>
    </tr>
</table>

### effect

<table>
    <tr>
        <td><b>Description</b></td>
        <td>
            Whether the statement, if it is in effect, should allow or deny access. 
            All access is denied by default, so use <code>deny</code> when you'd like to 
            override an <code>allow</code> statement that will also be in effect. 
            See <a href="policy_logic.md">Policy Evaluation Logic</a>
        </td>
    </tr>
    <tr>
        <td><b>Type</b></td>
        <td><code>str</code></td>
    </tr>
    <tr>
        <td><b>Values</b></td>
        <td>
            <ul>
                <li>
                   <code>"allow"</code>
                </li>
                <li>
                   <code>"deny"</code>
                </li>
            </ul>
        </td>
    </tr>
</table>

### condition
<table>
    <tr>
        <td><b>Description</b></td>
        <td>
            Name of a condition method that return boolean. Optionally, you can pass an argument to the condition 
            method like <code>{method_name}:{value}</code> (e.g. <code>user_must_be:owner</code>).<br>
            See <a href="policy_logic.md">Policy Evaluation Logic</a>
        </td>
    </tr>
    <tr>
        <td><b>Type</b></td>
        <td><code>str | List[str]</code></td>
    </tr>
    <tr>
        <td><b>Examples</b></td>
        <td>
            <ul>
                <li>
                   <code>"is_manager_of_account"</code> 
                </li>
                <li>
                   <code>"is_author_of_post"</code>
                </li>
                <li>
                    <code>["balance_is_positive", "account_is_not_frozen"]`</code>
                </li>
                <li>
                    <code>"user_must_be:account_manager"</code>
                </li>
            </ul>
        </td>
    </tr>
</table>

### condition_expression
<table>
    <tr>
        <td><b>Description</b></td>
        <td>
            Same as the <code>condition</code> element, but with added support for evaluating boolean combinations.
            Syntax is similar to Python conditions.
        </td>
    </tr>
    <tr>
        <td><b>Type</b></td>
        <td><code>str | List[str]</code></td>
    </tr>
    <tr>
        <td><b>Examples</b></td>
        <td>
            <ul>
                <li>
                    <code>["(is_request_from_account_owner or is_FBI_request)"]</code>
                </li>
                <li>
                    <code>"is_sunny and is_weekend"</code>
                </li>
                <li>
                    <code>["is_tasty", "not is_expensive"]</code>
                </li>
            </ul>
        </td>
    </tr>
</table>

## Field Permission Statements

### principal _(required)_
_Same as on Access Statements_
<table>
    <tr>
        <td><b>Description</b></td>
        <td>
            Should match the user of the current request by identifying a group they belong to or their user ID.
        </td>
    </tr>
    <tr>
        <td><b>Special Values</b></td>
        <td>
            <ul>
                <li>
                    <code>"*"</code> (any user)
                </li>
                <li>
                    <code>"admin"</code> (user.is_superuser)
                </li>
                <li>
                    <code>"staff"</code> (user.is_staff)
                </li>
                <li>
                    <code>"active"</code> (user.is_active)
                </li>
                <li>
                    <code>"disabled"</code> (not user.is_active)
                </li>
                <li>
                    <code>"authenticated"</code> (not user.is_anonymous)
                </li>
                <li>
                    <code>"anonymous"</code> (user.is_anonymous)
                </li>
            </ul>
        </td>
    </tr>
    <tr>
        <td><b>Type</b></td>
        <td> <code>str | List[str]</code> </td>
    </tr>
    <tr>
        <td><b>Formats</b></td>
        <td>
            <ul>
                <li>
                   Match by group with <code>"group:{name}"</code>
                </li>
                <li>
                   Match by ID with <code>"id:{id}" </code>
                </li>
            </ul>      
        </td>
    </tr>
    <tr>
        <td><b>Examples</b></td>
        <td>
            <ul>
                <li>
                   <code>["group:admins", "id:9322"]</code>
                </li>
                <li>
                   <code>"id:5352"</code>
                </li>
                <li>
                    <code>["anonymous"]</code> 
                </li>
            </ul>
        </td>
    </tr>
</table>

### fields (required)
<table>
    <tr>
        <td><b>Description</b></td>
        <td>
            List of fields that should be modified when matched. 
        </td>
    </tr>
    <tr>
        <td><b>Special Values</b></td>
        <td>
            <ul>
                <li>
                    <code>"*"</code> (all fields)
                </li>
            </ul>
        </td>
    </tr>
    <tr>
        <td><b>Type</b></td>
        <td> <code>str | List[str]</code> </td>
    </tr>
    <tr>
        <td><b>Examples</b></td>
        <td>
            <ul>
                <li>
                   <code>["username", "password"]</code>
                </li>
                <li>
                   <code>"*"</code>
                </li>
            </ul>
        </td>
    </tr>
</table>

### effect

<table>
    <tr>
        <td><b>Description</b></td>
        <td>
            Whether the statement is to allow or deny the access to fields.
            See <a href="usage/field_permissions.md">Serializer Field Permissions</a>
        </td>
    </tr>
    <tr>
        <td><b>Type</b></td>
        <td><code>str</code></td>
    </tr>
    <tr>
        <td><b>Values</b></td>
        <td>
            <ul>
                <li>
                   <code>"allow"</code>
                </li>
                <li>
                   <code>"deny"</code>
                </li>
            </ul>
        </td>
    </tr>
</table>


## Using Policies as Statements

It is possible to nest policies inside other policies.
This way, all statements from the child policy are **copied** to the parent policy.

This is useful to avoid rewriting statements that should be defined on multiple policies.

Example: 
```python
class ChildPolicy(AccessPolicy):
    statements = [
        Statement(principal="anonymous", action="<safe_method>", effect="allow"),
    ]


class ParentPolicy(AccessPolicy):
    statements = [
        {"principal": "*", "action": "create", "effect": "allow"},
        ChildPolicy(),
        {"principal": "anonymous", "action": "retrieve", "effect": "deny"}
    ]
```

Is the same as:
```python
class MyPolicy(AccessPolicy):
    statements = [
        {"principal": "*", "action": "create", "effect": "allow"},
        Statement(principal="anonymous", action="<safe_method>", effect="allow"),
        {"principal": "anonymous", "action": "retrieve", "effect": "deny"}
    ]
```
