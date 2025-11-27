import os
from pathlib import Path
from dotenv import load_dotenv

# ===============================================================
# BASE DO PROJETO
# ===============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega variáveis do .env
load_dotenv(BASE_DIR / '.env')


# ===============================================================
# CONFIGURAÇÕES PRINCIPAIS
# ===============================================================

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'chave_default_para_dev')
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',')


# ===============================================================
# INSTALLED_APPS
# ===============================================================

INSTALLED_APPS = [
    # Django default apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Libs externas
    'widget_tweaks',

    # App principal
    'agendamento',
]


# ===============================================================
# MIDDLEWARE
# ===============================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ===============================================================
# URL PRINCIPAL
# ===============================================================

ROOT_URLCONF = 'sistema_agendamento.urls'


# ===============================================================
# TEMPLATES
# ===============================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],   # Pasta templates global
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


# ===============================================================
# WSGI
# ===============================================================

WSGI_APPLICATION = 'sistema_agendamento.wsgi.application'


# ===============================================================
# BANCO DE DADOS — PostgreSQL
# ===============================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'agendamento_db'),
        'USER': os.environ.get('DB_USER', 'agendamento_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}


# ===============================================================
# VALIDAÇÃO DE SENHAS
# ===============================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ===============================================================
# IDIOMA E TIMEZONE
# ===============================================================

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True
USE_TZ = True


# ===============================================================
# STATIC & MEDIA FILES
# ===============================================================

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ===============================================================
# AUTENTICAÇÃO
# ===============================================================

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'pagina_inicial'
LOGOUT_REDIRECT_URL = 'login'
