from rest_framework import serializers
from app.models import Lesson, Homework, Mistake, Student, VideoLesson, HomeworkImage, MistakeImage
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

class HomeworkImageUploadSerializer(serializers.Serializer): #Сериализатор для POST-запроса
    homework = serializers.IntegerField()
    images = serializers.ListField(
        child=serializers.ImageField(), write_only=True
    )

    def create(self, validated_data):
        homework_id = validated_data['homework']
        images = validated_data['images']

        instances = [
            HomeworkImage(homework_id=homework_id, image=image)
            for image in images
        ]
        # bulk_create возвращает список, мы это сохраняем в self.instance
        self.instance = HomeworkImage.objects.bulk_create(instances)
        return self.instance

    def to_representation(self, instance):
        # instance — список, сериализуем вручную
        return [
            {
                "id": img.id,
                "homework": img.homework_id,
                "image": img.image.url,
                "uploaded_at": img.uploaded_at,
            }
            for img in instance
        ]

class HomeworkImageSerializer(serializers.ModelSerializer): #Сериализатор для GET-запроса
    class Meta:
        model = HomeworkImage
        fields = ['id', 'homework', 'image', 'uploaded_at']

class HomeworkSerializer(serializers.ModelSerializer):
    images = HomeworkImageSerializer(many=True, read_only=True)

    class Meta:
        model = Homework
        fields = ['id', 'student', 'teacher', 'day', 'topic', 'tasks', 'is_corrected', 'is_done', 'images']

    def validate_student(self, value):
        if not Student.objects.filter(id=value).exists():
            raise serializers.ValidationError("Student not found.")
        return value

class MistakeImageUploadSerializer(serializers.Serializer): #Сериализатор для POST-запроса
    mistake = serializers.IntegerField()
    images = serializers.ListField(
        child=serializers.ImageField(), write_only=True
    )

    def create(self, validated_data):
        mistake_id = validated_data['mistake']
        images = validated_data['images']

        instances = [
            MistakeImage(mistake_id=mistake_id, image=image)
            for image in images
        ]
        # bulk_create возвращает список, мы это сохраняем в self.instance
        self.instance = MistakeImage.objects.bulk_create(instances)
        return self.instance

    def to_representation(self, instance):
        # instance — список, сериализуем вручную
        return [
            {
                "id": img.id,
                "mistake": img.mistake_id,
                "image": img.image.url,
                "uploaded_at": img.uploaded_at,
            }
            for img in instance
        ]

class MistakeImageSerializer(serializers.ModelSerializer): #Сериализатор для GET-запроса
    class Meta:
        model = MistakeImage
        fields = ['id', 'mistake', 'image', 'uploaded_at']

class MistakeSerializer(serializers.ModelSerializer):
    images = MistakeImageSerializer(many=True, read_only=True)
    class Meta:
        model = Mistake
        fields = ['id', 'student', 'lesson', 'description', 'is_fixed', 'images']

    def validate_student(self, value):
        if not Student.objects.filter(id=value).exists():
            raise serializers.ValidationError("Student not found.")
        return value

class LessonSerializer(serializers.ModelSerializer):
    homeworks = serializers.SerializerMethodField()
    errors = MistakeSerializer(many=True, read_only=True, source='mistake_set')

    class Meta:
        model = Lesson
        fields = [
            'id', 'day_of_week', 'start_time','day', 'end_time', 'zoom_link',
            'students', 'homeworks', 'errors', 'description'
        ]

    def get_homeworks(self, obj):
        return HomeworkSerializer(obj.homeworks.all(), many=True).data

class LessonMinimalSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)  # Имя учителя

    class Meta:
        model = Lesson
        fields = ['id', 'day_of_week', 'start_time', 'end_time', 'zoom_link', 'teacher_name', 'description']

class VideoLessonSerializer(serializers.ModelSerializer):
    creator = serializers.StringRelatedField(read_only=True)  # или просто поля, если вы хотите выводить имя

    class Meta:
        model = VideoLesson
        fields = ['id', 'title', 'video_url', 'creator', 'is_active']

    def create(self, validated_data):
        # Создаем новый объект VideoLesson с присвоением пользователя в поле creator
        return VideoLesson.objects.create(**validated_data)