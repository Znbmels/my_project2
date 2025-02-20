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


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student')
    name = models.CharField(max_length=100)


class Lesson(models.Model):
    day_of_week = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()
    teacher = models.ForeignKey(
        'app.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=1  # ID учителя по умолчанию
    )

    zoom_link = models.URLField()
    students = models.ManyToManyField(Student, related_name='lessons')


class Homework(models.Model):
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE, related_name='homework_set')
    day = models.DateField()
    topic = models.CharField(max_length=255)
    tasks = models.JSONField()

    def __str__(self):
        return f"{self.topic} ({self.day})"

class ErrorLog(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='errorlog_set')  # related_name
    description = models.TextField()