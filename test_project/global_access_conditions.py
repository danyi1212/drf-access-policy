from rest_access_policy.utils import object_level_condition

not_a_func = True


def is_a_func(request, view, action):
    return True


def simple_condition(request, view, action):
    return True


def is_a_cat(request, view, action, name: str):
    if name == "Garfield":
        return True
    return False


@object_level_condition()
def user_must_be(request, view, action, obj, arg):
    if obj:
        return getattr(obj, arg) == request.user
    else:
        return True
