import os
from datetime import timedelta
from pathlib import Path

DEBUG = True # Продакшен
file = os.getcwd()
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'your-secret-key-here'

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'tahfiz.halalguide.me',
    '37.27.216.212',
    'django_app',
]

CSRF_TRUSTED_ORIGINS = [
    "https://tahfiz.halalguide.me",
    "http://tahfiz.halalguide.me",
]

SECURE_PROXY_SSL_HEADER = None
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_yasg',
    'app',
    'sslserver',
]


MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Основной URL-конфиг
ROOT_URLCONF = 'my_project2.urls'

# Шаблоны
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI-приложение
WSGI_APPLICATION = 'my_project2.wsgi.application'

# База данных
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3'
    }
}

# Проверка паролей
AUTH_PASSWORD_VALIDATORS = [
    # {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    # {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    # {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    # {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Международизация
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Статические файлы
STATIC_URL = '/static/'
#STATIC_ROOT = BASE_DIR / 'static'
#STATIC_ROOT = '/app/static'
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")


STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'



# MEDIA_URL = '/media/'
# #MEDIA_ROOT = BASE_DIR / 'media'
# MEDIA_ROOT = '/app/media'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'app', 'media')

# Настройки REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

# Настройки JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=35),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=35),
}

AUTH_USER_MODEL = 'app.User'
