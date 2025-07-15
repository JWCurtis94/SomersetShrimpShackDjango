from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_order_confirmation_email(order):
    """
    Send order confirmation email to customer
    """
    try:
        # Prepare email context
        context = {
            'order': order,
            'order_items': order.items.all(),
            'total': order.total_price,
            'shipping_cost': order.shipping_cost,
            'site_name': 'Somerset Shrimp Shack',
        }
        
        # Render email content
        subject = f'Order Confirmation - #{order.id}'
        html_message = render_to_string('store/emails/order_confirmation.html', context)
        plain_message = render_to_string('store/emails/order_confirmation.txt', context)
        
        # Send email to customer
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Order confirmation email sent to {order.email} for order #{order.id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send order confirmation email for order #{order.id}: {str(e)}")
        return False

def send_order_notification_email(order):
    """
    Send order notification email to site owner/admin
    """
    try:
        # Prepare email context
        context = {
            'order': order,
            'order_items': order.items.all(),
            'total': order.total_price,
            'shipping_cost': order.shipping_cost,
            'site_name': 'Somerset Shrimp Shack',
        }
        
        # Render email content
        subject = f'New Order Received - #{order.id}'
        html_message = render_to_string('store/emails/order_notification.html', context)
        plain_message = render_to_string('store/emails/order_notification.txt', context)
        
        # Get admin email from settings or use default
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'admin@somersetshrimp.com')
        
        # Send email to admin
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Order notification email sent to {admin_email} for order #{order.id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send order notification email for order #{order.id}: {str(e)}")
        return False
