from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from app.models import Teacher

def get_active_user(username, password):
    """
    Возвращает активного пользователя, если учетные данные верны.
    """
    user = authenticate(username=username, password=password)
    if not user or not user.is_active:
        raise AuthenticationFailed("No active account found with the given credentials")
    return user

def get_teacher_by_user(user):
    """
    Возвращает объект Teacher, связанный с данным пользователем.
    """
    try:
        return user.teacher
    except Teacher.DoesNotExist:
        raise ValueError("User is not associated with a teacher.")
