# HEROKU DATABASE CONFIGURATION GUIDE

## 🚀 **Database Setup for Heroku Deployment**

### ✅ **What I Fixed:**

1. **Removed local PostgreSQL URL** - Heroku provides this automatically
2. **Secured email password** - Removed plain text password
3. **Set SQLite for local development** - Better for testing

### 📋 **Heroku Database Setup Steps:**

#### Step 1: Add PostgreSQL to Your Heroku App
```bash
# Add Heroku Postgres addon (free tier)
heroku addons:create heroku-postgresql:essential-0 --app your-app-name

# Check database URL (Heroku sets this automatically)
heroku config --app your-app-name
```

#### Step 2: Environment Variables for Heroku
Set these in Heroku dashboard or via CLI:

```bash
# Set production environment variables
heroku config:set DEBUG=False --app your-app-name
heroku config:set DJANGO_SECRET_KEY=your-super-secret-production-key --app your-app-name

# Email settings
heroku config:set EMAIL_HOST=smtp.gmail.com --app your-app-name
heroku config:set EMAIL_PORT=587 --app your-app-name
heroku config:set EMAIL_USE_TLS=True --app your-app-name
heroku config:set EMAIL_HOST_USER=info@somersetshrimpshack.uk --app your-app-name
heroku config:set EMAIL_HOST_PASSWORD=your-gmail-app-password --app your-app-name
heroku config:set DEFAULT_FROM_EMAIL="Somerset Shrimp Shack <noreply@somersetshrimpshack.uk>" --app your-app-name
heroku config:set ADMIN_EMAIL=info@somersetshrimpshack.uk --app your-app-name

# Stripe settings
heroku config:set STRIPE_PUBLIC_KEY=pk_live_your_live_key --app your-app-name
heroku config:set STRIPE_SECRET_KEY=sk_live_your_live_key --app your-app-name
heroku config:set STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret --app your-app-name
```

#### Step 3: Database Migration on Heroku
```bash
# Run migrations on Heroku
heroku run python manage.py migrate --app your-app-name

# Create superuser on Heroku
heroku run python manage.py createsuperuser --app your-app-name
```

### 🔍 **How Heroku Database Works:**

1. **Automatic DATABASE_URL**: Heroku automatically provides a `DATABASE_URL` environment variable
2. **Dynamic URLs**: Heroku database URLs can change, so never hardcode them
3. **Your settings.py handles this**: The existing code automatically detects Heroku's DATABASE_URL

### 🛠 **Local vs Heroku Configuration:**

#### Local Development (.env file):
```bash
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3  # SQLite for local testing
EMAIL_HOST_PASSWORD=your-gmail-app-password
```

#### Heroku Production (Config Vars):
```bash
DEBUG=False
DATABASE_URL=postgres://... # Automatically provided by Heroku
EMAIL_HOST_PASSWORD=your-gmail-app-password
```

### ⚠️ **Important Security Notes:**

1. **Never commit passwords** to version control
2. **Use different Stripe keys** for production (live keys, not test keys)
3. **Use Gmail App Password**, not your regular Gmail password
4. **Set DEBUG=False** in production

### 📧 **Gmail App Password Setup:**

1. Go to Google Account settings
2. Security → 2-Step Verification (must be enabled)
3. App passwords → Generate new password
4. Use this 16-character password in EMAIL_HOST_PASSWORD

### 🧪 **Testing Database Connection:**

```bash
# Test locally
python manage.py check --deploy

# Test on Heroku
heroku run python manage.py check --deploy --app your-app-name
```

Your database configuration is now properly set up for both local development and Heroku production! 🎉
