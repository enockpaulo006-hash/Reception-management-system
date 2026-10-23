
import os
from pathlib import Path


# =========================================================
# 1. PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# =========================================================
# 2. SECURITY AND DEBUG SETTINGS
# =========================================================

SECRET_KEY = 'django-insecure-wj&-dt7=_d!7g=tud9j-@0x+lml)_49rxvjmawu=ry8wo+s*v#'

DEBUG = True

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
]


# =========================================================
# 3. INSTALLED APPLICATIONS
# =========================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'reception',
]


# =========================================================
# 4. MIDDLEWARE
# =========================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'reception.middleware.FirstRunSetupMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]


# =========================================================
# 5. URLS AND TEMPLATES
# =========================================================

ROOT_URLCONF = 'clinic.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'reception.context_processors.clinic_name',
            ],
        },
    },
]

WSGI_APPLICATION = 'clinic.wsgi.application'


# =========================================================
# 6. DATABASE CONFIGURATION
# =========================================================

if os.environ.get('CLINIC_PRODUCTION') == '1':
    DATA_DIR = r'C:\ProgramData\ClinicReception\data'
    LOG_DIR = r'C:\ProgramData\ClinicReception\logs'

    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    DB_PATH = os.path.join(DATA_DIR, 'db.sqlite3')
else:
    DB_PATH = BASE_DIR / 'db.sqlite3'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DB_PATH,
    }
}


# =========================================================
# 7. PASSWORD VALIDATION
# =========================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'UserAttributeSimilarityValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'MinimumLengthValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'CommonPasswordValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'NumericPasswordValidator'
        ),
    },
]


# =========================================================
# 8. LANGUAGE AND TIME ZONE
# =========================================================

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Dar_es_Salaam'

USE_I18N = True
USE_TZ = True


# =========================================================
# 9. STATIC FILES
# =========================================================

STATIC_URL = '/static/'

# Source folder containing app.css and the dispensary logo.
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Destination used by collectstatic in production.
STATIC_ROOT = BASE_DIR / 'staticfiles'


# =========================================================
# 10. WHITE NOISE STATIC FILE STORAGE
# =========================================================

# Keep the existing WhiteNoise middleware.
# Use compressed static files with manifest-based names.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': (
            'whitenoise.storage.CompressedManifestStaticFilesStorage'
        ),
    },
}


# =========================================================
# 11. EMAIL CONFIGURATION
# =========================================================

MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}


# =========================================================
# 12. PRODUCTION ERROR LOGGING
# =========================================================

if os.environ.get('CLINIC_PRODUCTION') == '1':
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'clinic_file': {
                'class': 'logging.FileHandler',
                'filename': os.path.join(LOG_DIR, 'errors.log'),
                'level': 'ERROR',
            },
        },
        'loggers': {
            'django.request': {
                'handlers': ['clinic_file'],
                'level': 'ERROR',
                'propagate': False,
            },
        },
    }


# =========================================================
# 13. LOGIN AND LOGOUT
# =========================================================

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'


# =========================================================
# 14. SESSION SETTINGS
# =========================================================

SESSION_COOKIE_AGE = 600
SESSION_SAVE_EVERY_REQUEST = True


# =========================================================
# 15. APPLICATION OPTIONS
# =========================================================

SHOW_AUDIT_LOG = False
