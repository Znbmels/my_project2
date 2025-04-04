import logging
from collections import defaultdict
from django.views import View
from django.http import JsonResponse
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from app.models import User, Homework, ErrorLog, Lesson, Student, VideoLesson
from app.services.utils import get_teacher_by_user
from app.serializers import (
    UserSerializer,
    LessonSerializer,
    HomeworkSerializer,
    ErrorLogSerializer,
    LessonMinimalSerializer,
    VideoLessonSerializer,
    StudentSerializer,
)
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
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
            # Исправление запроса
            homeworks = Homework.objects.select_related('student')  # Используйте 'student' вместо 'lesson'
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
            # Проверка, что только учителя могут создавать задания
            if not hasattr(request.user, "teacher"):
                return Response({"error": "Only teachers can create homework assignments"},
                                status=status.HTTP_403_FORBIDDEN)

            # Получаем список ID студентов из запроса
            student_ids = request.data.get("students", [])
            if not student_ids:
                return Response({"error": "You must specify at least one student"},
                                status=status.HTTP_400_BAD_REQUEST)

            # Получаем студентов из базы данных
            students = Student.objects.filter(id__in=student_ids)
            if not students.exists():
                return Response({"error": "No valid students found"},
                                status=status.HTTP_400_BAD_REQUEST)

            # Создаём ДЗ для каждого студента
            homeworks = []
            for student in students:
                # Передаем данные в сервис для создания ДЗ
                homework_data = create_homework(
                    student.id,
                    request.data.get("day"),
                    request.data.get("topic"),
                    request.data.get("tasks")
                )
                homeworks.append(homework_data)

            # Возвращаем успешный ответ
            return Response({"message": "Homework created successfully", "homeworks": homeworks},
                            status=status.HTTP_201_CREATED)

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
            student_id = request.data.get("student")
            lesson_id = request.data.get("lesson")
            description = request.data.get("description")

            # Создаем запись об ошибке через сервис
            error_log = create_error_log(
                student_id=student_id,
                lesson_id=lesson_id,
                description=description
            )

            # Устанавливаем is_corrected в False по умолчанию
            error_log.is_corrected = False
            error_log.save()

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
            homeworks = Homework.objects.filter(student=student).select_related('student', 'lesson__teacher')
            error_logs = ErrorLog.objects.filter(student=student)

            # Мапим ошибки по ID домашки
            error_map = {error.lesson.id: error.is_corrected for error in error_logs}

            grouped_data = defaultdict(list)

            for hw in homeworks:
                day = hw.day.strftime("%Y-%m-%d")  # как title
                teacher_name = hw.lesson.teacher.name if hw.lesson and hw.lesson.teacher else "N/A"
                is_corrected = error_map.get(hw.lesson.id, False)

                grouped_data[day].append({
                    "topic": hw.topic,
                    "task": hw.tasks,
                    "teacher_name": teacher_name,
                    "note": hw.note if hasattr(hw, 'note') else "",
                    "isCorrected": is_corrected
                })

            # Преобразуем в нужный формат
            response_data = [{"title": day, "data": items} for day, items in grouped_data.items()]

            return Response(response_data, status=status.HTTP_200_OK)

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
            errors = ErrorLog.objects.filter(student=student)  # Использу объект Student
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
            #является ли пользователь студентом
            if not hasattr(request.user, "student"):
                return Response(
                    {"error": "Only students can view their lessons"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Получаем связанные с этим студентом уроки
            student = request.user.student
            lessons = Lesson.objects.filter(students=student)

            logger.debug(f"Lessons for student {student.id}: {lessons}")

            #  минимальный сериализатор для вывода
            serializer = LessonMinimalSerializer(lessons, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error fetching lessons for student: {e}")
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class ErrorLogUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        try:
            user = request.user

            # Проверяем, является ли пользователь учителем
            if not hasattr(user, 'teacher'):
                return Response({"error": "Only teachers can update error logs"}, status=status.HTTP_403_FORBIDDEN)

            # Получаем ID ошибки из запроса
            error_log_id = request.data.get("error_log_id")
            if not error_log_id:
                return Response({"error": "error_log_id is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Получаем объект ошибки
            try:
                error_log = ErrorLog.objects.get(id=error_log_id)
            except ErrorLog.DoesNotExist:
                return Response({"error": "Error log not found"}, status=status.HTTP_404_NOT_FOUND)

            # Обновляем поле is_corrected
            error_log.is_corrected = request.data.get("is_corrected", error_log.is_corrected)
            error_log.save()

            serializer = ErrorLogSerializer(error_log)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VideoLessonListCreateView(generics.ListCreateAPIView):
    queryset = VideoLesson.objects.all()
    serializer_class = VideoLessonSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Проверяем, что только учитель может создать урок
        if not hasattr(self.request.user, 'teacher'):  # Например, если у пользователя есть поле teacher
            raise PermissionDenied("Only teachers can create video lessons.")
        # Сохраняем видеоурок с привязкой к текущему пользователю
        serializer.save(creator=self.request.user)

class VideoLessonDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = VideoLesson.objects.all()
    serializer_class = VideoLessonSerializer
    authentication_classes = [JWTAuthentication]  # Используем JWT для аутентификации
    permission_classes = [IsAuthenticated]  # Требуется авторизация для всех пользователей

    def update(self, request, *args, **kwargs):
        # Проверяем, что только учитель может редактировать уроки
        if not hasattr(request.user, 'teacher'):
            raise PermissionDenied("Only teachers can update video lessons.")
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # Проверяем, что только учитель может удалять уроки
        if not hasattr(request.user, 'teacher'):
            raise PermissionDenied("Only teachers can delete video lessons.")
        return super().destroy(request, *args, **kwargs)


class StudentListView(generics.ListAPIView):
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'teacher':  # Проверяем, что пользователь — учитель
            return Student.objects.all()
        return Student.objects.none()