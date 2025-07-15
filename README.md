# Somerset Shrimp Shack - Django E-commerce Project

A professional e-commerce website for aquarium shrimp, plants, and supplies built with Django.

## 🚀 Features

- **Product Catalog**: Browse shrimp, plants, and aquarium supplies by category
- **Shopping Cart**: Add/remove items, update quantities
- **User Authentication**: Registration, login, password reset
- **Order Management**: Complete checkout process with Stripe integration
- **Admin Dashboard**: Product management, order tracking, inventory control
- **Care Guides**: Comprehensive guides for shrimp and plant care
- **Responsive Design**: Mobile-friendly interface
- **Search & Filtering**: Find products easily

## 🛠️ Quick Setup

### Prerequisites
- Python 3.10+
- pip (Python package manager)
- PostgreSQL (optional, SQLite used by default)

### Installation

1. **Clone and Navigate**
   ```bash
   cd SomersetShrimpShackDjango-main
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux/Mac
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   copy .env.example .env
   # Edit .env with your settings (optional for development)
   ```

5. **Database Setup**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Collect Static Files**
   ```bash
   python manage.py collectstatic --noinput
   ```

7. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

Visit `http://127.0.0.1:8000` to see your application!

## 🔧 Configuration

### Environment Variables

Create a `.env` file (copy from `.env.example`) with:

```env
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
STRIPE_PUBLIC_KEY=pk_test_your_stripe_key
STRIPE_SECRET_KEY=sk_test_your_stripe_key
```

### Database Options

**SQLite (Default)**
- No additional setup required
- Perfect for development

**PostgreSQL (Production)**
```env
DATABASE_URL=postgres://username:password@localhost:5432/dbname
```

## 📚 Usage

### Admin Access
1. Create superuser: `python manage.py createsuperuser`
2. Visit `/admin/` to manage products, categories, and orders

### Adding Products
1. Access admin panel
2. Go to "Products" → "Add Product"
3. Fill in details and upload images
4. Set category, price, and stock levels

### Managing Orders
- View orders in admin panel
- Update order status (pending → paid → shipped → delivered)
- Track inventory automatically

## 🚀 Deployment

### Production Checklist

1. **Environment Variables**
   ```env
   DEBUG=False
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   DJANGO_SECRET_KEY=secure-random-key
   DATABASE_URL=postgres://...
   ```

2. **Security Settings**
   ```bash
   python manage.py check --deploy
   ```

3. **Static Files**
   ```bash
   python manage.py collectstatic --noinput
   ```

4. **Database Migration**
   ```bash
   python manage.py migrate
   ```

### Deployment Platforms

**Heroku**
```bash
git push heroku main
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

**Railway/DigitalOcean**
- Configure environment variables
- Set up PostgreSQL database
- Run migrations

## 🏗️ Project Structure

```
Somerset-Shrimp-Shack/
├── ecommerce/          # Project settings
├── store/              # Main application
│   ├── models.py       # Database models
│   ├── views.py        # Business logic
│   ├── urls.py         # URL routing
│   ├── forms.py        # Django forms
│   ├── admin.py        # Admin configuration
│   ├── static/         # CSS, JS, images
│   └── templates/      # HTML templates
├── staticfiles/        # Collected static files
├── media/              # User uploads
├── requirements.txt    # Python dependencies
└── manage.py          # Django management
```

## 🔧 Development

### Running Tests
```bash
python manage.py test
```

### Code Quality
```bash
python manage.py check
python manage.py check --deploy
```

### Debug Mode
- Set `DEBUG=True` in `.env`
- Access debug toolbar at `/__debug__/`

## 📦 Key Dependencies

- **Django 5.0.6**: Web framework
- **Stripe**: Payment processing
- **Pillow**: Image handling
- **WhiteNoise**: Static file serving
- **django-allauth**: Authentication
- **psycopg2-binary**: PostgreSQL support

## 🆘 Troubleshooting

### Common Issues

**Static files not loading**
```bash
python manage.py collectstatic --noinput
```

**Database errors**
```bash
python manage.py migrate
```

**Permission errors**
- Check file permissions
- Ensure media/static directories are writable

### Getting Help

1. Check Django logs in console
2. Review error messages carefully
3. Ensure all environment variables are set
4. Verify database connectivity

## 📜 License

This project is for educational/commercial use. Please check with the original authors for licensing terms.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

---

**Somerset Shrimp Shack** - Premium aquarium supplies delivered to your door! 🦐🌱
