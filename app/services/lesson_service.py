from app.models import Lesson, Teacher, Student
import logging

logger = logging.getLogger(__name__)


def create_lesson(teacher, students=None, **kwargs):
    """
    Создает урок и добавляет студентов, если они указаны.
    """
    if not isinstance(teacher, Teacher):
        raise ValueError("Invalid teacher object")

    if students and not all(isinstance(student, (int, Student)) for student in students):
        raise ValueError("Students should be a list of IDs or Student objects")

    try:
        # Создаем урок
        lesson = Lesson.objects.create(teacher=teacher, **kwargs)

        # Устанавливаем студентов, если они переданы
        if students:
            lesson.students.set(students)

        return lesson
    except Exception as e:
        logger.error(f"Error creating lesson: {e}")
        raise


def get_lessons_by_teacher(teacher):
    """
    Возвращает список уроков, связанных с данным учителем,
    включая предзагрузку связанных студентов.
    """
    if not isinstance(teacher, Teacher):
        raise ValueError("Invalid teacher object")

    return Lesson.objects.filter(teacher=teacher).prefetch_related('students')
