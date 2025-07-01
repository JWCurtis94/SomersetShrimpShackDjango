#!/usr/bin/env python
"""
Debug script for production 400 errors
Run this to check your Django configuration for common 400 error causes
"""

import os
import sys
from pathlib import Path

# Add the project directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

import django
django.setup()

from django.conf import settings
from django.core.management import execute_from_command_line

def check_400_issues():
    print("=== PRODUCTION 400 ERROR DIAGNOSTIC ===\n")
    
    print("1. DEBUG Setting:")
    print(f"   DEBUG = {settings.DEBUG}")
    print(f"   Expected for production: False ✓" if not settings.DEBUG else "   WARNING: DEBUG should be False in production!")
    
    print(f"\n2. ALLOWED_HOSTS:")
    print(f"   Current hosts: {settings.ALLOWED_HOSTS}")
    
    expected_hosts = ['somersetshrimpshack.uk', 'www.somersetshrimpshack.uk']
    missing_hosts = [host for host in expected_hosts if host not in settings.ALLOWED_HOSTS]
    
    if not missing_hosts:
        print("   ✓ Production domains are included")
    else:
        print(f"   ❌ Missing hosts: {missing_hosts}")
    
    print(f"\n3. CSRF Configuration:")
    print(f"   CSRF_COOKIE_SECURE = {settings.CSRF_COOKIE_SECURE}")
    
    if hasattr(settings, 'CSRF_TRUSTED_ORIGINS'):
        print(f"   CSRF_TRUSTED_ORIGINS = {settings.CSRF_TRUSTED_ORIGINS}")
        if 'https://somersetshrimpshack.uk' in settings.CSRF_TRUSTED_ORIGINS:
            print("   ✓ Production domain is in CSRF trusted origins")
        else:
            print("   ❌ Production domain missing from CSRF trusted origins")
    else:
        print("   ❌ CSRF_TRUSTED_ORIGINS not set")
    
    print(f"\n4. Security Settings:")
    print(f"   SECURE_SSL_REDIRECT = {settings.SECURE_SSL_REDIRECT}")
    print(f"   SESSION_COOKIE_SECURE = {settings.SESSION_COOKIE_SECURE}")
    
    print(f"\n5. Database Configuration:")
    db_engine = settings.DATABASES['default']['ENGINE']
    print(f"   Database Engine: {db_engine}")
    
    if 'postgresql' in db_engine:
        print("   ✓ Using PostgreSQL for production")
    elif 'sqlite' in db_engine:
        print("   ⚠️  Using SQLite - consider PostgreSQL for production")
    
    print(f"\n6. Static Files:")
    print(f"   STATIC_ROOT = {settings.STATIC_ROOT}")
    print(f"   STATIC_URL = {settings.STATIC_URL}")
    
    print(f"\n=== COMMON 400 ERROR CAUSES ===")
    print("1. Domain not in ALLOWED_HOSTS")
    print("2. Missing CSRF_TRUSTED_ORIGINS for POST requests")
    print("3. SSL/HTTPS configuration issues")
    print("4. Incorrect HOST header from reverse proxy")
    print("5. Malformed HTTP requests")
    
    print(f"\n=== RECOMMENDATIONS ===")
    print("1. Deploy the updated settings.py with the new ALLOWED_HOSTS")
    print("2. Restart your production server after deployment")
    print("3. Check your web server/proxy configuration (Nginx, Apache, etc.)")
    print("4. Verify SSL certificate is properly configured")
    print("5. Test with curl: curl -H 'Host: somersetshrimpshack.uk' https://your-server-ip/")

if __name__ == '__main__':
    check_400_issues()
