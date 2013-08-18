# settings for django test suite
import os

options = {'use_mars': True,
           'allow_nulls_in_unique_constraints': False,  # sqlserver doesn't fully support multiple nulls in unique constraint
           }

DATABASES = {
    'default': {
        'ENGINE': os.environ['BACKEND'],
        'HOST': os.environ['HOST'],
        'NAME': os.environ['DATABASE_NAME'] + '_default',
        'USER': os.environ['SQLUSER'],
        'PASSWORD': os.environ['SQLPASSWORD'],
        'OPTIONS': options,
        },
    'other': {
        'ENGINE': os.environ['BACKEND'],
        'HOST': os.environ['HOST'],
        'NAME': os.environ['DATABASE_NAME'] + '_other',
        'USER': os.environ['SQLUSER'],
        'PASSWORD': os.environ['SQLPASSWORD'],
        'OPTIONS': options,
        }
    }

SECRET_KEY = "django_tests_secret_key"

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.UnsaltedMD5PasswordHasher',
    )
