# app/services/teacher_service.py

def get_teacher_by_user(user):
    # Предполагается, что у модели User есть связь OneToOne с Teacher
    return user.teacher
