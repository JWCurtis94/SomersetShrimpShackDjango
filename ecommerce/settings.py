import os
from pathlib import Path
from django.contrib.messages import constants as messages
from dotenv import load_dotenv
import dj_database_url

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'default-secret-key-for-dev')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True  # Set to True for debugging

# Allow all App Engine URLs and local development
ALLOWED_HOSTS = ['*']  # Allow all hosts temporarily for debugging

# Application definition
INSTALLED_APPS = [
    'admin_interface',  # Must be before django.contrib.admin
    'colorfield',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'store',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'ecommerce',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'ecommerce.urls'

WSGI_APPLICATION = 'ecommerce.wsgi.application'

# Database configuration - ultra direct approach
# Get all environment variables for debugging
print("All environment variables:")
for key, value in os.environ.items():
    if 'DATABASE' in key or 'HEROKU_POSTGRESQL' in key:
        print(f"{key}: {value[:15]}..." if value else f"{key}: {value}")

# Get the DATABASE_URL from Heroku
db_url = os.environ.get('DATABASE_URL')
print(f"Raw DATABASE_URL: {db_url[:30]}..." if db_url else "Raw DATABASE_URL: None")

# Get any other potential database URLs
heroku_pg_url = None
for key, value in os.environ.items():
    if 'HEROKU_POSTGRESQL_' in key and '_URL' in key:
        heroku_pg_url = value
        print(f"Found alternative PG URL: {key} = {value[:30]}...")

# Try to use the DATABASE_URL first
if db_url and 'postgres:' in db_url:
    print(f"Using primary DATABASE_URL")
    DATABASES = {
        'default': dj_database_url.parse(db_url)
    }
# If not available, try to use a HEROKU_POSTGRESQL_*_URL if found
elif heroku_pg_url and 'postgres:' in heroku_pg_url:
    print(f"Using alternative HEROKU_POSTGRESQL URL")
    DATABASES = {
        'default': dj_database_url.parse(heroku_pg_url)
    }
# Fallback to SQLite for local development
else:
    print("Using SQLite database (fallback)")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }

print(f"Final database config: ENGINE={DATABASES['default'].get('ENGINE')}, HOST={DATABASES['default'].get('HOST', 'localhost')}")

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'store', 'templates'),
            os.path.join(BASE_DIR, 'templates'),
        ],
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

# Simplified static files storage for debugging
STATICFILES_STORAGE = 'whitenoise.storage.StaticFilesStorage'

# Security Settings (relaxed for debugging)
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Authentication Settings
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

# Allauth settings
ACCOUNT_LOGIN_METHODS = {"username"}
ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_USERNAME_REQUIRED = True
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_SIGNUP_REDIRECT_URL = "/"

# Static and Media Files
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'store', 'static'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Stripe Settings
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY', '')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')

# Messages configuration
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

# Add detailed logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        }
    }
}