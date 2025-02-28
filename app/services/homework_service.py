from app.models import Homework, Student
from app.serializers import HomeworkSerializer

def create_homework(student_id, day, topic, tasks):
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        raise ValueError(f"Student with ID {student_id} does not exist.")

    # Создаём домашнее задание
    homework = Homework.objects.create(
        student=student,
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