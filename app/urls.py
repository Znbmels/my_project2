# app/urls.py

from django.urls import path
from . import views

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
    path('student/errors/', views.StudentErrorListView.as_view(), name='student-errors'),
    path('student/lessons/', views.StudentLessonsAPIView.as_view(), name='student-lessons'),
]
