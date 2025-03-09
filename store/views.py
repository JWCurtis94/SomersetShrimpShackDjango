from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum, F, Q, Count
from django.core.paginator import Paginator
from .models import Product, Order, OrderItem
from .cart import Cart
from decimal import Decimal
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import UserCreationForm
import stripe
import json
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Set up Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY

# Helper Functions
def is_staff(user):
    """Check if user is staff"""
    return user.is_staff

def paginate_queryset(request, queryset, per_page=12):
    """Helper function to paginate querysets"""
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page', 1)
    return paginator.get_page(page_number)

###################
# Public Views
###################

def product_list(request):
    """Display list of all available products with filters and sorting"""
    # Extract filters from request
    category = request.GET.get('category')
    sort = request.GET.get('sort', 'name')  # Default sort by name
    search = request.GET.get('search', '')
    in_stock = request.GET.get('in_stock')
    
    # Start with all products that are available
    products = Product.objects.filter(available=True)
    
    # Apply filters if provided
    if category:
        products = products.filter(category=category)
        
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search)
        )
    
    if in_stock == "1":
        products = products.filter(stock__gt=0)
    
    # Apply sorting
    if sort == 'price-asc':
        products = products.order_by('price')
    elif sort == 'price-desc':
        products = products.order_by('-price')
    elif sort == 'newest':
        products = products.order_by('-created_at')
    else:  # Default to name
        products = products.order_by('name')
    
    # Setup pagination
    products_page = paginate_queryset(request, products)
    
    # Get all available categories for the filter with product count
    category_counts = Product.objects.filter(available=True).values(
        'category'
    ).annotate(count=Count('id')).order_by('category')
    
    categories = dict(Product.CATEGORY_CHOICES)
    
    return render(request, 'store/product_list.html', {
        'products': products_page,
        'categories': categories,
        'category_counts': category_counts,
        'current_category': category,
        'current_sort': sort,
        'search_query': search,
        'in_stock_only': in_stock == "1",
    })

def product_detail(request, product_id):
    """Show detailed information about a product"""
    product = get_object_or_404(Product, id=product_id)
    
    # Load related products in same category
    related_products = Product.objects.filter(
        category=product.category, 
        available=True
    ).exclude(id=product.id)[:4]
    
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'sizes': Product.SIZE_CHOICES if hasattr(Product, 'SIZE_CHOICES') else None
    })

def care_guides(request):
    """Display care guides for shrimp and fish"""
    return render(request, 'store/care_guides.html')

###################
# Cart Views
###################

def cart_view(request):
    """Show current cart contents"""
    cart = Cart(request)
    cart_items = cart.get_cart_items()
    
    # Calculate cart totals
    total_price = cart.get_total_price()
    
    # Only apply shipping cost if cart is not empty
    shipping_cost = Decimal('4.99') if total_price > 0 else Decimal('0')
    grand_total = total_price + shipping_cost if total_price > 0 else Decimal('0')
    
    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'shipping_cost': shipping_cost,
        'grand_total': grand_total,
        'item_count': cart.get_item_count()
    })

def add_to_cart(request, product_id):
    """Add a product to the shopping cart"""
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    
    # Check if product is in stock and available
    if not product.is_in_stock:
        messages.error(request, f"Sorry, {product.name} is out of stock.")
        return redirect('store:product_detail', product_id=product_id)
    
    # Process form data if POST request
    if request.method == 'POST':
        # Extract quantity from form
        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            quantity = 1
            
        # Extract size if provided
        size = request.POST.get('size')
        
        # Validate quantity
        if quantity <= 0:
            quantity = 1
        
        # Check against available stock
        if quantity > product.stock:
            messages.warning(request, f"Only {product.stock} items available. Adding maximum quantity.")
            quantity = product.stock
        
        # Add to cart
        cart.add(product, quantity=quantity, size=size)
        
        product_name = product.name
        if size:
            product_name = f"{product_name} ({size})"
            
        messages.success(request, f"Added {quantity}x {product_name} to your cart.")
        
        # Redirect based on 'next' parameter or to cart
        next_url = request.POST.get('next')
        if next_url:
            try:
                return redirect(next_url)
            except:
                # If redirect fails (e.g., invalid URL), fall back to cart view
                pass
                
        return redirect('store:cart_view')
    
    # If not POST, redirect to product detail
    return redirect('store:product_detail', product_id=product_id)

def remove_from_cart(request, product_id):
    """Remove a product from the shopping cart"""
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    
    # Extract size from query parameters or POST data
    size = request.GET.get('size') or request.POST.get('size')
    
    # Remove the product
    if cart.remove(product, size=size):
        product_name = product.name
        if size:
            product_name = f"{product_name} ({size})"
        messages.success(request, f"Removed {product_name} from your cart.")
    else:
        messages.error(request, "Item could not be removed from cart.")
    
    return redirect('store:cart_view')

def update_cart(request, product_id):
    """Update quantity of a product in the cart"""
    cart = Cart(request)
    
    if request.method == "POST":
        try:
            # Extract quantity and size
            new_quantity = int(request.POST.get('quantity', 1))
            size = request.POST.get('size')
            
            # Get product for stock validation
            product = get_object_or_404(Product, id=product_id)
            
            # Validate against stock availability
            if new_quantity > product.stock:
                messages.warning(request, f"Only {product.stock} items available. Setting to maximum.")
                new_quantity = product.stock
                
            # Update the cart
            if cart.update(product_id, new_quantity, size=size):
                messages.success(request, "Cart updated successfully.")
            else:
                messages.error(request, "Failed to update cart. Item not found.")
                
        except ValueError:
            messages.error(request, "Invalid quantity provided.")

    # Redirect to referring page if available, otherwise to cart view
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect("store:cart_view")

def clear_cart(request):
    """Remove all items from the cart"""
    cart = Cart(request)
    cart.clear()
    messages.success(request, "Your cart has been cleared.")
    return redirect("store:cart_view")

###################
# Checkout Views
###################

def checkout(request, product_id):
    """Process checkout for a single product"""
    product = get_object_or_404(Product, id=product_id)
    
    # Check stock and availability
    if not product.is_in_stock:
        messages.error(request, f"{product.name} is currently out of stock.")
        return redirect("store:product_detail", product_id=product.id)

    # Get quantity and size
    quantity = int(request.POST.get('quantity', 1))
    size = request.POST.get('size')
    
    # Validate quantity against stock
    if quantity > product.stock:
        messages.warning(request, f"Only {product.stock} items available. Setting to maximum.")
        quantity = product.stock
    
    # Get customer email for order
    email = request.user.email if request.user.is_authenticated else request.POST.get('email')
    
    if not email:
        messages.error(request, "Email address is required for checkout.")
        return redirect("store:product_detail", product_id=product.id)

    try:
        # Create Stripe checkout session
        product_name = f"{product.name}{f' - {size}' if size else ''}"
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'gbp',
                    'product_data': {
                        'name': product_name,
                        'description': product.description[:255] if product.description else None,
                        'images': [request.build_absolute_uri(product.image.url)] if product.image else None,
                    },
                    'unit_amount': int(product.price * 100),  # Convert to pence
                },
                'quantity': quantity,
            }],
            mode='payment',
            success_url=request.build_absolute_uri('/store/success/'),
            cancel_url=request.build_absolute_uri('/store/cancel/'),
            metadata={
                'product_id': product.id,
                'quantity': quantity,
                'size': size if size else '',
                'email': email,
                'user_id': request.user.id if request.user.is_authenticated else None,
            }
        )
        
        # Create preliminary order
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            email=email,
            stripe_checkout_id=session.id,
            status='pending',
            total_amount=product.price * quantity,  # Using total_amount from model
            shipping_address='To be provided',
            created_at=timezone.now()
        )
        
        # Create order item
        OrderItem.objects.create(
            order=order,
            product=product,
            price=product.price,
            quantity=quantity,
            size=size
        )
        
        return redirect(session.url)
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        messages.error(request, f"Payment error: {str(e)}")
        return redirect("store:product_detail", product_id=product.id)
    except Exception as e:
        logger.error(f"Error in checkout: {str(e)}")
        messages.error(request, "An error occurred during checkout. Please try again.")
        return redirect("store:product_detail", product_id=product.id)

def checkout_cart(request):
    """Process checkout for entire cart"""
    cart = Cart(request)
    cart_items = cart.get_cart_items()
    
    # Check if cart is empty
    if not cart_items:
        messages.warning(request, "Your cart is empty.")
        return redirect("store:cart_view")
    
    # Get customer email    
    email = request.user.email if request.user.is_authenticated else request.POST.get('email')
    
    if request.method == 'POST':
        # Validate email
        if not email:
            messages.error(request, "Email address is required for checkout.")
            return render(request, "store/checkout.html", {
                "cart_items": cart_items,
                "total": cart.get_total_price(),
                "shipping_cost": Decimal('4.99'),
                "grand_total": cart.get_total_price() + Decimal('4.99'),
            })
        
        # Calculate totals
        total = cart.get_total_price()
        shipping_cost = Decimal('4.99')
        grand_total = total + shipping_cost
        
        # Stock validation for all items
        for item in cart_items:
            if item.quantity > item.product.stock:
                messages.warning(
                    request, 
                    f"Only {item.product.stock} of {item.product.name} available. "
                    f"Please update your cart quantity."
                )
                return redirect("store:cart_view")
        
        try:
            # Create line items for Stripe
            line_items = []
            metadata = {
                'cart': 'true',
                'email': email,
                'user_id': request.user.id if request.user.is_authenticated else None,
            }
            
            # Add product items
            for i, item in enumerate(cart_items):
                product = item.product
                product_name = f"{product.name}{f' - {item.size}' if item.size else ''}"
                
                line_items.append({
                    'price_data': {
                        'currency': 'gbp',
                        'product_data': {
                            'name': product_name,
                            'images': [request.build_absolute_uri(product.image.url)] if product.image else None,
                        },
                        'unit_amount': int(product.price * 100),  # Convert to pence
                    },
                    'quantity': item.quantity,
                })
                
                # Add item details to metadata
                metadata[f'item_{i}_product_id'] = product.id
                metadata[f'item_{i}_quantity'] = item.quantity
                if item.size:
                    metadata[f'item_{i}_size'] = item.size
                
            # Add shipping cost as separate line item
            line_items.append({
                'price_data': {
                    'currency': 'gbp',
                    'product_data': {
                        'name': 'Shipping',
                    },
                    'unit_amount': int(shipping_cost * 100),  # Convert to pence
                },
                'quantity': 1,
            })
            
            # Create Stripe checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=request.build_absolute_uri('/store/success/'),
                cancel_url=request.build_absolute_uri('/store/cancel/'),
                shipping_address_collection={
                    'allowed_countries': ['GB'],  # UK only for now
                },
                metadata=metadata
            )
            
            # Create preliminary order
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                email=email,
                stripe_checkout_id=session.id,
                status='pending',
                total_amount=grand_total,  # Using total_amount from model
                shipping_address='To be provided via Stripe',
                created_at=timezone.now()
            )
            
            # Create order items
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.price,
                    quantity=item.quantity,
                    size=item.size
                )
            
            return redirect(session.url)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error in cart checkout: {str(e)}")
            messages.error(request, f"Payment error: {str(e)}")
            return redirect("store:cart_view")
        except Exception as e:
            logger.error(f"Error in cart checkout: {str(e)}")
            messages.error(request, "An error occurred during checkout. Please try again.")
            return redirect("store:cart_view")
    
    # GET request - show checkout form
    return render(request, "store/checkout.html", {
        "cart_items": cart_items,
        "total": cart.get_total_price(),
        "shipping_cost": Decimal('4.99'),
        "grand_total": cart.get_total_price() + Decimal('4.99'),
    })

def payment_success(request):
    """Handle successful payment"""
    cart = Cart(request)
    cart.clear()  # Clear the cart after successful payment
    
    return render(request, "store/payment_success.html")

def payment_cancel(request):
    """Handle cancelled payment"""
    return render(request, "store/payment_cancel.html")

###################
# Webhook Handlers
###################

@require_POST
def stripe_webhook(request):
    """
    Handle Stripe webhook events (esp. for payment confirmations)
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    
    try:
        # Verify webhook signature and extract event
        if webhook_secret:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        else:
            # Without webhook signing, just parse the payload
            data = json.loads(payload)
            event = stripe.Event.construct_from(data, stripe.api_key)
    except ValueError as e:
        logger.error(f"Invalid payload: {str(e)}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {str(e)}")
        return HttpResponse(status=400)

    # Handle the specific event types
    if event.type == 'checkout.session.completed':
        session = event.data.object  # Stripe Checkout Session
        
        try:
            # Find the corresponding order
            order = Order.objects.get(stripe_checkout_id=session.id)
            
            # Update order status and payment date
            order.status = 'paid'
            order.payment_date = timezone.now()
            
            # Get shipping details from the session
            if hasattr(session, 'shipping') and session.shipping:
                name = session.shipping.name
                address = session.shipping.address
                
                order.shipping_name = name
                order.shipping_address = address.line1
                if hasattr(address, 'line2') and address.line2:
                    order.shipping_address += f"\n{address.line2}"
                order.shipping_city = address.city
                order.shipping_state = address.state
                order.shipping_zip = address.postal_code
                order.shipping_country = address.country
            
            order.save()
            
            # Update product stock levels
            for item in order.items.all():
                product = item.product
                if product.stock >= item.quantity:
                    product.stock -= item.quantity
                    product.save()
                else:
                    logger.warning(f"Order #{order.id}: Not enough stock for {product.name}")
            
            logger.info(f"Payment for order #{order.id} completed successfully")
            
        except Order.DoesNotExist:
            logger.error(f"Order not found for session ID: {session.id}")
            return HttpResponse(status=404)
    
    # Acknowledge receipt of the event
    return HttpResponse(status=200)

###################
# Order Views
###################

@login_required
def order_history(request):
    """
    Display order history for the logged-in user
    """
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    return render(request, 'store/order_history.html', {
        'orders': orders,
        'title': 'Your Order History',
    })

@login_required
def order_detail(request, order_id):
    """
    Display detailed information about a specific order
    """
    # If user is logged in, ensure they can only view their own orders
    # Staff users can view any order
    if request.user.is_authenticated and not request.user.is_staff:
        order = get_object_or_404(Order, id=order_id, user=request.user)
    elif request.user.is_staff:
        order = get_object_or_404(Order, id=order_id)
    else:
        # Should not happen with @login_required, but just in case
        return redirect(f"{settings.LOGIN_URL}?next={request.path}")
    
    # Get all items for this order
    order_items = order.items.all()
    
    return render(request, 'store/order_detail.html', {
        'order': order,
        'order_items': order_items,
        'title': f'Order #{order.order_reference or order.id}',
    })

@login_required
def order_summary(request):
    """
    Display a summary of the most recent order (typically used after checkout)
    """
    # Try to get the most recent order for the user
    try:
        order = Order.objects.filter(user=request.user).latest('created_at')
        return render(request, 'store/order_summary.html', {
            'order': order, 
            'title': 'Order Summary'
        })
    except Order.DoesNotExist:
        messages.warning(request, "You don't have any orders yet.")
        return redirect('store:product_list')

###################
# Admin Views
###################

@staff_member_required
def dashboard(request):
    """
    Admin dashboard showing key metrics
    """
    # Get counts for dashboard stats
    products_count = Product.objects.count()
    orders_count = Order.objects.count()
    recent_orders = Order.objects.order_by('-created_at')[:5]
    low_stock_products = Product.objects.filter(stock__lte=5, available=True).order_by('stock')[:5]
    
    # Calculate total revenue - using total_amount instead of total_price
    total_revenue = Order.objects.filter(status='paid').aggregate(
        total=Sum(F('total_amount'))
    )['total'] or Decimal('0')
    
    # Get monthly order counts
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    monthly_orders = []
    for i in range(6):  # Past 6 months
        month = (current_month - i) % 12 or 12  # Handle December (0)
        year = current_year if month <= current_month else current_year - 1
        
        count = Order.objects.filter(
            created_at__month=month,
            created_at__year=year,
            status='paid'
        ).count()
        
        month_name = timezone.datetime(year, month, 1).strftime('%b')
        monthly_orders.append({'month': month_name, 'count': count})
    
    # Reverse to show oldest to newest
    monthly_orders.reverse()
    
    return render(request, 'store/dashboard.html', {
        'title': 'Admin Dashboard',
        'products_count': products_count,
        'orders_count': orders_count,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'low_stock_products': low_stock_products,
        'monthly_orders': monthly_orders,
    })

@staff_member_required
def stock_management(request):
    """
    View for managing product stock levels
    """
    # Extract filters from request
    category = request.GET.get('category')
    stock_status = request.GET.get('stock_status')
    search = request.GET.get('search', '')
    
    # Start with all products
    products = Product.objects.all()
    
    # Apply filters if provided
    if category:
        products = products.filter(category=category)
        
    if stock_status:
        if stock_status == 'low':
            products = products.filter(stock__gt=0, stock__lte=5)
        elif stock_status == 'out':
            products = products.filter(stock=0)
    
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(id__icontains=search)
        )
    
    # Order by stock (low to high) then by name
    products = products.order_by('stock', 'name')
    
    # Get categories for filter dropdown
    categories = dict(Product.CATEGORY_CHOICES)
    
    return render(request, 'store/stock_management.html', {
        'title': 'Stock Management',
        'products': products,
        'categories': categories,
        'current_category': category,
        'current_stock_status': stock_status,
        'search_query': search,
    })

@staff_member_required
def update_stock(request, product_id):
    """Update stock for a single product"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        try:
            new_stock = int(request.POST.get('stock', 0))
            if new_stock >= 0:
                old_stock = product.stock
                product.stock = new_stock
                product.save()
                
                change = new_stock - old_stock
                if change > 0:
                    messages.success(request, f"Added {change} to {product.name} stock (now {new_stock})")
                elif change < 0:
                    messages.success(request, f"Removed {abs(change)} from {product.name} stock (now {new_stock})")
                else:
                    messages.info(request, f"Stock for {product.name} unchanged (still {new_stock})")
            else:
                messages.error(request, "Stock amount must be a non-negative number")
        except ValueError:
            messages.error(request, "Invalid stock value provided")
            
    # Redirect to referer or stock management page
    referer = request.META.get('HTTP_REFERER')
    if referer and 'stock' in referer:
        return redirect(referer)
    return redirect('store:stock_management')

@staff_member_required
def update_stock_bulk(request):
    """Handle bulk stock updates from the stock management form"""
    if request.method == 'POST':
        products_updated = 0
        
        # Process all form fields
        for key, value in request.POST.items():
            # Check if this is a stock update field (format: stock_X where X is product ID)
            if key.startswith('stock_'):
                try:
                    # Extract product ID from field name
                    product_id = int(key.replace('stock_', ''))
                    new_stock = int(value)
                    
                    if new_stock < 0:
                        continue  # Skip negative values
                        
                    # Find and update product
                    product = Product.objects.get(id=product_id)
                    
                    # Only update if stock value actually changed
                    if product.stock != new_stock:
                        product.stock = new_stock
                        product.save()
                        products_updated += 1
                        
                except (ValueError, Product.DoesNotExist):
                    # Skip any fields with invalid format or non-existent products
                    continue
        
        if products_updated > 0:
            messages.success(request, f"Successfully updated stock for {products_updated} product(s).")
        else:
            messages.info(request, "No stock levels were changed.")
            
        # Redirect to referer or stock management page
        referer = request.META.get('HTTP_REFERER')
        if referer and 'stock' in referer:
            return redirect(referer)
    
    return redirect('store:stock_management')

@staff_member_required
def order_management(request):
    """
    Admin view for managing orders
    """
    # Extract filters from request
    status = request.GET.get('status')
    search = request.GET.get('search', '')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Start with all orders
    orders = Order.objects.all()
    
    # Apply filters if provided
    if status:
        orders = orders.filter(status=status)
    
    if search:
        orders = orders.filter(
            Q(email__icontains=search) | 
            Q(shipping_name__icontains=search) |
            Q(order_reference__icontains=search) |
            Q(id__icontains=search)
        )
    
    if start_date:
        try:
            start = timezone.datetime.strptime(start_date, '%Y-%m-%d')
            orders = orders.filter(created_at__gte=start)
        except ValueError:
            pass
    
    if end_date:
        try:
            end = timezone.datetime.strptime(end_date, '%Y-%m-%d')
            end = end.replace(hour=23, minute=59, second=59)
            orders = orders.filter(created_at__lte=end)
        except ValueError:
            pass
            
    # Order by most recent first
    orders = orders.order_by('-created_at')
    
    # Setup pagination
    orders_page = paginate_queryset(request, orders, per_page=20)
    
    return render(request, 'store/order_management.html', {
        'title': 'Order Management',
        'orders': orders_page,
        'status_choices': Order.STATUS_CHOICES,
        'current_status': status,
        'search_query': search,
        'start_date': start_date,
        'end_date': end_date,
    })

@staff_member_required
def update_order_status(request, order_id):
    """
    Update the status of an order
    """
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        tracking = request.POST.get('tracking_number')
        notes = request.POST.get('notes')
        
        # Update status if valid
        if new_status and new_status in dict(Order.STATUS_CHOICES):
            old_status = order.get_status_display()
            order.status = new_status
            
            # Update tracking number if provided
            if tracking:
                order.tracking_number = tracking
            
            # Update notes if provided
            if notes:
                order.notes = notes
            
            order.save()
            messages.success(
                request, 
                f"Order #{order.id} status updated from {old_status} to {order.get_status_display()}."
            )
        else:
            messages.error(request, "Invalid status provided.")
    
    # Redirect to referer or order management
    referer = request.META.get('HTTP_REFERER')
    if referer and 'order' in referer:
        return redirect(referer)
        
    return redirect('store:order_management')

###################
# Product Management
###################

@staff_member_required
def add_product(request):
    """
    Add a new product to the store
    """
    if request.method == 'POST':
        # Extract form data
        name = request.POST.get('name')
        category = request.POST.get('category')
        price = request.POST.get('price')
        description = request.POST.get('description')
        stock = request.POST.get('stock', 0)
        image = request.FILES.get('image')
        meta_description = request.POST.get('meta_description', '')
        featured = request.POST.get('featured') == 'on'
        
        # Basic validation
        if not all([name, category, price]):
            messages.error(request, "Name, category, and price are required fields.")
            categories = Product.CATEGORY_CHOICES  # Changed this line - pass the tuple directly
            return render(request, 'store/add_product.html', {
                'title': 'Add Product',
                'categories': categories
            })
        
        try:
            # Create new product
            product = Product(
                name=name,
                category=category,
                price=Decimal(price),
                description=description or '',
                meta_description=meta_description,
                stock=int(stock) if stock else 0,
                featured=featured,
                image=image,
                created_at=timezone.now()
            )
            product.save()
            
            messages.success(request, f"Product '{name}' added successfully!")
            return redirect('store:edit_product', product_id=product.id)
            
        except Exception as e:
            logger.error(f"Error adding product: {str(e)}")
            messages.error(request, f"Error adding product: {str(e)}")
    
    # For GET requests, show the form
    categories = Product.CATEGORY_CHOICES  # Changed this line - pass the tuple directly
    return render(request, 'store/add_product.html', {
        'title': 'Add Product',
        'categories': categories
    })

@staff_member_required
def edit_product(request, product_id):
    """
    Edit an existing product
    """
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        try:
            # Extract form data
            product.name = request.POST.get('name')
            product.category = request.POST.get('category')
            product.price = Decimal(request.POST.get('price'))
            product.description = request.POST.get('description', '')
            product.meta_description = request.POST.get('meta_description', '')
            product.stock = int(request.POST.get('stock', 0))
            product.featured = request.POST.get('featured') == 'on'
            product.available = request.POST.get('available') == 'on'
            
            # Handle image update if provided
            if 'image' in request.FILES:
                product.image = request.FILES['image']
            
            # Handle size if defined in model
            if hasattr(Product, 'SIZE_CHOICES'):
                product.size = request.POST.get('size', '')
                
            product.save()
            messages.success(request, f"Product '{product.name}' updated successfully!")
            
        except Exception as e:
            logger.error(f"Error updating product: {str(e)}")
            messages.error(request, f"Error updating product: {str(e)}")
    
    categories = Product.CATEGORY_CHOICES  # Changed from dict(Product.CATEGORY_CHOICES)
    sizes = Product.SIZE_CHOICES if hasattr(Product, 'SIZE_CHOICES') else None
    
    return render(request, 'store/edit_product.html', {
        'title': f'Edit Product: {product.name}',
        'product': product,
        'categories': categories,
        'sizes': sizes,
    })

@staff_member_required
def delete_product(request, product_id):
    """
    Delete a product
    """
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        # Check if product has been ordered
        ordered = OrderItem.objects.filter(product=product).exists()
        
        if ordered and request.POST.get('action') != 'force_delete':
            # If product has been ordered, show warning first
            return render(request, 'store/delete_product.html', {
                'product': product,
                'title': f'Delete Product: {product.name}',
                'ordered': True,
            })
        
        try:
            product_name = product.name
            product.delete()
            messages.success(request, f"Product '{product_name}' has been deleted.")
            return redirect('store:stock_management')
            
        except Exception as e:
            logger.error(f"Error deleting product: {str(e)}")
            messages.error(request, f"Error deleting product: {str(e)}")
            return redirect('store:edit_product', product_id=product.id)
    
    # For GET requests, show confirmation page
    return render(request, 'store/delete_product.html', {
        'product': product,
        'title': f'Delete Product: {product.name}',
    })

# Add this function to your views.py file
def about_us(request):
    """Display information about the company"""
    return render(request, 'store/about_us.html')

# Also add a simple contact view since we linked to it
def contact(request):
    """Display contact form and information"""
    # Simple version for now
    return render(request, 'store/contact.html')

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('store:login')
    else:
        form = UserCreationForm()
    return render(request, 'store/sign_up.html', {'form': form})

@login_required
def profile(request):
    return render(request, 'store/profile.html')