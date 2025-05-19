"""
Somerset Shrimp Shack - Store Views
This file contains all view functions for the store application.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum, F, Q, Count, Min, Max
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.forms import UserCreationForm
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required

from .models import Product, Order, OrderItem, Category
from .cart import Cart
from .forms import CheckoutForm, ProductForm, ContactForm

from decimal import Decimal, InvalidOperation
import uuid
import stripe
import json
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Set up Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY

# Constants
SHIPPING_COST = Decimal('4.99')

###################
# Helper Functions
###################

def is_staff(user):
    """Check if user is staff"""
    return user.is_staff

def paginate_queryset(request, queryset, per_page=12):
    """Helper function to paginate querysets with error handling"""
    paginator = Paginator(queryset, per_page)
    page = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        page_obj = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page
        page_obj = paginator.page(paginator.num_pages)
    
    return page_obj

###################
# Public Views
###################

def home(request):
    """Display the homepage with featured products"""
    # Get featured products that are available
    featured_products = Product.objects.filter(
        featured=True, 
        available=True
    ).order_by('?')[:4]
    
    # Get newest products
    new_arrivals = Product.objects.filter(
        available=True
    ).order_by('-created_at')[:8]
    
    # Get categories for the nav
    categories = {category.id: category.name for category in Category.objects.all()}
    
    return render(request, 'store/home.html', {
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'categories': categories,
    })

def product_list(request):
    """Display list of all available products with filters and sorting"""
    # Extract filters from request
    category_id = request.GET.get('category')
    sort = request.GET.get('sort', 'name')  # Default sort by name
    search = request.GET.get('search', '')
    in_stock = request.GET.get('in_stock')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    # Start with all products that are available
    products = Product.objects.filter(available=True)
    
    # Apply filters if provided
    if category_id:
        try:
            category_id = int(category_id)
            products = products.filter(category_id=category_id)
        except (ValueError, TypeError):
            pass
        
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search)
        )
    
    if in_stock == "1":
        products = products.filter(stock__gt=0)
    
    # Price range filtering
    if min_price:
        try:
            products = products.filter(price__gte=Decimal(min_price))
        except (ValueError, TypeError, InvalidOperation):
            pass
            
    if max_price:
        try:
            products = products.filter(price__lte=Decimal(max_price))
        except (ValueError, TypeError, InvalidOperation):
            pass
    
    # Apply sorting
    if sort == 'price-asc':
        products = products.order_by('price')
    elif sort == 'price-desc':
        products = products.order_by('-price')
    elif sort == 'newest':
        products = products.order_by('-created')  # Assuming the field is 'created' not 'created_at'
    else:  # Default to name
        products = products.order_by('name')
    
    # Setup pagination
    products_page = paginate_queryset(request, products)
    
    # Get all categories with their product counts
    category_counts = Category.objects.annotate(
        count=Count('products', filter=Q(products__available=True))
    ).values('id', 'name', 'count')
    
    # Get all categories for the filter dropdown
    categories = {cat.id: cat.name for cat in Category.objects.all()}
    
    # Get min and max prices for price range filter
    price_range = Product.objects.filter(available=True).aggregate(
        min_price=Min('price'),
        max_price=Max('price')
    )
    
    return render(request, 'store/product_list.html', {
        'products': products_page,
        'categories': categories,
        'category_counts': category_counts,
        'current_category': category_id,
        'current_sort': sort,
        'search_query': search,
        'in_stock_only': in_stock == "1",
        'price_range': price_range,
    })

def product_detail(request, slug):
    """Show detailed information about a product"""
    product = get_object_or_404(Product, slug=slug, available=True)
    
    # Load related products in same category
    related_products = Product.objects.filter(
        category=product.category, 
        available=True
    ).exclude(id=product.id).order_by('?')[:4]
    
    # Check if product is in cart already
    cart = Cart(request)
    in_cart = cart.is_in_cart(product)
    
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'sizes': Product.SIZE_CHOICES if hasattr(Product, 'SIZE_CHOICES') else None,
        'in_cart': in_cart,
    })

def category_detail(request, slug):
    """Display all products in a specific category"""
    # Find the category by slug or 404
    category = get_object_or_404(Category, slug=slug)
    
    # Get all available products in this category
    products = Product.objects.filter(
        category=category.name,  # Use the category name as stored in Product
        available=True
    ).order_by('name')
    
    # Paginate the results
    products_page = paginate_queryset(request, products)
    
    return render(request, 'store/category_detail.html', {
        'category': category,
        'products': products_page,
    })

def care_guides(request):
    """Display care guides for shrimp and fish"""
    guides = [
        {
            'title': 'Neocaridina Shrimp Care Guide',
            'content': 'Basic care instructions for Neocaridina shrimp...',
            'image': 'neocaridina.jpg',
            'slug': 'neocaridina-care'
        },
        {
            'title': 'Caridina Shrimp Care Guide',
            'content': 'Basic care instructions for Caridina shrimp...',
            'image': 'caridina.jpg', 
            'slug': 'caridina-care'
        },
        # More guides can be added here
    ]
    
    return render(request, 'store/care_guides.html', {
        'guides': guides,
        'title': 'Shrimp Care Guides',
    })

def guide_detail(request, slug):
    """Display a specific care guide"""
    # In a real application, you'd fetch this from a database
    guides = {
        'neocaridina-care': {
            'title': 'Neocaridina Shrimp Care Guide',
            'content': '...',
            'image': 'neocaridina.jpg',
        },
        'caridina-care': {
            'title': 'Caridina Shrimp Care Guide',
            'content': '...',
            'image': 'caridina.jpg',
        },
    }
    
    # Get the guide or 404
    guide = guides.get(slug)
    if not guide:
        raise Http404("Care guide not found")
    
    return render(request, 'store/guide_detail.html', {
        'guide': guide,
        'title': guide['title'],
    })

def about_us(request):
    """Display information about the company"""
    team_members = [
        {
            'name': 'John Smith',
            'title': 'Founder & Shrimp Expert',
            'bio': 'John has been keeping shrimp for over 10 years...',
            'image': 'john.jpg',
        },
        # More team members can be added here
    ]
    
    return render(request, 'store/about_us.html', {
        'team': team_members,
        'title': 'About Somerset Shrimp Shack',
    })

def contact(request):
    """Handle contact form submission and display contact information"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Process the form data
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            
            # In a real application, you'd send an email here
            # send_contact_email(name, email, subject, message)
            
            messages.success(request, "Thank you for your message! We'll get back to you soon.")
            return redirect('store:contact')
    else:
        # Initialize the form for GET requests
        form = ContactForm()
    
    # Company contact information
    contact_info = {
        'email': 'info@somersetshrimpsack.co.uk',
        'phone': '+44 123 456 7890',
        'address': '123 Somerset Road, Taunton, Somerset, UK',
        'business_hours': 'Monday-Friday: 9am-5pm, Saturday: 10am-4pm',
    }
    
    return render(request, 'store/contact.html', {
        'form': form,
        'contact_info': contact_info,
        'title': 'Contact Us',
    })

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
    shipping_cost = SHIPPING_COST if total_price > 0 else Decimal('0')
    grand_total = total_price + shipping_cost if total_price > 0 else Decimal('0')
    
    # Check stock status for all items
    stock_warnings = []
    for item in cart_items:
        product = item.product
        if item.quantity > product.stock:
            stock_warnings.append({
                'product': product,
                'requested': item.quantity,
                'available': product.stock
            })
    
    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'shipping_cost': shipping_cost,
        'grand_total': grand_total,
        'item_count': cart.get_item_count(),
        'stock_warnings': stock_warnings,
    })

@require_http_methods(["POST", "GET"])
def add_to_cart(request, product_id):
    """Add a product to the shopping cart"""
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    
    # Check if product is in stock and available
    if not product.is_in_stock:
        messages.error(request, f"Sorry, {product.name} is out of stock.")
        return redirect('store:product_detail', slug=product.slug)
    
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
    return redirect('store:product_detail', slug=product.slug)

@require_POST
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
    
    # Check if we should return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success', 
            'cart_total': cart.get_total_price(),
            'item_count': cart.get_item_count()
        })
    
    return redirect('store:cart_view')

@require_POST
def update_cart(request, product_id):
    """Update quantity of a product in the cart"""
    cart = Cart(request)
    
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
        
    # Check if we should return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success', 
            'cart_total': cart.get_total_price(),
            'item_count': cart.get_item_count()
        })

    # Redirect to referring page if available, otherwise to cart view
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect("store:cart_view")

@require_POST
def clear_cart(request):
    """Remove all items from the cart"""
    cart = Cart(request)
    cart.clear()
    messages.success(request, "Your cart has been cleared.")
    
    # Check if we should return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'item_count': 0})
        
    return redirect("store:cart_view")

###################
# Checkout Views
###################

def checkout_cart(request):
    """Process checkout for entire cart"""
    cart = Cart(request)
    cart_items = cart.get_cart_items()
    
    # Check if cart is empty
    if not cart_items:
        messages.warning(request, "Your cart is empty.")
        return redirect("store:cart_view")
        
    # Calculate totals
    total = cart.get_total_price()
    shipping_cost = SHIPPING_COST
    grand_total = total + shipping_cost
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        
        if form.is_valid():
            # Get customer data
            email = form.cleaned_data['email']
            
            # Stock validation for all items
            out_of_stock_items = []
            for item in cart_items:
                if item.quantity > item.product.stock:
                    out_of_stock_items.append({
                        'name': item.product.name,
                        'requested': item.quantity,
                        'available': item.product.stock
                    })
            
            # If any items are out of stock, show error and redirect back
            if out_of_stock_items:
                for item in out_of_stock_items:
                    messages.warning(
                        request, 
                        f"Only {item['available']} of {item['name']} available. "
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
                    success_url=request.build_absolute_uri(reverse('store:payment_success')),
                    cancel_url=request.build_absolute_uri(reverse('store:payment_cancel')),
                    shipping_address_collection={
                        'allowed_countries': ['GB'],  # UK only for now
                    },
                    metadata=metadata
                )
                
                # Generate unique order reference
                order_reference = f"SSS-{uuid.uuid4().hex[:8].upper()}"
                
                # Create preliminary order
                order = Order.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    email=email,
                    order_reference=order_reference,
                    stripe_checkout_id=session.id,
                    status='pending',
                    total_amount=grand_total,
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
    else:
        # For GET request, initialize the form
        initial_data = {}
        if request.user.is_authenticated:
            initial_data['email'] = request.user.email
        
        form = CheckoutForm(initial=initial_data)
    
    # GET request - show checkout form
    return render(request, "store/checkout.html", {
        "cart_items": cart_items,
        "form": form,
        "total": total,
        "shipping_cost": shipping_cost,
        "grand_total": grand_total,
        "title": "Checkout",
    })

def payment_success(request):
    """Handle successful payment"""
    cart = Cart(request)
    cart.clear()  # Clear the cart after successful payment
    
    # If user is authenticated, try to get their most recent order
    recent_order = None
    if request.user.is_authenticated:
        try:
            recent_order = Order.objects.filter(
                user=request.user, 
                status='paid'
            ).latest('created_at')
        except Order.DoesNotExist:
            pass
    
    return render(request, "store/payment_success.html", {
        'title': 'Payment Successful',
        'order': recent_order
    })

def payment_cancel(request):
    """Handle cancelled payment"""
    return render(request, "store/payment_cancel.html", {
        'title': 'Payment Cancelled'
    })

###################
# Webhook Handlers
###################

@csrf_exempt
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
    
    # Paginate the results
    page_obj = paginate_queryset(request, orders, per_page=10)
    
    return render(request, 'store/order_history.html', {
        'orders': page_obj,
        'title': 'Your Order History',
    })

@login_required
def order_detail(request, order_reference):
    """
    Display detailed information about a specific order
    """
    # If user is logged in, ensure they can only view their own orders
    # Staff users can view any order
    if request.user.is_authenticated and not request.user.is_staff:
        order = get_object_or_404(Order, order_reference=order_reference, user=request.user)
    elif request.user.is_staff:
        order = get_object_or_404(Order, order_reference=order_reference)
    else:
        # Should not happen with @login_required, but just in case
        return redirect(f"{settings.LOGIN_URL}?next={request.path}")
    
    # Get all items for this order
    order_items = order.items.all()
    
    return render(request, 'store/order_detail.html', {
        'order': order,
        'order_items': order_items,
        'title': f'Order #{order.order_reference}',
    })

###################
# User Account Views
###################

def signup(request):
    """Handle user registration"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('store:login')
    else:
        form = UserCreationForm()
    
    return render(request, 'store/sign_up.html', {
        'form': form,
        'title': 'Create an Account'
    })

@login_required
def profile(request):
    """Display and manage user profile"""
    # Get user's recent orders
    recent_orders = Order.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]
    
    # Get saved addresses (if you implement this feature)
    saved_addresses = []  # In a real app, fetch from a UserAddress model
    
    return render(request, 'store/profile.html', {
        'user': request.user,
        'recent_orders': recent_orders,
        'saved_addresses': saved_addresses,
        'title': 'Your Profile'
    })

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
    # Using the correct field name for category
    low_stock_products = Product.objects.filter(stock__lt=10).values('id', 'name', 'category', 'stock', 'slug')
    
    # Calculate total revenue
    total_revenue = Order.objects.filter(status='paid').aggregate(
        total=Sum(F('total_amount'))
    )['total'] or Decimal('0')
    
    # Get monthly order counts
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    monthly_orders = []
    monthly_revenue = []
    
    for i in range(6):  # Past 6 months
        month = (current_month - i) % 12 or 12  # Handle December (0)
        year = current_year if month <= current_month else current_year - 1
        
        month_start = timezone.datetime(year, month, 1)
        if month == 12:
            next_month_start = timezone.datetime(year + 1, 1, 1)
        else:
            next_month_start = timezone.datetime(year, month + 1, 1)
        
        # Orders this month
        month_orders = Order.objects.filter(
            created_at__gte=month_start,
            created_at__lt=next_month_start,
            status='paid'
        )
        
        count = month_orders.count()
        revenue = month_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        
        month_name = timezone.datetime(year, month, 1).strftime('%b %Y')
        monthly_orders.append({'month': month_name, 'count': count})
        monthly_revenue.append({'month': month_name, 'amount': float(revenue)})
    
    # Reverse to show oldest to newest
    monthly_orders.reverse()
    monthly_revenue.reverse()
    
    return render(request, 'store/dashboard.html', {
        'title': 'Admin Dashboard',
        'products_count': products_count,
        'orders_count': orders_count,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'low_stock_products': low_stock_products,
        'monthly_orders': monthly_orders,
        'monthly_revenue': monthly_revenue,
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
        elif stock_status == 'unavailable':
            products = products.filter(available=False)
    
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(id__icontains=search)
        )
    
    # Order by stock (low to high) then by name
    products = products.order_by('stock', 'name')
    
    # Setup pagination
    page_obj = paginate_queryset(request, products, per_page=20)
    
    # Get categories for filter dropdown
    categories = {cat.id: cat.name for cat in Category.objects.all()}
    
    return render(request, 'store/stock_management.html', {
        'title': 'Stock Management',
        'products': page_obj,
        'categories': categories,
        'current_category': category,
        'current_stock_status': stock_status,
        'search_query': search,
    })

@staff_member_required
@require_POST
def update_stock(request, product_id):
    """Update stock for a single product"""
    product = get_object_or_404(Product, id=product_id)
    
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
        
    # Check if we should return JSON for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'stock': product.stock,
            'status': product.stock_status
        })
            
    # Redirect to referer or stock management page
    referer = request.META.get('HTTP_REFERER')
    if referer and 'stock' in referer:
        return redirect(referer)
    return redirect('store:stock_management')

@staff_member_required
@require_POST
def update_stock_bulk(request):
    """Handle bulk stock updates from the stock management form"""
    products_updated = 0
    results = []
    
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
                    old_stock = product.stock
                    product.stock = new_stock
                    product.save()
                    products_updated += 1
                    
                    # Add to results for AJAX response
                    results.append({
                        'id': product.id,
                        'stock': product.stock,
                        'change': new_stock - old_stock,
                        'status': product.stock_status
                    })
                    
            except (ValueError, Product.DoesNotExist):
                # Skip any fields with invalid format or non-existent products
                continue
    
    # Check if we should return JSON for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'updated': products_updated,
            'results': results
        })
        
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
    page_obj = paginate_queryset(request, orders, per_page=20)
    
    # Summary stats for current filter
    order_count = orders.count()
    total_revenue = orders.filter(status='paid').aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0')
    
    return render(request, 'store/order_management.html', {
        'title': 'Order Management',
        'orders': page_obj,
        'order_count': order_count,
        'total_revenue': total_revenue,
        'status_choices': Order.STATUS_CHOICES,
        'current_status': status,
        'search_query': search,
        'start_date': start_date,
        'end_date': end_date,
    })

@staff_member_required
@require_POST
def update_order_status(request, order_id):
    """
    Update the status of an order
    """
    order = get_object_or_404(Order, id=order_id)
    
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
            f"Order #{order.order_reference} status updated from {old_status} to {order.get_status_display()}."
        )
    else:
        messages.error(request, "Invalid status provided.")
    
    # Check if we should return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'status': order.get_status_display()
        })
    
    # Redirect to referer or order management
    referer = request.META.get('HTTP_REFERER')
    if referer and 'order' in referer:
        return redirect(referer)
        
    return redirect('store:order_management')

###################
# Product Management
###################

@staff_member_required
def product_management(request):
    """List all products with management options"""
    # Extract filters
    category = request.GET.get('category')
    availability = request.GET.get('availability')
    search = request.GET.get('search', '')
    
    # Start with all products
    products = Product.objects.all()
    
    # Apply filters
    if category:
        products = products.filter(category=category)
        
    if availability:
        if availability == 'available':
            products = products.filter(available=True)
        elif availability == 'unavailable':
            products = products.filter(available=False)
            
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search)
        )
    
    # Order by name
    products = products.order_by('name')
    
    # Set up pagination
    page_obj = paginate_queryset(request, products, per_page=20)
    
    # Get categories for filter
    categories = {cat.id: cat.name for cat in Category.objects.all()}
    
    return render(request, 'store/product_management.html', {
        'title': 'Product Management',
        'products': page_obj,
        'categories': categories,
        'current_category': category,
        'current_availability': availability,
        'search_query': search,
    })

@staff_member_required
def add_product(request):
    """Add a new product"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            # Ensure the slug is set
            if not product.slug:
                from django.utils.text import slugify
                product.slug = slugify(product.name)
            product.save()
            
            messages.success(request, f"Product '{product.name}' was successfully added.")
            return redirect('store:product_management')
    else:
        form = ProductForm()
    
    return render(request, 'store/product_form.html', {
        'form': form,
        'title': 'Add New Product',
        'submit_text': 'Add Product',
    })

@staff_member_required
def edit_product(request, product_id):
    """
    Edit an existing product
    """
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"Product '{product.name}' updated successfully!")
            return redirect('store:product_management')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'store/product_form.html', {
        'form': form,
        'product': product,
        'title': f'Edit Product: {product.name}',
        'submit_text': 'Update Product',
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
            return redirect('store:product_management')
            
        except Exception as e:
            logger.error(f"Error deleting product: {str(e)}")
            messages.error(request, f"Error deleting product: {str(e)}")
            return redirect('store:edit_product', product_id=product.id)
    
    # For GET requests, show confirmation page
    return render(request, 'store/delete_product.html', {
        'product': product,
        'title': f'Delete Product: {product.name}',
    })

@staff_member_required
def toggle_product_availability(request, product_id):
    """Toggle a product's availability status"""
    product = get_object_or_404(Product, id=product_id)
    product.available = not product.available
    product.save()
    
    status = "available" if product.available else "unavailable"
    messages.success(request, f"Product '{product.name}' is now {status}.")
    
    # Check if we should return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'available': product.available,
            'product_id': product.id
        })
        
    # Redirect back to product management
    return redirect('store:product_management')

def checkout(request, product_id=None):
    """Redirects to the appropriate checkout view"""
    if product_id:
        # If specific product checkout is needed, implement that logic here
        messages.info(request, 'Direct product checkout not implemented')
        return redirect('store:product_detail', slug=get_object_or_404(Product, id=product_id).slug)
    else:
        # For cart checkout, use the existing checkout_cart view
        return checkout_cart(request)

def order_summary(request):
    """Display order summary before checkout"""
    # Implementation will go here
    return redirect('store:checkout_cart')
