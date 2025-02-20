# app/services/homework_service.py

from app.models import Homework

def create_homework(lesson, day, topic, tasks):
    homework = Homework.objects.create(
        lesson=lesson,
        day=day,
        topic=topic,
        tasks=tasks
    )
    return homework

def get_homeworks_for_student(student):
    # Выбираем домашние задания для уроков, в которых участвует студент.
    return Homework.objects.filter(lesson__students=student)
