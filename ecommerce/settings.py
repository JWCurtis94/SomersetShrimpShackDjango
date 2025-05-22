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

# Database configuration for local development and Heroku deployment
# Load environment variables from .env file
load_dotenv()

# Get DATABASE_URL from environment (Heroku will set this automatically)
db_url = os.environ.get('DATABASE_URL')

# Check for alternative Heroku PostgreSQL URLs (backup)
heroku_pg_url = None
for key, value in os.environ.items():
    if 'HEROKU_POSTGRESQL_' in key and '_URL' in key:
        heroku_pg_url = value
        break

# Configure database based on available URLs
if db_url and ('postgres' in db_url or 'postgresql' in db_url):
    # Use primary DATABASE_URL (from Heroku or local .env)
    DATABASES = {
        'default': dj_database_url.parse(db_url, conn_max_age=600)
    }
    print("✅ Using PostgreSQL database")
    
elif heroku_pg_url and ('postgres' in heroku_pg_url or 'postgresql' in heroku_pg_url):
    # Fallback to alternative Heroku PostgreSQL URL
    DATABASES = {
        'default': dj_database_url.parse(heroku_pg_url, conn_max_age=600)
    }
    print("✅ Using alternative Heroku PostgreSQL database")
    
else:
    # Final fallback to SQLite for local development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    print("⚠️ Using SQLite database (local development)")

# Add SSL configuration for production (Heroku requires SSL)
if 'postgresql' in DATABASES['default'].get('ENGINE', ''):
    # Check if we're on Heroku by looking for Heroku-specific indicators
    is_heroku = any([
        'DATABASE_URL' in os.environ and 'heroku' in os.environ.get('DATABASE_URL', ''),
        'DYNO' in os.environ,  # Heroku sets this environment variable
        'heroku' in os.environ.get('DATABASE_URL', '').lower()
    ])
    
    if is_heroku:
        DATABASES['default']['OPTIONS'] = {
            'sslmode': 'require',
        }
        print("🔒 SSL enabled for Heroku PostgreSQL")
    else:
        DATABASES['default']['OPTIONS'] = {
            'sslmode': 'disable',
        }
        print("🔓 SSL disabled for local PostgreSQL")

# Debug output
db_engine = DATABASES['default'].get('ENGINE', 'Unknown')
db_name = DATABASES['default'].get('NAME', 'Unknown')
db_host = DATABASES['default'].get('HOST', 'localhost')
print(f"Final database config:")
print(f"  Engine: {db_engine}")
print(f"  Name: {db_name}")
print(f"  Host: {db_host}")

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
# Improved WhiteNoise configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

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

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

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
# Change your LOGGING configuration to be less verbose
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',  # Change from DEBUG to INFO
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',  # Change from DEBUG to WARNING
        },
        'django.utils.autoreload': {
            'handlers': ['console'],
            'level': 'WARNING',  # Specifically quiet the autoreload debug messages
        }
    }
}

if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1']