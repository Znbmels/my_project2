# app/services/student_service.py

def get_student_by_user(user):
    # Предполагается, что у модели User есть связь OneToOne со Student
    return user.student
