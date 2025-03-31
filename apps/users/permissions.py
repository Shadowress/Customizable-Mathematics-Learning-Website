from apps.users.models import CustomUser


def normal_user_required(user) -> bool:
    return user.is_authenticated and user.role == CustomUser.NORMAL_USER


def content_manager_required(user) -> bool:
    return user.is_authenticated and user.role == CustomUser.CONTENT_MANAGER
