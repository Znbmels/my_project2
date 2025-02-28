# app/services/homework_service.py

from app.models import Homework

def create_homework(student, day, topic, tasks):
    homework = Homework.objects.create(
        student=student,
        day=day,
        topic=topic,
        tasks=tasks
    )
    return homework

def get_homeworks_for_student(student):
    # Выбираем домашние задания для уроков, в которых участвует студент.
    return Homework.objects.filter(student=student)
