# app/services/error_service.py
from app.models import Mistake, Student, Lesson  # Добавьте импорт Lesson

def create_mistake(student_id, homework_id, description):
    # Создает запись об ошибке для указанного студента и ДЗ (на самом деле lesson).
    try:
        student = Student.objects.get(id=student_id)
        homework = Lesson.objects.get(id=homework_id)
        mistake = Mistake.objects.create(
            student=student,
            homework=homework,
            description=description
        )
        return mistake
    except Student.DoesNotExist:
        raise ValueError("Student with the given ID does not exist.")
    except Lesson.DoesNotExist:
        raise ValueError("Lesson with the given ID does not exist.")

def get_mistakes_for_student(student):
    return Mistake.objects.filter(student=student)
