import logging
from django.views import View
from django.http import JsonResponse
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from app.models import User, Homework, ErrorLog, Lesson, Student
from app.services.utils import get_teacher_by_user
from app.serializers import (
    UserSerializer,
    LessonSerializer,
    HomeworkSerializer,
    ErrorLogSerializer,
    LessonMinimalSerializer,
)
from app.services.lesson_service import create_lesson, get_lessons_by_teacher
from app.services.homework_service import create_homework, get_homeworks_for_student
from app.services.error_service import create_error_log, get_errors_for_student
from app.services.teacher_service import get_teacher_by_user
from app.services.student_service import get_student_by_user

logger = logging.getLogger(__name__)


# Root view providing information about API endpoints
class ApiRootView(View):
    def get(self, request, *args, **kwargs):
        data = {
            'message': 'Welcome to the API root!',
            'endpoints': {
                'register': '/register/',
                'login': '/login/',
                'lessons': '/lessons/',
                'homeworks': '/homeworks/',
                'errors': '/errors/',
            }
        }
        return JsonResponse(data)


# View for user registration
class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # Сохранение пользователя с хэшированием пароля
            return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# View for user login with JWT token generation
class LoginView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)  # Authenticate user credentials
        if user:
            refresh = RefreshToken.for_user(user)  # Generate JWT tokens
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        else:
            logger.error(f"Authentication failed for user: {username}")
            return Response({"detail": "No active account found with the given credentials"},
                            status=status.HTTP_400_BAD_REQUEST)


# View to retrieve all homework assignments
class HomeworkListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            homeworks = Homework.objects.select_related("lesson").all()  # Fetch homework with related lesson
            serializer = HomeworkSerializer(homeworks, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching homeworks: {e}")
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# View to create a new homework assignment (teachers only)
class HomeworkCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            if not hasattr(request.user, "teacher"):
                return Response({"error": "Only teachers can create homework assignments"},
                                status=status.HTTP_403_FORBIDDEN)
            serializer = HomeworkSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()  # Save homework data
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating homework: {e}")
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# View to retrieve all error logs
class ErrorLogListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            errors = ErrorLog.objects.select_related("student", "lesson").all()  # Fetch related data
            serializer = ErrorLogSerializer(errors, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching error logs: {e}")
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# View to create a new error log (teachers only)
class ErrorLogCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Получаем данные из запроса
            student_id = request.data.get("student")
            lesson_id = request.data.get("lesson")
            description = request.data.get("description")

            # Создаем запись об ошибке через сервис
            error_log = create_error_log(
                student_id=student_id,
                lesson_id=lesson_id,
                description=description
            )

            # Сериализуем данные
            serializer = ErrorLogSerializer(error_log)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Ошибка при создании записи об ошибке: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# View to create a lesson (teachers only)
class LessonCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Проверка, является ли пользователь учителем
            if not hasattr(request.user, "teacher"):
                return Response({"error": "Only teachers can create lessons"}, status=status.HTTP_403_FORBIDDEN)

            # Получаем объект учителя
            teacher = get_teacher_by_user(request.user)

            # Добавляем учителя в данные запроса
            data = request.data.copy()
            data["teacher"] = teacher.id  # Передаем ID учителя

            # Валидация данных через сериализатор
            serializer = LessonSerializer(data=data)
            if serializer.is_valid():
                # Сохраняем данные через сериализатор
                lesson = serializer.save()

                # Возвращаем созданный урок
                return Response(LessonSerializer(lesson).data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error creating lesson: {e}")
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# View to list lessons for a teacher
class LessonListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            if not hasattr(request.user, "teacher"):
                return Response({"error": "Only teachers can view their lessons"},
                                status=status.HTTP_403_FORBIDDEN)
            teacher = get_teacher_by_user(request.user)  # Fetch teacher object
            lessons = get_lessons_by_teacher(teacher)  # Fetch lessons for teacher
            serializer = LessonSerializer(lessons, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching lessons: {e}")
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# View to list homeworks for a student
class StudentHomeworkListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            if not hasattr(request.user, "student"):
                return Response({"error": "Only students can view their homework assignments"},
                                status=status.HTTP_403_FORBIDDEN)

            student = request.user.student
            lessons = Lesson.objects.filter(students=student)
            homeworks = Homework.objects.filter(lesson__in=lessons)
            logger.debug(f"Homeworks for student: {homeworks}")  # Логирование
            serializer = HomeworkSerializer(homeworks, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error fetching student homework: {e}")
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# View to list error logs for a student
class StudentErrorListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            if not hasattr(request.user, "student"):
                return Response({"error": "Only students can view their error logs"},
                                status=status.HTTP_403_FORBIDDEN)

            student = request.user.student  # Fetch student object
            errors = ErrorLog.objects.filter(student=student)  # Используем объект Student
            serializer = ErrorLogSerializer(errors, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error fetching student error logs: {e}")
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# View to list lessons for a specific student
class StudentLessonsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Проверяем, является ли пользователь студентом
            if not hasattr(request.user, "student"):
                return Response(
                    {"error": "Only students can view their lessons"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Получаем связанные с этим студентом уроки
            student = request.user.student
            lessons = Lesson.objects.filter(students=student)

            logger.debug(f"Lessons for student {student.id}: {lessons}")

            # Используем минимальный сериализатор для вывода
            serializer = LessonMinimalSerializer(lessons, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error fetching lessons for student: {e}")
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from django.shortcuts import render

# Create your views here.
