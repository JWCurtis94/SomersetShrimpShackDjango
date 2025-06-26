# PostgreSQL Database Setup Guide

## Overview
This guide will help you set up PostgreSQL for the Somerset Shrimp Shack Django project.

## Prerequisites
- Python virtual environment activated
- PostgreSQL server installed on your system

## Step 1: Install PostgreSQL

### Windows
1. Download PostgreSQL from https://www.postgresql.org/download/windows/
2. Run the installer and follow the setup wizard
3. Remember the password you set for the 'postgres' user
4. Default port is 5432 (keep this unless you have conflicts)

### macOS
```bash
# Using Homebrew
brew install postgresql
brew services start postgresql

# Or download from postgresql.org
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

## Step 2: Create Database and User

### Method 1: Using PostgreSQL Command Line
```bash
# Connect to PostgreSQL as superuser
psql -U postgres

# In the PostgreSQL prompt:
CREATE DATABASE somerset_shrimp_db;
CREATE USER shrimp_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE somerset_shrimp_db TO shrimp_user;
ALTER USER shrimp_user CREATEDB;  -- Allows running tests
\q
```

### Method 2: Using pgAdmin (GUI)
1. Open pgAdmin (installed with PostgreSQL)
2. Connect to your PostgreSQL server
3. Right-click "Databases" → Create → Database
4. Name: `somerset_shrimp_db`
5. Right-click "Login/Group Roles" → Create → Login/Group Role
6. Name: `shrimp_user`, set password in "Definition" tab
7. In "Privileges" tab, check "Can login?" and "Create databases?"

## Step 3: Configure Django Settings

### Option 1: Using DATABASE_URL (Recommended)
Create a `.env` file in your project root:
```bash
cp .env.example .env
```

Edit `.env` and add:
```bash
# PostgreSQL connection
DATABASE_URL=postgresql://shrimp_user:your_secure_password@localhost:5432/somerset_shrimp_db

# Other required settings
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
STRIPE_PUBLIC_KEY=pk_test_your_key
STRIPE_SECRET_KEY=sk_test_your_key
```

### Option 2: Individual Settings
Alternatively, you can use individual database settings in `.env`:
```bash
DB_ENGINE=django.db.backends.postgresql
DB_NAME=somerset_shrimp_db
DB_USER=shrimp_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432
```

## Step 4: Test Database Connection

Test the connection:
```bash
python manage.py check --database default
```

If successful, you should see "System check identified no issues."

## Step 5: Run Migrations

```bash
# Apply all migrations
python manage.py migrate

# Create a superuser for admin access
python manage.py createsuperuser
```

## Step 6: Load Initial Data (Optional)

If you have existing data in SQLite, you can transfer it:

```bash
# Export data from SQLite (if you have existing data)
python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission --indent 2 > data_backup.json

# Load data into PostgreSQL
python manage.py loaddata data_backup.json
```

## Step 7: Verify Setup

```bash
# Run the development server
python manage.py runserver

# Test admin interface
# Go to http://127.0.0.1:8000/admin/
```

## Common Issues and Solutions

### Issue: "psycopg2" not found
**Solution:** The project already includes `psycopg2-binary` in requirements.txt. If you get this error:
```bash
pip install psycopg2-binary
```

### Issue: Connection refused
**Solution:** 
1. Check if PostgreSQL is running:
   - Windows: Check Services for "postgresql" 
   - macOS: `brew services list | grep postgresql`
   - Linux: `sudo systemctl status postgresql`

2. Check connection parameters in your `.env` file

### Issue: Authentication failed
**Solution:**
1. Verify username/password in `.env` file
2. Reset password if needed:
```sql
ALTER USER shrimp_user PASSWORD 'new_password';
```

### Issue: Database doesn't exist
**Solution:**
```sql
CREATE DATABASE somerset_shrimp_db;
```

### Issue: Permission denied
**Solution:**
```sql
GRANT ALL PRIVILEGES ON DATABASE somerset_shrimp_db TO shrimp_user;
```

## Production Considerations

### For Production Deployment:
1. Use environment variables for all sensitive data
2. Enable SSL for database connections
3. Set up database backups
4. Use connection pooling (like pgbouncer)
5. Monitor database performance

### Example Production DATABASE_URL:
```bash
DATABASE_URL=postgresql://username:password@db.example.com:5432/somerset_shrimp_prod?sslmode=require
```

## Database Backup and Restore

### Backup:
```bash
pg_dump -U shrimp_user -h localhost somerset_shrimp_db > backup.sql
```

### Restore:
```bash
psql -U shrimp_user -h localhost somerset_shrimp_db < backup.sql
```

## Performance Tips

1. **Indexes**: The project includes optimized database indexes
2. **Connection Pooling**: Consider using pgbouncer for production
3. **Monitoring**: Use tools like pg_stat_statements for query analysis
4. **Regular Maintenance**: Run VACUUM and ANALYZE regularly

## Security Best Practices

1. Use strong passwords
2. Limit database user permissions
3. Enable SSL in production
4. Regularly update PostgreSQL
5. Monitor access logs
6. Use environment variables for credentials

## Need Help?

If you encounter issues:
1. Check PostgreSQL logs
2. Verify connection parameters
3. Ensure PostgreSQL service is running
4. Check firewall settings
5. Consult the project's README.md for additional troubleshooting
