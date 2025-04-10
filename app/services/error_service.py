# app/services/error_service.py
from app.models import Mistake, Student, Lesson  # Добавьте импорт Lesson

def create_mistake(student_id, lesson_id, description):
    """
    Создает запись об ошибке для указанного студента и урока.
    """
    try:
        student = Student.objects.get(id=student_id)
        lesson = Lesson.objects.get(id=lesson_id)  # Теперь Lesson доступен
        Mistake = Mistake.objects.create(
            student=student,
            lesson=lesson,
            description=description
        )
        return Mistake
    except Student.DoesNotExist:
        raise ValueError("Student with the given ID does not exist.")
    except Lesson.DoesNotExist:
        raise ValueError("Lesson with the given ID does not exist.")

def get_mistakes_for_student(student):
    return Mistake.objects.filter(student=student)
