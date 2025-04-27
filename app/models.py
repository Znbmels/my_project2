from django.db import models
from django.contrib.auth.models import AbstractUser

def validate_total_pages(value):
    if value > 604:
        raise ValidationError('Total pages cannot exceed 604.')

class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher')
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student')
    name = models.CharField(max_length=100)
    current_ayah = models.ForeignKey('Ayah', null=True, blank=True, on_delete=models.SET_NULL)
    murajaah_start_page = models.IntegerField(default = 1)
    murajaah_total_pages = models.IntegerField(validators=[validate_total_pages], default=10)
    last_task_update = models.DateField(null=True, blank=True, default=None)


    def __str__(self):
        return self.name

class Lesson(models.Model):
    name = models.CharField(max_length=255, default="Default Lesson Name")
    day_of_week = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, default=1  # ID учителя по умолчанию
    )
    day = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    zoom_link = models.URLField()
    students = models.ManyToManyField(Student, related_name='lessons')

    def __str__(self):
        return self.name

class Homework(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='homeworks')
    day = models.DateField()
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"({self.day})"

class HomeworkImage(models.Model):
    homework = models.ForeignKey('Homework', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='homework_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Mistake(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    homework = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='mistakes_for_homework', null=True,
                                 blank=True)
    description = models.TextField()
    is_fixed = models.BooleanField(default=False)  # Новое поле

    def __str__(self):
        return f"{self.student.name} in {self.homework.name}"

class MistakeImage(models.Model):
    mistake = models.ForeignKey('Mistake', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='mistake_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class VideoLesson(models.Model):
    title = models.CharField(max_length=200)
    video_url = models.URLField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='video_lessons')  # связь с пользователем
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Surah(models.Model):
    name = models.CharField(max_length=100)
    number = models.IntegerField()

class Ayah(models.Model):
    text = models.CharField(max_length=100)
    number = models.IntegerField()
    surah = models.ForeignKey(Surah, on_delete=models.CASCADE)
    transcription = models.TextField()

class Task(models.Model):
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='tasks')  # Указываем related_name
    # для Homework
    surah = models.ForeignKey(Surah, on_delete=models.CASCADE)
    ayah = models.ForeignKey(Ayah, on_delete=models.CASCADE)
    is_done = models.BooleanField(default=False)

class TasksBuffer(models.Model):
    student = models.OneToOneField('Student', on_delete=models.CASCADE, related_name='buffer')
    ayahs = models.ManyToManyField('Ayah', related_name='in_buffers')

    def __str__(self):
        return f"Buffer for {self.student}"

class Murajaah(models.Model):
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='murajaahs')
    start_page = models.IntegerField()
    end_page = models.IntegerField()
    is_done = models.BooleanField(default=False)

