# app/urls.py

from django.urls import path
from . import views
from .views import MistakeUpdateView
from .views import StudentListView

urlpatterns = [
    path('', views.ApiRootView.as_view(), name='api-root'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('teacher/lessons/create/', views.LessonCreateView.as_view(), name='lesson-create'),
    path('teacher/lessons/list/', views.TeacherLessonListView.as_view(), name='lesson-list'),
    path('teacher/homeworks/create/', views.HomeworkCreateView.as_view(), name='homework-create'),
    path('teacher/homeworks/list/', views.HomeworkListView.as_view(), name='homework-list'),
    path('teacher/mistakes/create/', views.MistakeCreateView.as_view(), name='mistake-create'),
    path('mistakes/list/', views.MistakeListView.as_view(), name='mistake-list'),
    path('student/homeworks/', views.StudentHomeworkListView.as_view(), name='student-homeworks'),
    path('student/mistakes/', views.StudentMistakeListView.as_view(), name='student-mistakes'),
    path('student/lessons/', views.StudentLessonsAPIView.as_view(), name='student-lessons'),
    path('mistakes/update/', MistakeUpdateView.as_view(), name='update-mistake-log'),
    path('videos/', views.VideoLessonListCreateView.as_view(), name='video-lesson-list-create'),
    path('videos/<int:pk>/', views.VideoLessonDetailView.as_view(), name='video-lesson-detail'),
    path('student/', views.StudentListView.as_view(), name='student-list'),
]
