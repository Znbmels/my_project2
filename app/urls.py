# app/urls.py

from django.urls import path
from . import views
from .views import ErrorLogUpdateView
from .views import ErrorLogUpdateView
from .views import StudentListView
from app.views import HomeworkCorrectionView
from .views import HomeworkImageUploadView

urlpatterns = [
    path('', views.ApiRootView.as_view(), name='api-root'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('lessons/create/', views.LessonCreateView.as_view(), name='lesson-create'),
    path('lessons/list/', views.LessonListView.as_view(), name='lesson-list'),
    path('homeworks/create/', views.HomeworkCreateView.as_view(), name='homework-create'),
    path('homeworks/list/', views.HomeworkListView.as_view(), name='homework-list'),
    path('errors/create/', views.ErrorLogCreateView.as_view(), name='error-create'),
    path('errors/list/', views.ErrorLogListView.as_view(), name='error-list'),
    path('student/homeworks/', views.StudentHomeworkListView.as_view(), name='student-homeworks'),
    path('homeworks/upload-image/', HomeworkImageUploadView.as_view(), name='homework-upload-image'),
    path("homeworks/<int:homework_id>/correct/", HomeworkCorrectionView.as_view()),
    path('student/errors/', views.StudentErrorListView.as_view(), name='student-errors'),
    path('student/lessons/', views.StudentLessonsAPIView.as_view(), name='student-lessons'),
    path('errors/update/', ErrorLogUpdateView.as_view(), name='update-error-log'),
    path('videos/', views.VideoLessonListCreateView.as_view(), name='video-lesson-list-create'),
    path('videos/<int:pk>/', views.VideoLessonDetailView.as_view(), name='video-lesson-detail'),
    path('student/', views.StudentListView.as_view(), name='student-list'),
]
