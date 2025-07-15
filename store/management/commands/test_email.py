from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from store.models import Order
from store.utils import send_order_confirmation_email, send_order_notification_email

class Command(BaseCommand):
    help = 'Test email notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--order-id',
            type=int,
            help='Order ID to test email with (optional)',
        )
        parser.add_argument(
            '--test-email',
            type=str,
            help='Email address to send test to',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing email configuration...'))
        
        # Test basic email sending
        if options['test_email']:
            try:
                send_mail(
                    subject='Test Email from Somerset Shrimp Shack',
                    message='This is a test email to verify email configuration is working.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[options['test_email']],
                    fail_silently=False,
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Test email sent successfully to {options["test_email"]}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to send test email: {str(e)}')
                )
                return
        
        # Test order email notifications
        if options['order_id']:
            try:
                order = Order.objects.get(id=options['order_id'])
                
                # Test customer confirmation email
                if send_order_confirmation_email(order):
                    self.stdout.write(
                        self.style.SUCCESS(f'Order confirmation email sent for order #{order.id}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to send order confirmation email for order #{order.id}')
                    )
                
                # Test admin notification email
                if send_order_notification_email(order):
                    self.stdout.write(
                        self.style.SUCCESS(f'Order notification email sent for order #{order.id}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to send order notification email for order #{order.id}')
                    )
                    
            except Order.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Order #{options["order_id"]} not found')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error testing order emails: {str(e)}')
                )
        
        self.stdout.write(self.style.SUCCESS('Email testing completed.'))
