from app.models import Task, Ayah, Surah, Homework, Student, TasksBuffer, Murajaah
from rest_framework.exceptions import ValidationError
from datetime import timedelta
import datetime
from app.serializers import HomeworkSerializer

def create_homework(student_id, teacher, lesson_id, day, topic, tasks):
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        raise ValueError(f"Student with ID {student_id} does not exist.")

    homework = Homework.objects.create(
        student=student,
        day=day,
        note=note
    )

    # Сериализуем объект Homework для возвращения данных
    serializer = HomeworkSerializer(homework)
    return serializer.data

def buffer_update(homework):
    student = homework.student
    tasks = homework.tasks.all()
    buffer, created = TasksBuffer.objects.get_or_create(student=student)
    for task in tasks:
        ayah = task.ayah
        if task.is_done:
            # Добавляем в буфер, если ещё не добавлен
            if not buffer.ayahs.filter(id=ayah.id).exists():  # проверка, если аят уже в буфере
                buffer.ayahs.add(ayah)  # используем метод add
        else:
            # Удаляем из буфера, если ранее был добавлен
            buffer.ayahs.remove(ayah)

def create_tasks(student):
    day = datetime.date.today() # устанавливаем начальную дату — сегодня.
    # определяем, с какого аята начинать:
    if student.current_ayah is not None:
        current_ayah = student.current_ayah # если у ученика есть current_ayah, берем его;
    else:
        current_ayah = Ayah.objects.get(number=1)
        student.current_ayah = Ayah.objects.get(number=1)
    for i in range(7):
        homework, _ = Homework.objects.get_or_create(student=student, day=day, note='')
        Task.objects.filter(homework_id=homework.id).delete()
        for j in range(3):
            print(current_ayah)
            while TasksBuffer.objects.filter(student=student, ayahs=current_ayah).exists():
                current_ayah = Ayah.objects.get(number=current_ayah.number + 1)
                print(current_ayah , "произошло изменение")
            Task.objects.create(
            homework_id=homework.id,
            surah_id=current_ayah.surah.id,
            ayah=current_ayah
            ) # создаём новый таск с текущим аятом и сурой.
            try:
                current_ayah = Ayah.objects.get(number=current_ayah.number + 1)
            except Ayah.DoesNotExist:
                pass
        day += timedelta(days=1)
    student.current_ayah = Ayah.objects.get(number=1)
    student.save()
    return None

def create_murajaah_tasks(student):
    today = datetime.date.today()
    previous_day = today - timedelta(days=1)
    pages_per_day = student.murajaah_total_pages
    start_page = student.murajaah_start_page
    previous_homework = Homework.objects.filter(student=student, day=today - timedelta(days=1)).first()
    previous_murajaah = None
    if previous_homework:
        previous_murajaah = Murajaah.objects.filter(homework=previous_homework).first()
    for i in range(7):
        end_page = min(604, start_page + pages_per_day - 1)
        day = today + datetime.timedelta(days=i)
        homework, created = Homework.objects.get_or_create(student=student, day=day)
        if not Murajaah.objects.filter(homework=homework).exists():
            if previous_murajaah:
                start_page = previous_murajaah.start_page
                end_page = start_page + pages_per_day - 1
            Murajaah.objects.create(
                            homework=homework,
                            start_page=start_page,
                            end_page=end_page
                        )
            start_page += pages_per_day
        elif not previous_murajaah.is_done:
            current_murajaah = Murajaah.objects.filter(homework=homework).first()
            previous_murajaah_data = {
                'start_page': current_murajaah.start_page,
                'end_page': current_murajaah.end_page,
            }
            Murajaah.objects.filter(homework=homework).update(start_page=previous_murajaah.start_page,
                                                              end_page=previous_murajaah.end_page)
            previous_murajaah = Murajaah(**previous_murajaah_data)
        else:
            print("Continue")
            continue
        current_murajaah = Murajaah.objects.filter(homework=homework).first()
    student.murajaah_start_page = start_page
    student.save()
    return None