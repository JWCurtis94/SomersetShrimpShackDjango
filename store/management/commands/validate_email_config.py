"""
Django management command to validate email configuration
This command checks email settings and tests email functionality
"""
from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Validate email configuration and test email functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-email',
            type=str,
            help='Send a test email to the specified address'
        )
        parser.add_argument(
            '--production-check',
            action='store_true',
            help='Perform production-specific email validation checks'
        )

    def handle(self, *args, **options):
        """Main command handler"""
        self.stdout.write(self.style.HTTP_INFO('Email Configuration Validation'))
        self.stdout.write('=' * 50)
        
        # Basic configuration check
        self._check_basic_email_config()
        
        # Production-specific checks
        if options['production_check'] or not settings.DEBUG:
            self._check_production_email_config()
        
        # Test email sending
        if options['test_email']:
            self._send_test_email(options['test_email'])
        
        self.stdout.write(self.style.SUCCESS('\n✅ Email configuration validation completed'))

    def _check_basic_email_config(self):
        """Check basic email configuration"""
        self.stdout.write(self.style.HTTP_INFO('\n📧 Basic Email Configuration:'))
        
        # Check email backend
        email_backend = getattr(settings, 'EMAIL_BACKEND', None)
        if email_backend:
            self.stdout.write(f'✓ Email Backend: {email_backend}')
            
            if 'console' in email_backend.lower():
                self.stdout.write(self.style.WARNING('  ⚠️  Using console backend (development only)'))
            elif 'smtp' in email_backend.lower():
                self.stdout.write('  ✓ Using SMTP backend (production ready)')
        else:
            self.stdout.write(self.style.ERROR('✗ EMAIL_BACKEND not configured'))
            raise CommandError('EMAIL_BACKEND setting is required')
        
        # Check DEFAULT_FROM_EMAIL
        default_from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        if default_from_email:
            self.stdout.write(f'✓ Default From Email: {default_from_email}')
        else:
            self.stdout.write(self.style.WARNING('⚠️  DEFAULT_FROM_EMAIL not set'))
        
        # Check ADMIN_EMAIL
        admin_email = getattr(settings, 'ADMIN_EMAIL', None)
        if admin_email:
            self.stdout.write(f'✓ Admin Email: {admin_email}')
        else:
            self.stdout.write(self.style.WARNING('⚠️  ADMIN_EMAIL not set (using default)'))

    def _check_production_email_config(self):
        """Check production-specific email configuration"""
        self.stdout.write(self.style.HTTP_INFO('\n🔒 Production Email Configuration:'))
        
        if 'console' in getattr(settings, 'EMAIL_BACKEND', '').lower():
            self.stdout.write(self.style.ERROR('✗ Console email backend in production'))
            raise CommandError('Console email backend not suitable for production')
        
        # Check SMTP settings
        required_smtp_settings = [
            'EMAIL_HOST',
            'EMAIL_PORT', 
            'EMAIL_HOST_USER',
            'EMAIL_HOST_PASSWORD'
        ]
        
        for setting_name in required_smtp_settings:
            value = getattr(settings, setting_name, None)
            if value:
                if setting_name == 'EMAIL_HOST_PASSWORD':
                    # Don't log password, just confirm it exists
                    self.stdout.write(f'✓ {setting_name}: [CONFIGURED]')
                else:
                    self.stdout.write(f'✓ {setting_name}: {value}')
            else:
                self.stdout.write(self.style.ERROR(f'✗ {setting_name} not configured'))
                if not settings.DEBUG:
                    raise CommandError(f'{setting_name} is required for production')
        
        # Check TLS/SSL settings
        email_use_tls = getattr(settings, 'EMAIL_USE_TLS', False)
        email_use_ssl = getattr(settings, 'EMAIL_USE_SSL', False)
        
        if email_use_tls:
            self.stdout.write('✓ EMAIL_USE_TLS: Enabled')
        elif email_use_ssl:
            self.stdout.write('✓ EMAIL_USE_SSL: Enabled')
        else:
            self.stdout.write(self.style.WARNING('⚠️  Neither TLS nor SSL enabled for email'))
        
        # Validate email addresses format
        self._validate_email_addresses()

    def _validate_email_addresses(self):
        """Validate format of configured email addresses"""
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        email_settings = {
            'DEFAULT_FROM_EMAIL': getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            'ADMIN_EMAIL': getattr(settings, 'ADMIN_EMAIL', None),
        }
        
        for setting_name, email in email_settings.items():
            if email:
                try:
                    validate_email(email)
                    self.stdout.write(f'✓ {setting_name} format valid')
                except ValidationError:
                    self.stdout.write(self.style.ERROR(f'✗ {setting_name} format invalid: {email}'))

    def _send_test_email(self, recipient_email):
        """Send a test email to verify configuration"""
        self.stdout.write(self.style.HTTP_INFO(f'\n📤 Sending test email to {recipient_email}:'))
        
        try:
            from django.core.validators import validate_email
            validate_email(recipient_email)
            
            subject = 'Somerset Shrimp Shack - Email Configuration Test'
            message = '''
This is a test email from Somerset Shrimp Shack.

If you received this email, your email configuration is working correctly.

Email Configuration Details:
- Email Backend: {}
- From Email: {}
- Admin Email: {}

Time: {}
            '''.format(
                getattr(settings, 'EMAIL_BACKEND', 'Not configured'),
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not configured'),
                getattr(settings, 'ADMIN_EMAIL', 'Not configured'),
                self._get_current_time()
            )
            
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                recipient_list=[recipient_email],
                fail_silently=False,
            )
            
            self.stdout.write(self.style.SUCCESS(f'✅ Test email sent successfully to {recipient_email}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed to send test email: {str(e)}'))
            logger.error(f'Email configuration test failed: {str(e)}')
            raise CommandError(f'Email test failed: {str(e)}')

    def _get_current_time(self):
        """Get current time as string"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
