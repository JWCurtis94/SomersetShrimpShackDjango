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
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-key-change-in-production-use-env-vars')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Allow all App Engine URLs and local development
if DEBUG:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '[::1]']  # Restrict to known development hosts
else:
    # In production, restrict to specific hosts
    ALLOWED_HOSTS = [
        'localhost',
        '127.0.0.1',
        '.herokuapp.com',  # Heroku apps
        '.railway.app',    # Railway apps
        'somersetshrimpshack.uk',  # Your production domain
        'www.somersetshrimpshack.uk',  # Include www subdomain
    ]

# Application definition
INSTALLED_APPS = [
    'admin_interface',
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
    'storages',  # For AWS S3 storage
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

# Database configuration - Environment dependent
db_url = os.environ.get('DATABASE_URL')

# Try to use the DATABASE_URL first (supports postgresql:// and postgres://)
if db_url and ('postgres' in db_url or 'postgresql' in db_url):
    DATABASES = {
        'default': dj_database_url.parse(db_url)
    }
# Check for individual PostgreSQL settings
elif os.environ.get('DB_ENGINE') == 'django.db.backends.postgresql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'somerset_shrimp_db'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
            'OPTIONS': {
                'connect_timeout': 10,
            }
        }
    }
# Check for alternative Heroku PostgreSQL URLs
else:
    heroku_pg_url = None
    for key, value in os.environ.items():
        if 'HEROKU_POSTGRESQL_' in key and '_URL' in key:
            heroku_pg_url = value
            break
    
    if heroku_pg_url and 'postgres' in heroku_pg_url:
        DATABASES = {
            'default': dj_database_url.parse(heroku_pg_url)
        }
    # Fallback to SQLite for local development
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
            }
        }

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
                'store.context_processors.categories_context',
            ],
        },
    },
]

# Simplified static files storage for debugging
# Improved WhiteNoise configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Security Settings - Environment dependent
SECURE_SSL_REDIRECT = not DEBUG  # Only redirect to HTTPS in production
SESSION_COOKIE_SECURE = not DEBUG  # Only secure cookies in production
CSRF_COOKIE_SECURE = not DEBUG  # Only secure CSRF cookies in production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Additional security headers for production
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Session Configuration
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# CSRF Configuration
CSRF_COOKIE_AGE = 31449600  # 1 year
CSRF_USE_SESSIONS = False  # Use cookies instead of sessions for better performance

# CSRF Trusted Origins for production domain
if not DEBUG:
    CSRF_TRUSTED_ORIGINS = [
        'https://somersetshrimpshack.uk',
        'https://www.somersetshrimpshack.uk',
    ]

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
LOGIN_URL = '/login/'
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

# AWS S3 Configuration for Media Files
USE_S3 = os.environ.get('USE_S3', 'False').lower() == 'true'

if USE_S3:
    # AWS S3 Settings
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    
    # S3 Media files configuration
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
    
    # Optional: Use CloudFront if you have it set up
    # AWS_S3_CUSTOM_DOMAIN = 'your-cloudfront-domain.cloudfront.net'
    # MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
    
    # S3 Settings
    AWS_DEFAULT_ACL = None  # Use bucket's default policy instead of ACLs
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_S3_FILE_OVERWRITE = False
    AWS_LOCATION = 'media'
    
    # Additional S3 settings for newer AWS security requirements
    AWS_QUERYSTRING_AUTH = False  # Don't add authentication parameters to URLs
    AWS_S3_SIGNATURE_VERSION = 's3v4'  # Use the latest signature version
else:
    # Local media files (for development)
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

# Email Configuration
if DEBUG and not os.getenv("FORCE_EMAIL", "False").lower() == "true":
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)


# Default from email
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Somerset Shrimp Shack <noreply@somersetshrimp.com>')

# Admin email for order notifications
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@somersetshrimp.com')

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple' if DEBUG else 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'django.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'] + (['file'] if not DEBUG else []),
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',  # Reduce database query noise
            'propagate': False,
        },
        'django.utils.autoreload': {
            'handlers': ['console'],
            'level': 'WARNING',  # Quiet the autoreload debug messages
            'propagate': False,
        },
        'store': {  # Your app's logger
            'handlers': ['console'] + (['file'] if not DEBUG else []),
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1']