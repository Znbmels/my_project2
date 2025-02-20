from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from app.models import User, Teacher, Student, Lesson, Homework, ErrorLog


# Регистрация модели User
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email')

    # Настройка полей формы для создания пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'is_active', 'is_staff'),
        }),
    )

    # Настройка полей формы для редактирования пользователя
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('email', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )


# Регистрация остальных моделей
@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name', 'user')
    search_fields = ('name', 'user__username')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'user')
    search_fields = ('name', 'user__username')


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('day_of_week', 'start_time', 'end_time', 'teacher', 'zoom_link')
    list_filter = ('day_of_week', 'teacher')
    search_fields = ('teacher__name', 'zoom_link')


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'day', 'topic')
    list_filter = ('lesson', 'day')
    search_fields = ('topic',)


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ('student', 'lesson', 'description')
    list_filter = ('student', 'lesson')
    search_fields = ('description',)