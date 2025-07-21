from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

def send_order_confirmation_email(order):
    """
    Send a detailed order confirmation email to the customer.
    """
    try:
        order_items = order.items.all()

        context = {
            'order': order,
            'order_items': order_items,
            'total': order.total_amount,
            'shipping_cost': Decimal('0.00'),  # No separate shipping cost in current model
            'site_name': 'Somerset Shrimp Shack',
            'customer_name': getattr(order, 'shipping_name', ''),
            'shipping_info': {
                'address': getattr(order, 'shipping_address', ''),
                'city': getattr(order, 'shipping_city', ''),
                'state': getattr(order, 'shipping_state', ''),
                'zip': getattr(order, 'shipping_zip', ''),
                'country': getattr(order, 'shipping_country', ''),
            }
        }

        subject = f'Order Confirmation - #{order.order_reference}'
        html_message = render_to_string('store/emails/order_confirmation.html', context)
        plain_message = render_to_string('store/emails/order_confirmation.txt', context)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Confirmation email sent to customer {order.email} for order #{order.id}")
        return True

    except Exception as e:
        logger.error(f"Failed to send confirmation email for order #{order.id}: {str(e)}")
        return False


def send_order_notification_email(order):
    """
    Send a detailed order notification email to the site owner/admin.
    """
    try:
        order_items = order.items.all()

        context = {
            'order': order,
            'order_items': order_items,
            'total': order.total_amount,
            'shipping_cost': Decimal('0.00'),  # No separate shipping cost in current model
            'site_name': 'Somerset Shrimp Shack',
            'customer_name': getattr(order, 'shipping_name', ''),
            'shipping_info': {
                'address': getattr(order, 'shipping_address', ''),
                'city': getattr(order, 'shipping_city', ''),
                'state': getattr(order, 'shipping_state', ''),
                'zip': getattr(order, 'shipping_zip', ''),
                'country': getattr(order, 'shipping_country', ''),
            }
        }

        subject = f'New Order Received - #{order.order_reference}'
        html_message = render_to_string('store/emails/order_notification.html', context)
        plain_message = render_to_string('store/emails/order_notification.txt', context)

        admin_email = getattr(settings, 'ADMIN_EMAIL', 'admin@somersetshrimp.com')

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Order notification email sent to admin {admin_email} for order #{order.id}")
        return True

    except Exception as e:
        logger.error(f"Failed to send order notification email for order #{order.id}: {str(e)}")
        return False
