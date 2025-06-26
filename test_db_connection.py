#!/usr/bin/env python
"""
Database Connection Test Script for Somerset Shrimp Shack
Run this script to test your PostgreSQL connection before running migrations.
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.db import connection
from django.core.management import execute_from_command_line
from django.conf import settings

def test_database_connection():
    """Test the database connection and display configuration info."""
    
    print("=" * 60)
    print("SOMERSET SHRIMP SHACK - DATABASE CONNECTION TEST")
    print("=" * 60)
    
    # Display current database configuration
    db_config = settings.DATABASES['default']
    print(f"\nDatabase Configuration:")
    print(f"  Engine: {db_config['ENGINE']}")
    
    if 'postgresql' in db_config['ENGINE']:
        print(f"  Database: {db_config.get('NAME', 'Not specified')}")
        print(f"  Host: {db_config.get('HOST', 'localhost')}")
        print(f"  Port: {db_config.get('PORT', '5432')}")
        print(f"  User: {db_config.get('USER', 'Not specified')}")
    else:
        print(f"  Database File: {db_config.get('NAME', 'Not specified')}")
    
    print(f"\nTesting connection...")
    
    try:
        # Test the connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
        if result[0] == 1:
            print("✅ SUCCESS: Database connection established!")
            
            # Get database info
            with connection.cursor() as cursor:
                if 'postgresql' in db_config['ENGINE']:
                    cursor.execute("SELECT version()")
                    version = cursor.fetchone()[0]
                    print(f"   PostgreSQL Version: {version}")
                    
                    cursor.execute("SELECT current_database()")
                    db_name = cursor.fetchone()[0]
                    print(f"   Connected to database: {db_name}")
                    
                    cursor.execute("SELECT current_user")
                    user = cursor.fetchone()[0]
                    print(f"   Connected as user: {user}")
                
                # Check if tables exist
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                table_count = cursor.fetchone()[0]
                print(f"   Number of tables: {table_count}")
                
                if table_count == 0:
                    print("   ⚠️  No tables found. You may need to run migrations.")
                else:
                    print("   ✅ Database tables exist.")
            
            return True
            
    except Exception as e:
        print(f"❌ ERROR: Database connection failed!")
        print(f"   Error details: {str(e)}")
        print(f"\n💡 Troubleshooting tips:")
        
        if 'postgresql' in db_config['ENGINE']:
            print("   1. Ensure PostgreSQL server is running")
            print("   2. Check database name, username, and password in .env file")
            print("   3. Verify the database exists: CREATE DATABASE somerset_shrimp_db;")
            print("   4. Check user permissions: GRANT ALL PRIVILEGES ON DATABASE somerset_shrimp_db TO username;")
        else:
            print("   1. Check if SQLite database file exists and is readable")
            print("   2. Ensure proper file permissions")
        
        return False

def run_django_checks():
    """Run Django system checks."""
    print(f"\n" + "=" * 60)
    print("RUNNING DJANGO SYSTEM CHECKS")
    print("=" * 60)
    
    try:
        execute_from_command_line(['manage.py', 'check', '--database', 'default'])
        print("✅ Django system checks passed!")
        return True
    except Exception as e:
        print(f"❌ Django system checks failed: {str(e)}")
        return False

def main():
    """Main function to run all tests."""
    
    # Test database connection
    db_success = test_database_connection()
    
    if db_success:
        # Run Django checks
        check_success = run_django_checks()
        
        if check_success:
            print(f"\n" + "=" * 60)
            print("🎉 ALL TESTS PASSED!")
            print("=" * 60)
            print("Your database is ready. Next steps:")
            print("1. Run migrations: python manage.py migrate")
            print("2. Create superuser: python manage.py createsuperuser")
            print("3. Start development server: python manage.py runserver")
        else:
            print(f"\n❌ Some system checks failed. Please review the errors above.")
    else:
        print(f"\n❌ Database connection failed. Please check your configuration.")
        
        # Show environment variables for debugging
        print(f"\nEnvironment variables (for debugging):")
        database_url = os.environ.get('DATABASE_URL', 'Not set')
        if 'password' in database_url.lower():
            # Hide password for security
            database_url = database_url.split('@')[0].split(':')[:-1]
            database_url = ':'.join(database_url) + ':***@' + database_url.split('@')[1] if '@' in os.environ.get('DATABASE_URL', '') else database_url
        
        print(f"  DATABASE_URL: {database_url}")
        print(f"  DB_ENGINE: {os.environ.get('DB_ENGINE', 'Not set')}")
        print(f"  DB_NAME: {os.environ.get('DB_NAME', 'Not set')}")
        print(f"  DB_USER: {os.environ.get('DB_USER', 'Not set')}")
        print(f"  DB_HOST: {os.environ.get('DB_HOST', 'Not set')}")
        print(f"  DB_PORT: {os.environ.get('DB_PORT', 'Not set')}")

if __name__ == "__main__":
    main()
