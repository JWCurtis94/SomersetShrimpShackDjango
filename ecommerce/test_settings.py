"""
Test settings for running payment process tests
"""
from .settings import *

# Use SQLite for testing to avoid migration issues
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable migrations for faster testing
class DisableMigrations:
    def __contains__(self, item):
        return True
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Test specific settings
DEBUG = True
SECRET_KEY = 'test-secret-key-for-testing-only'
ALLOWED_HOSTS = ['*', 'testserver']

# Disable security features for testing
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False

# Use simple static files storage for testing
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Disable static files collection in testing
STATIC_ROOT = None
CSRF_COOKIE_SECURE = False

# Use local storage for tests
USE_S3 = False
MEDIA_ROOT = '/tmp/test_media'

# Use console email backend for testing
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Stripe test settings
STRIPE_WEBHOOK_SECRET = 'whsec_test_webhook_secret_for_testing'
STRIPE_PUBLISHABLE_KEY = 'pk_test_fake_publishable_key_for_testing'
STRIPE_SECRET_KEY = 'sk_test_fake_secret_key_for_testing'
