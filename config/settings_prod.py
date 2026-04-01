from .settings import *
import os

DEBUG = False

ALLOWED_HOSTS = [
    'changky.com',
    'www.changky.com',
    'api.changky.com',
    '134.209.98.222',
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
    'https://changky.com',
    'https://www.changky.com',
    'https://api.changky.com',
    'http://localhost:3010',
    'http://localhost:3000',
    'http://127.0.0.1:3010',
    'http://127.0.0.1:3000',
]

CORS_ALLOW_ALL_ORIGINS = False

STATIC_URL = '/static/'
STATIC_ROOT = '/home/odette/odette-be/staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/odette/odette-be/media'