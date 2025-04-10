import logging
from collections import defaultdict
from datetime import datetime, date
from django.views import View
from django.http import JsonResponse
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from app.models import User, Homework, Mistake, Lesson, Student, VideoLesson
from app.services.utils import get_teacher_by_user
from app.serializers import (
    UserSerializer,
    LessonSerializer,
    HomeworkSerializer,
    # MistakeSerializer,
    LessonMinimalSerializer,
    VideoLessonSerializer,
    StudentSerializer,
    HomeworkImageUploadSerializer,
    MistakeImageSerializer,
)
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from app.services.lesson_service import create_lesson, get_lessons_by_teacher
from app.services.homework_service import create_homework, get_homeworks_for_student
from app.services.error_service import create_mistake, get_mistakes_for_student
from app.services.teacher_service import get_teacher_by_user
from app.services.student_service import get_student_by_user
from django.shortcuts import get_object_or_404
from .models import HomeworkImage
import traceback


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
                'mistakes': '/mistakes/',
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
        return Response(serializer.mistakes, status=status.HTTP_400_BAD_REQUEST)


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
        if not hasattr(request.user, "teacher"):
            return Response({"error": "Only teachers can correct homework."}, status=status.HTTP_403_FORBIDDEN)

        try:
            # Исправление запроса
            homeworks = Homework.objects.select_related('student')  # Используйте 'student' вместо 'lesson'
            serializer = HomeworkSerializer(homeworks, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error fetching homeworks: {e}")
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request):
        # Только учитель может редактировать
        if not hasattr(request.user, "teacher"):
            return Response({"error": "Only teachers can correct homework."}, status=status.HTTP_403_FORBIDDEN)

        homework_id = request.data.get("homework_id")
        if not homework_id:
            return Response({"error": "homework_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        is_corrected = request.data.get("is_corrected")
        if is_corrected is None:
            return Response({"error": "Missing 'is_corrected' field"}, status=status.HTTP_400_BAD_REQUEST)
        homework = get_object_or_404(Homework, id=homework_id)
        homework.is_corrected = is_corrected
        homework.save()

        return Response({"message": "Homework corrected status updated."}, status=status.HTTP_200_OK)

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
            teacher = request.user.teacher
            homeworks = []
            for student in students:
                # Передаем данные в сервис для создания ДЗ
                homework_data = create_homework(
                    student.id,
                    teacher,
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


# View to retrieve all mistake logs
class MistakeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            mistakes = Mistake.objects.select_related("student", "lesson").all()  # Fetch related data
            serializer = MistakeSerializer(mistakes, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching error logs: {e}")
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# View to create a new mistake log (teachers only)
class MistakeCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            student_id = request.data.get("student")
            lesson_id = request.data.get("lesson")
            description = request.data.get("description")

            # Создаем запись об ошибке через сервис
            mistake_log = create_mistake_log(
                student_id=student_id,
                lesson_id=lesson_id,
                description=description
            )

            # Устанавливаем is_corrected в False по умолчанию
            mistake_log.is_corrected = False
            mistake_log.save()

            # Сериализуем данные
            serializer = MistakeSerializer(mistake_log)
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
class TeacherLessonListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            if not hasattr(request.user, "teacher"):
                return Response({"error": "Only teachers can view their lessons"},
                                status=status.HTTP_403_FORBIDDEN)

            teacher = get_teacher_by_user(request.user)  # Fetch teacher object
            lessons = get_lessons_by_teacher(teacher)  # Fetch lessons for teacher
            # Фильтрация уроков по дате
            date_str = request.query_params.get('date')
            if date_str:
                try:
                    filter_date = date.fromisoformat(date_str)
                    lessons = lessons.filter(day=filter_date)
                except ValueError:
                    return Response({"error": "Invalid date format. Use YYYY-MM-DD."},
                                    status=status.HTTP_400_BAD_REQUEST)
            else:
                today = date.today()
                lessons = lessons.filter(day__gte=today)


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
            today = date.today()
            homeworks = Homework.objects.filter(student=student,
                                                day__gte=today
                                                ).select_related('teacher')

            grouped_data = defaultdict(list)
            for hw in homeworks:
                day = hw.day.strftime("%Y-%m-%d")
                teacher_name = hw.teacher.name if hw.teacher else "N/A"
                is_corrected = hw.is_corrected
                is_done = hw.is_done

                tasks = hw.tasks
                if isinstance(tasks, dict):
                    task_items = tasks.values()
                elif isinstance(tasks, list):
                    task_items = tasks
                else:
                    task_items = [tasks]

                for task in task_items:
                    grouped_data[day].append({
                        "id": hw.id,
                        "topic": hw.topic,
                        "task": task,
                        "teacher_name": teacher_name,
                        "note": hw.note or "",
                        "isCorrected": is_corrected,
                        "is_Done" : is_done
                    })

            response_data = [{"title": day, "data": items} for day,
            items in grouped_data.items()]
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error fetching student homework: {e}")
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request):
        try:
            if not hasattr(request.user, "student"):
                return Response({"error": "Only students can update homework status"},
                                status=status.HTTP_403_FORBIDDEN)

            homework_id = request.data.get("homework_id")
            is_done = request.data.get("is_done")

            if homework_id is None or is_done is None:
                return Response({"error": "Missing homework_id or is_done"}, status=status.HTTP_400_BAD_REQUEST)

            # Проверка, что задание принадлежит текущему студенту
            homework = Homework.objects.get(id=homework_id, student=request.user.student)
            homework.is_done = is_done
            homework.save()

            return Response({"message": "Homework status updated"}, status=status.HTTP_200_OK)

        except Homework.DoesNotExist:
            return Response({"error": "Homework not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error updating homework status: {e}")
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        serializer = HomeworkImageUploadSerializer(data=request.data)
        if serializer.is_valid():
            images = serializer.save()
            response_data = [
                {
                    "id": img.id,
                    "homework": img.homework_id,
                    "image": request.build_absolute_uri(img.image.url),
                    "uploaded_at": img.uploaded_at,
                }
                for img in images
            ]
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# View to list mistake logs for a student
class StudentMistakeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            if not hasattr(request.user, "student"):
                return Response({"error": "Only students can view their error logs"},
                                status=status.HTTP_403_FORBIDDEN)

            student = request.user.student  # Fetch student object
            mistakes = Mistake.objects.filter(student=student)  # Использу объект Student
            serializer = MistakeSerializer(mistakes, many=True)
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

            student = request.user.student
            lessons = Lesson.objects.filter(students=student)
            # Фильтрация по дате, если указана
            date_str = request.query_params.get('date')
            if date_str:
                try:
                    filter_date = date.fromisoformat(date_str)
                    lessons = lessons.filter(day=filter_date)
                except ValueError:
                    return Response({"error": "Invalid date format. Use YYYY-MM-DD."},
                                    status=status.HTTP_400_BAD_REQUEST)
            else:
                today = date.today()
                lessons = lessons.filter(day__gte=today)

            #  минимальный сериализатор для вывода
            serializer = LessonMinimalSerializer(lessons, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error fetching lessons for student: {e}")
            logger.error(traceback.format_exc())
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class MistakeUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        try:
            user = request.user

            # Проверяем, является ли пользователь учителем
            if not hasattr(user, 'teacher'):
                return Response({"error": "Only teachers can update error logs"}, status=status.HTTP_403_FORBIDDEN)

            # Получаем ID ошибки из запроса
            mistake_log_id = request.data.get("mistake_log_id")
            if not mistake_log_id:
                return Response({"error": "mistake_log_id is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Получаем объект ошибки
            try:
                mistake_log = Mistake.objects.get(id=mistake_log_id)
            except Mistake.DoesNotExist:
                return Response({"error": "mistake log not found"}, status=status.HTTP_404_NOT_FOUND)

            # Обновляем поле is_corrected
            mistake_log.is_corrected = request.data.get("is_corrected", mistake_log.is_corrected)
            mistake_log.save()

            serializer = MistakeSerializer(mistake_log)
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
