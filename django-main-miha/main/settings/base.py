from pathlib import Path
import os
import sys

# from corsheaders.defaults import default_headers Miha

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(os.path.join(BASE_DIR, 'thirdparty'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

ALLOWED_HOSTS = ["*"]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core.apps.CoreConfig',
    'diplom.apps.DiplomConfig'
]

MIDDLEWARE = [
    'thirdparty.threadlocals.middleware.ThreadLocalMiddleware',
    # 'corsheaders.middleware.CorsMiddleware', #Miha
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware', # Miha 
    # отключаем CSRF проверку
    # 'utils.auth.DisableCSRFMiddleware', #Miha
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # RemoteUserMiddleware с обновленным заголовком и логированием
    # 'utils.auth.CustomRemoteUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

AUTHENTICATION_BACKENDS = [
    # Для автоматической аутентификации тех, кто приходит с определенным заголовком
    # RemoteUserBackend с возможностью управления автоматическим созданием пользователя
    'utils.auth.CustomRemoteUserBackend',
    'django.contrib.auth.backends.ModelBackend',
]

ROOT_URLCONF = 'main.urls'
STATICFILES_DIRS = (os.path.join(BASE_DIR,'static'),)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR.joinpath('templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.user_group',
            ],
        },
    },
]

# Опционально настройки кэширования
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'app-unique-cache',
        'TIMEOUT': 300,  # 300 sec
    }
}
# настройки поведения данных сессий
SESSION_ENGINE = 'django.contrib.sessions.backends.file'
# cache - данные сессии хранятся в памяти, при перезапуске приложения теряются
# cached_db - данные сессии записываются в БД, читаются из памяти.
# если не найдены в памяти - читаются из БД
# file  - складывается в файлы в SESSION_FILE_PATH


DATABASE_ROUTERS = ['main.routers.DbRouter']

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Asia/Yekaterinburg'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files inside development.py and production.py (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_FILES_DIRS = (os.path.join(BASE_DIR, 'static'),)
STATIC_ROOT = os.path.join(BASE_DIR, 'static', 'front', 'react-front', 'build')


# corsheaders
# для django-template приложения
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_WHITELIST = (
    '0.0.0.0'
)
# CORS_ALLOW_HEADERS = default_headers + ('Content-Disposition',)
CORS_EXPOSE_HEADERS = ['*']

# RemoteUserMiddleware по-умолчанию создает новых пользователей
# это лучше отключить кастомной настройкой, так как у пользователя django_auth_user
# и у обычного пользователя прав на insert таблицы auth_user нет.
CREATE_UNKNOWN_USER = False

# не обновлять каждый раз при обработке запроса последнюю активность пользователя
NO_UPDATE_LAST_LOGIN = True

# для контроля версий развернутого приложения
APP_VERSION = 1

# LOGIN_URL = 'autuser:login'
# LOGIN_REDIRECT_URL = 'users:get_all'