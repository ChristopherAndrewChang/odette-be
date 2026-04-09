from .settings import *
import os

DEBUG = False

ALLOWED_HOSTS = [
    'odette.vip',
    'www.odette.vip',
    'api.odette.vip',
    'admin.odette.vip',
    '159.89.192.224',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

CORS_ALLOWED_ORIGINS = [
    'https://odette.vip',
    'https://www.odette.vip',
    'https://api.odette.vip',
    'https://admin.odette.vip',
    'http://localhost:3010',
    'http://localhost:3000',
    'http://127.0.0.1:3010',
    'http://127.0.0.1:3000',
]

CORS_ALLOW_ALL_ORIGINS = False

CSRF_TRUSTED_ORIGINS = [
    'https://odette.vip',
    'https://www.odette.vip',
    'https://api.odette.vip',
    'https://admin.odette.vip',
    'http://localhost:3010',
    'http://localhost:3000',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'accept-language',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-session-token',
    'ngrok-skip-browser-warning',
    'sec-ch-ua',
    'sec-ch-ua-mobile',
    'sec-ch-ua-platform',
    'referer',
]

FRONTEND_URL = 'https://odette.vip'

TIME_ZONE = 'Asia/Jakarta'
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = '/home/odette/odette-be/staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/odette/odette-be/media'

DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800