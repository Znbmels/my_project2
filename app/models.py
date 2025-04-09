from django.db import models
from django.contrib.auth.models import AbstractUser


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


class Homework(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='homeworks')
    lesson = models.ForeignKey( Lesson, on_delete=models.CASCADE, related_name='homeworks', null=True, blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    day = models.DateField()
    topic = models.CharField(max_length=255)
    tasks = models.JSONField()
    note = models.TextField(blank=True, null=True)
    is_corrected = models.BooleanField(default=False)
    is_done = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.topic} ({self.day})"

class HomeworkImage(models.Model):
    homework = models.ForeignKey('Homework', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='homework_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class ErrorLog(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='errorlog_set')  # related_name
    description = models.TextField()
    is_corrected = models.BooleanField(default=False)  # Новое поле

    def __str__(self):
        return f"Error for {self.student.name} in {self.lesson.name}"

class VideoLesson(models.Model):
    title = models.CharField(max_length=200)
    video_url = models.URLField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='video_lessons')  # связь с пользователем
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title