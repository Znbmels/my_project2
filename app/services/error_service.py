# app/services/error_service.py
from app.models import ErrorLog, Student, Lesson  # Добавьте импорт Lesson

def create_error_log(student_id, lesson_id, description):
    """
    Создает запись об ошибке для указанного студента и урока.
    """
    try:
        student = Student.objects.get(id=student_id)
        lesson = Lesson.objects.get(id=lesson_id)  # Теперь Lesson доступен
        error_log = ErrorLog.objects.create(
            student=student,
            lesson=lesson,
            description=description
        )
        return error_log
    except Student.DoesNotExist:
        raise ValueError("Student with the given ID does not exist.")
    except Lesson.DoesNotExist:
        raise ValueError("Lesson with the given ID does not exist.")

def get_errors_for_student(student):
    return ErrorLog.objects.filter(student=student)
