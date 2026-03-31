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
]

CORS_ALLOW_ALL_ORIGINS = False

STATIC_URL = '/static/'
STATIC_ROOT = '/home/odette/odette-backend/staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/odette/odette-backend/media'