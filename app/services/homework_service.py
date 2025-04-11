from app.models import Homework, Student, Lesson
from app.serializers import HomeworkSerializer

def create_homework(student_id, teacher, lesson_id, day, topic, tasks):
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        raise ValueError(f"Student with ID {student_id} does not exist.")

    try:
        lesson = Lesson.objects.get(id=lesson_id)
    except Lesson.DoesNotExist:
        raise ValueError(f"Lesson with ID {lesson_id} does not exist.")

    if not topic:
        topic = lesson.name
        # Создаём домашнее задание
    if not topic and not lesson:
        raise ValueError(f"Enter topic name or lesson id")

    homework = Homework.objects.create(
        student=student,
        teacher=teacher,
        day=day,
        topic=topic,
        tasks=tasks
    )

    # Сериализуем объект Homework для возвращения данных
    serializer = HomeworkSerializer(homework)
    return serializer.data


def get_homeworks_for_student(student_id):
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        raise ValueError(f"Student with ID {student_id} does not exist.")

    return Homework.objects.filter(student=student)