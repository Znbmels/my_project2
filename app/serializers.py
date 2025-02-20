from rest_framework import serializers
from app.models import Lesson, Homework, ErrorLog, Student
from django.contrib.auth import get_user_model

User = get_user_model()  # Используем вашу кастомную модель

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role']
        extra_kwargs = {
            'password': {'write_only': True},  # Скрыть пароль в ответах
        }

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            role=validated_data.get('role', 'student'),  # Добавляем роль
        )
        user.set_password(validated_data['password'])  # Хэширование пароля
        user.save()
        return user


class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Student
        fields = ['id', 'user', 'name']


class HomeworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Homework
        fields = ['id', 'lesson', 'day', 'topic', 'tasks']


class ErrorLogSerializer(serializers.ModelSerializer):
    student = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='student')  # Фильтруем только студентов
    )

    class Meta:
        model = ErrorLog
        fields = ['id', 'student', 'lesson', 'description']


class LessonSerializer(serializers.ModelSerializer):
    homeworks = serializers.SerializerMethodField()
    errors = ErrorLogSerializer(many=True, read_only=True, source='errorlog_set')

    class Meta:
        model = Lesson
        fields = [
            'id', 'day_of_week', 'start_time', 'end_time', 'zoom_link',
            'students', 'homeworks', 'errors'
        ]

    def get_homeworks(self, obj):
        return HomeworkSerializer(obj.homework_set.all(), many=True).data


class LessonMinimalSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)  # Имя учителя

    class Meta:
        model = Lesson
        fields = ['id', 'day_of_week', 'start_time', 'end_time', 'zoom_link', 'teacher_name']
