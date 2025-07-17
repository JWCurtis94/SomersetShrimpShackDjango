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
from django.views.decorators.cache import cache_page
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.db import transaction

from .models import Product, Order, OrderItem, Category
from .cart import Cart
from .forms import CheckoutForm, ProductForm, ContactForm, CategoryForm
from .utils import send_order_confirmation_email, send_order_notification_email

from decimal import Decimal, InvalidOperation
import uuid
import stripe
import json
import logging
import os

# Configure logger
logger = logging.getLogger(__name__)

# Set up Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY

# Constants
SHIPPING_COST = Decimal('6')

###################
# Helper Functions
###################

def is_staff(user):
    """Check if user is staff"""
    return user.is_staff

def validate_stock_quantity(quantity, max_stock=None):
    """Validate stock quantity input"""
    try:
        quantity = int(quantity)
        if quantity < 0:
            return None, "Quantity cannot be negative"
        if quantity > 9999:
            return None, "Quantity cannot exceed 9999"
        if max_stock is not None and quantity > max_stock:
            return max_stock, f"Only {max_stock} items available"
        return quantity, None
    except (ValueError, TypeError):
        return None, "Invalid quantity format"

def paginate_queryset(request, queryset, per_page=12):
    """Helper function to paginate querysets with error handling"""
    # Validate per_page parameter
    per_page = max(1, min(per_page, 100))  # Limit between 1 and 100
    
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

def ensure_media_directories():
    """Ensure that media directories exist for file uploads"""
    import os
    from django.conf import settings
    
    if hasattr(settings, 'MEDIA_ROOT') and settings.MEDIA_ROOT:
        # Create media directories if they don't exist
        media_dirs = [
            os.path.join(settings.MEDIA_ROOT, 'categories'),
            os.path.join(settings.MEDIA_ROOT, 'products'),
        ]
        
        for dir_path in media_dirs:
            if not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path, exist_ok=True)
                    logger.info(f"Created media directory: {dir_path}")
                except Exception as e:
                    logger.error(f"Error creating media directory {dir_path}: {str(e)}")

###################
# Public Views
###################

@cache_page(60 * 15)  # Cache for 15 minutes
def home(request):
    """Display the homepage with featured products"""
    # Get featured products that are available
    featured_products = Product.objects.filter(
        featured=True, 
        available=True
    ).select_related('category').order_by('?')[:4]
    
    # Get newest products
    new_arrivals = Product.objects.filter(
        available=True
    ).select_related('category').order_by('-created_at')[:8]
    
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
    category_filter = request.GET.get('category')
    sort = request.GET.get('sort', 'name')  # Default sort by name
    search = request.GET.get('search', '').strip()
    in_stock = request.GET.get('in_stock')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    # Start with all products that are available, using select_related for performance
    products = Product.objects.filter(available=True).select_related('category')
    
    # Apply filters if provided
    if category_filter:
        # Try to filter by category slug or name
        products = products.filter(
            Q(category__slug=category_filter) | Q(category__name__iexact=category_filter)
        )
        
    if search:
        # Limit search query length for security
        search = search[:100]
        products = products.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search)
        )
    
    if in_stock == "1":
        products = products.filter(stock__gt=0)
    
    # Price range filtering with better validation
    if min_price:
        try:
            min_price_decimal = Decimal(min_price)
            if min_price_decimal >= 0:
                products = products.filter(price__gte=min_price_decimal)
        except (ValueError, TypeError, InvalidOperation):
            logger.warning(f"Invalid min_price provided: {min_price}")
            
    if max_price:
        try:
            max_price_decimal = Decimal(max_price)
            if max_price_decimal >= 0:
                products = products.filter(price__lte=max_price_decimal)
        except (ValueError, TypeError, InvalidOperation):
            logger.warning(f"Invalid max_price provided: {max_price}")
    
    # Apply sorting with validation
    valid_sorts = ['name', 'price-asc', 'price-desc', 'newest']
    if sort not in valid_sorts:
        sort = 'name'
        
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
    
    # Organize products by category for template display
    categorized_products = {}
    for product in products_page:
        category_name = product.category.name
        if category_name not in categorized_products:
            categorized_products[category_name] = []
        categorized_products[category_name].append(product)
    
    # Get all categories with their product counts
    category_counts = Category.objects.annotate(
        count=Count('products', filter=Q(products__available=True))
    ).values('id', 'name', 'count')
    
    # Get all categories for display and filtering
    all_categories = Category.objects.all().order_by('name')
    categories_for_filter = {cat.name: cat.name for cat in all_categories}
    
    # Get min and max prices for price range filter
    price_range = Product.objects.filter(available=True).aggregate(
        min_price=Min('price'),
        max_price=Max('price')
    )
    
    # Get total products count for hero stats
    total_products = Product.objects.filter(available=True).count()
    
    return render(request, 'store/product_list.html', {
        'products': products_page,
        'categorized_products': categorized_products,
        'categories': categories_for_filter,
        'all_categories': all_categories,
        'category_counts': category_counts,
        'current_category': category_filter,
        'current_sort': sort,
        'search_query': search,
        'in_stock_only': in_stock == "1",
        'price_range': price_range,
        'total_products': total_products,
        'sort': sort,  # Add sort for template
    })

def product_detail(request, slug):
    """Display detailed product information"""
    product = get_object_or_404(Product, slug=slug)
    
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
    
    # Get all available products in this category - FIX: use category object directly
    products = Product.objects.filter(
        category=category,  # Changed from category.name to category
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

from django.core.mail import send_mail
from django.conf import settings

def contact(request):
    """Handle contact form submission and send email"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']

            # ✅ Send email to site owner
            send_mail(
                subject=f"New Contact Form Message: {subject}",
                message=f"From: {name} <{email}>\n\n{message}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
                fail_silently=False,
            )

            messages.success(request, "Thank you for your message! We'll get back to you soon.")
            return redirect('store:contact')
    else:
        form = ContactForm()

    return render(request, 'store/contact.html', {
        'form': form,
        'title': 'Contact Us',
    })

###################
# Cart Views
###################

def cart_view(request):
    """Show current cart contents"""
    cart = Cart(request)
    cart_items = cart.get_cart_items()
    # Debug statements removed for production
    logger.debug(f"Cart view called, cart items: {len(cart_items)}")
    
    # Calculate cart totals
    total_price = cart.get_total_price()
    
    # Use new shipping cost calculation method
    shipping_cost = cart.get_shipping_cost()
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
    logger.debug(f"Add to cart called with product_id={product_id}, method={request.method}")
    
    # Rate limiting: limit to 10 add-to-cart actions per minute per IP
    client_ip = request.META.get('REMOTE_ADDR', '')
    cache_key = f"add_to_cart_{client_ip}"
    current_requests = cache.get(cache_key, 0)
    
    if current_requests >= 10:
        messages.error(request, "Too many requests. Please try again in a minute.")
        return redirect('store:product_list')
    
    cache.set(cache_key, current_requests + 1, 60)  # Reset every minute
    try:
        product = get_object_or_404(Product, id=product_id)
    except (ValueError, TypeError):
        logger.warning(f"Invalid product_id provided: {product_id}")
        messages.error(request, "Invalid product.")
        return redirect('store:products')
        
    cart = Cart(request)
    logger.debug(f"Found product: {product.name}, cart items before: {len(cart.get_cart_items())}")
    
    # Check if product is in stock and available
    if not product.is_in_stock:
        messages.error(request, f"Sorry, {product.name} is out of stock.")
        return redirect('store:product_detail', slug=product.slug)
    
    # Process form data if POST request
    if request.method == 'POST':
        # Extract quantity from form with validation
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity <= 0 or quantity > 999:  # Add upper limit
                raise ValueError("Invalid quantity")
        except ValueError:
            messages.error(request, "Please enter a valid quantity.")
            return redirect('store:product_detail', slug=product.slug)
            
        # Extract size if provided
        size = request.POST.get('size')
        if size and len(size) > 20:  # Validate size input length
            size = size[:20]
        
        # Check against available stock
        if quantity > product.stock:
            messages.warning(request, f"Only {product.stock} items available. Adding maximum quantity.")
            quantity = product.stock
        
        # Add to cart
        cart.add(product, quantity=quantity, size=size)
        logger.debug(f"Added to cart. Cart items after: {len(cart.get_cart_items())}")
        
        product_name = product.name
        if size:
            product_name = f"{product_name} ({size})"
            
        messages.success(request, f"Added {quantity}x {product_name} to your cart.")
        logger.debug("Success message added")
        
        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': f"Added {quantity}x {product_name} to your cart.",
                'cart_item_count': cart.get_item_count(),
                'cart_total': str(cart.get_total_price())
            })
        
        # For regular requests, redirect based on 'next' parameter or to cart
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
        raw_quantity = request.POST.get('quantity', 1)
        size = request.POST.get('size')
        
        # Get product for stock validation
        product = get_object_or_404(Product, id=product_id)
        
        # Validate quantity using helper function
        new_quantity, error_message = validate_stock_quantity(raw_quantity, product.stock)
        
        if error_message:
            messages.error(request, error_message)
        elif new_quantity != int(raw_quantity):
            messages.warning(request, f"Quantity adjusted to {new_quantity} (maximum available).")
            
        if new_quantity is not None:
            # Update the cart
            if cart.update(product_id, new_quantity, size=size):
                if not error_message and new_quantity == int(raw_quantity):
                    messages.success(request, "Cart updated successfully.")
            else:
                messages.error(request, "Failed to update cart. Item not found.")
        else:
            messages.error(request, "Invalid quantity provided.")
            
    except Exception as e:
        logger.error(f"Error updating cart: {str(e)}")
        messages.error(request, "An error occurred while updating your cart.")
        
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
    shipping_cost = cart.get_shipping_cost()  # Use new dynamic shipping calculation
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
                
                # Create preliminary order and items in a transaction
                with transaction.atomic():
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
            except stripe.error.CardError as e:
                # Since it's a decline, stripe.error.CardError will be caught
                logger.error(f"Card error in cart checkout: {str(e)}")
                messages.error(request, f"Your card was declined: {e.user_message}")
                return redirect("store:cart_view")
            except stripe.error.RateLimitError as e:
                logger.error(f"Rate limit error in cart checkout: {str(e)}")
                messages.error(request, "Too many requests made to the payment provider. Please try again later.")
                return redirect("store:cart_view")
            except stripe.error.InvalidRequestError as e:
                logger.error(f"Invalid request error in cart checkout: {str(e)}")
                messages.error(request, "Invalid payment request. Please try again.")
                return redirect("store:cart_view")
            except stripe.error.AuthenticationError as e:
                logger.error(f"Authentication error in cart checkout: {str(e)}")
                messages.error(request, "Payment service authentication error. Please contact support.")
                return redirect("store:cart_view")
            except stripe.error.APIConnectionError as e:
                logger.error(f"Network error in cart checkout: {str(e)}")
                messages.error(request, "Network communication error. Please check your connection and try again.")
                return redirect("store:cart_view")
            except stripe.error.StripeError as e:
                logger.error(f"General Stripe error in cart checkout: {str(e)}")
                messages.error(request, f"Payment error: {str(e)}")
                return redirect("store:cart_view")
            except Exception as e:
                logger.error(f"Unexpected error in cart checkout: {str(e)}")
                messages.error(request, "An unexpected error occurred during checkout. Please try again.")
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
            
            # Send email notifications
            try:
                # Send confirmation email to customer
                send_order_confirmation_email(order)
                
                # Send notification email to admin
                send_order_notification_email(order)
                
                logger.info(f"Email notifications sent for order #{order.id}")
            except Exception as e:
                logger.error(f"Failed to send email notifications for order #{order.id}: {str(e)}")
            
            # Update product stock levels
            with transaction.atomic():
                for item in order.items.all():
                    product = item.product
                    if product.stock >= item.quantity:
                        product.stock -= item.quantity
                        product.save()
                    else:
                        logger.warning(f"Order #{order.id}: Not enough stock for {product.name}")
                        # Consider what to do here - maybe partial fulfillment or customer notification
            
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
    from django.contrib.auth.models import User
    from datetime import datetime, timedelta
    
    # Get current month and year
    now = timezone.now()
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    
    # Get counts for dashboard stats
    total_products = Product.objects.count()
    
    # Total orders (all time)
    total_orders = Order.objects.count()
    
    # Total orders this month
    orders_this_month = Order.objects.filter(
        created_at__gte=current_month_start
    ).count()
    
    # Total orders last month
    orders_last_month = Order.objects.filter(
        created_at__gte=last_month_start,
        created_at__lt=current_month_start
    ).count()
    
    # Calculate order growth percentage
    if orders_last_month > 0:
        order_growth = ((orders_this_month - orders_last_month) / orders_last_month) * 100
    else:
        order_growth = 100 if orders_this_month > 0 else 0
    
    # Total revenue (from paid orders)
    total_revenue = Order.objects.filter(status='paid').aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0')
    
    # Revenue this month
    revenue_this_month = Order.objects.filter(
        status='paid',
        created_at__gte=current_month_start
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    # Revenue last month
    revenue_last_month = Order.objects.filter(
        status='paid',
        created_at__gte=last_month_start,
        created_at__lt=current_month_start
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    # Calculate revenue growth percentage
    if revenue_last_month > 0:
        revenue_growth = ((revenue_this_month - revenue_last_month) / revenue_last_month) * 100
    else:
        revenue_growth = 100 if revenue_this_month > 0 else 0
    
    # Active customers (customers who have made orders this month)
    active_customers = Order.objects.filter(
        created_at__gte=current_month_start
    ).values('email').distinct().count()
    
    # Active customers last month
    active_customers_last_month = Order.objects.filter(
        created_at__gte=last_month_start,
        created_at__lt=current_month_start
    ).values('email').distinct().count()
    
    # Calculate customer growth percentage
    if active_customers_last_month > 0:
        customer_growth = ((active_customers - active_customers_last_month) / active_customers_last_month) * 100
    else:
        customer_growth = 100 if active_customers > 0 else 0
    
    # Recent orders for display
    recent_orders = Order.objects.select_related().order_by('-created_at')[:5]
    
    # Low stock products (stock < 10)
    low_stock_products = Product.objects.filter(stock__lt=10).select_related('category')
    
    # Products for overview section
    products = Product.objects.select_related('category').order_by('-created_at')[:10]
    
    # Get monthly data for charts (past 6 months)
    monthly_orders = []
    monthly_revenue = []
    
    for i in range(6):  # Past 6 months
        month_date = current_month_start - timedelta(days=30 * i)
        month_start = month_date.replace(day=1)
        
        if month_start.month == 12:
            next_month_start = month_start.replace(year=month_start.year + 1, month=1)
        else:
            next_month_start = month_start.replace(month=month_start.month + 1)
        
        # Orders this month
        month_orders = Order.objects.filter(
            created_at__gte=month_start,
            created_at__lt=next_month_start,
            status='paid'
        )
        
        count = month_orders.count()
        revenue = month_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        
        month_name = month_start.strftime('%b %Y')
        monthly_orders.append({'month': month_name, 'count': count})
        monthly_revenue.append({'month': month_name, 'amount': float(revenue)})
    
    # Reverse to show oldest to newest
    monthly_orders.reverse()
    monthly_revenue.reverse()
    
    return render(request, 'store/dashboard.html', {
        'title': 'Admin Dashboard',
        'total_products': total_products,
        'total_orders': total_orders,
        'orders_this_month': orders_this_month,
        'order_growth': round(order_growth, 1),
        'total_revenue': total_revenue,
        'revenue_this_month': revenue_this_month,
        'revenue_growth': round(revenue_growth, 1),
        'active_customers': active_customers,
        'customer_growth': round(customer_growth, 1),
        'recent_orders': recent_orders,
        'products': products,
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
    category_id = request.GET.get('category')
    stock_status = request.GET.get('stock_status')
    search = request.GET.get('search', '')
    
    # Start with all products
    products = Product.objects.all()
    
    # Apply filters if provided - FIX: use category_id for filtering
    if category_id:
        try:
            category_id = int(category_id)
            products = products.filter(category_id=category_id)
        except (ValueError, TypeError):
            pass
        
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
        'current_category': category_id,
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
        # Limit search query length for security
        search = search.strip()[:100]
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
        if new_status and new_status in [choice[0] for choice in Order.STATUS_CHOICES]:
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
        
        # Always redirect back to order management for dropdown submissions
        return redirect('store:order_management')
    
    # GET request - show the update form
    return render(request, 'store/update_order_status.html', {
        'order': order,
        'status_choices': Order.STATUS_CHOICES,
        'title': f'Update Order #{order.order_reference}',
    })

@staff_member_required
def test_order_update(request, order_id):
    """Test function to debug the order update issue"""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'store/update_order_status.html', {
        'order': order,
        'status_choices': Order.STATUS_CHOICES,
        'title': f'Test Update Order #{order.order_reference}',
    })

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
    # Get categories for the dropdown
    categories = [(cat.id, cat.name) for cat in Category.objects.all().order_by('name')]
    
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
    
    return render(request, 'store/add_product.html', {
        'form': form,
        'title': 'Add New Product',
        'submit_text': 'Add Product',
        'categories': categories,
    })

@staff_member_required
def edit_product(request, product_id):
    """
    Edit an existing product
    """
    product = get_object_or_404(Product, id=product_id)
    # Get categories for the dropdown
    category_choices = [(cat.id, cat.name) for cat in Category.objects.all().order_by('name')]
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"Product '{product.name}' updated successfully!")
            return redirect('store:product_management')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'store/edit_product.html', {
        'form': form,
        'product': product,
        'title': f'Edit Product: {product.name}',
        'submit_text': 'Update Product',
        'category_choices': category_choices,
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

###################
# Category Management Views
###################

@staff_member_required
def category_management(request):
    """
    View for managing categories
    """
    categories = Category.objects.all().order_by('order', 'name')
    
    return render(request, 'store/category_management.html', {
        'title': 'Category Management',
        'categories': categories,
    })

@staff_member_required
def add_category(request):
    """
    View for adding a new category
    """
    # Ensure media directories exist
    ensure_media_directories()
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    category = form.save()
                    messages.success(request, f'Category "{category.name}" created successfully!')
                    return redirect('store:category_management')
            except Exception as e:
                # Handle any database errors
                messages.error(request, f'Error creating category: {str(e)}')
                logger.error(f"Error creating category: {str(e)}", exc_info=True)
        else:
            # Display form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CategoryForm()
    
    return render(request, 'store/add_category.html', {
        'title': 'Add Category',
        'form': form,
    })

@staff_member_required
def edit_category(request, category_id):
    """
    View for editing an existing category
    """
    category = get_object_or_404(Category, id=category_id)
    
    # Ensure media directories exist
    ensure_media_directories()
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            try:
                with transaction.atomic():
                    category = form.save()
                    messages.success(request, f'Category "{category.name}" updated successfully!')
                    return redirect('store:category_management')
            except Exception as e:
                # Handle any database errors
                messages.error(request, f'Error updating category: {str(e)}')
                logger.error(f"Error updating category {category.name}: {str(e)}", exc_info=True)
        else:
            # Display form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'store/edit_category.html', {
        'title': 'Edit Category',
        'category': category,
        'form': form,
    })

@staff_member_required
def delete_category(request, category_id):
    """
    View for deleting a category
    """
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'Category "{category_name}" deleted successfully!')
        return redirect('store:category_management')
    
    return render(request, 'store/delete_category.html', {
        'title': 'Delete Category',
        'category': category,
    })

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

def custom_logout(request):
    """Custom logout view that shows a logout confirmation page"""
    from django.contrib.auth import logout
    
    if request.method == 'POST':
        # Log the user out and redirect
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('store:home')
    
    # For GET requests, show the logout confirmation page
    return render(request, 'store/logout.html', {
        'title': 'Logout'
    })

def debug_session(request):
    """Debug session data"""
    from django.http import JsonResponse
    cart = Cart(request)
    
    debug_info = {
        'session_key': request.session.session_key,
        'session_data': dict(request.session),
        'cart_items_count': len(cart.get_cart_items()),
        'cart_raw': cart.cart,
        'cart_total': str(cart.get_total_price()),
    }
    
    return JsonResponse(debug_info, indent=2)

def test_cart(request):
    """Simple test page for cart functionality"""
    products = Product.objects.filter(is_active=True)[:5]  # Get first 5 products
    return render(request, 'store/test_cart.html', {'products': products})

###################

@staff_member_required
@require_http_methods(["POST"])
def update_category_order(request):
    """
    AJAX view for updating category order
    """
    import json
    from django.http import JsonResponse
    
    try:
        data = json.loads(request.body)
        category_orders = data.get('categories', [])
        
        if not category_orders:
            return JsonResponse({'success': False, 'message': 'No category order data provided'})
        
        logger.info(f"Updating category order for {len(category_orders)} categories")
        
        with transaction.atomic():
            updated_count = 0
            for item in category_orders:
                category_id = item.get('id')
                new_order = item.get('order')
                
                if category_id is None or new_order is None:
                    logger.warning(f"Missing id or order in item: {item}")
                    continue
                
                try:
                    category = Category.objects.get(id=category_id)
                    old_order = category.order
                    category.order = new_order
                    category.save()
                    updated_count += 1
                    logger.info(f"Updated category '{category.name}' order from {old_order} to {new_order}")
                except Category.DoesNotExist:
                    logger.warning(f"Category with id {category_id} does not exist")
                    continue
                except Exception as e:
                    logger.error(f"Error updating category {category_id}: {str(e)}")
                    continue
        
        logger.info(f"Successfully updated order for {updated_count} categories")
        
        return JsonResponse({
            'success': True, 
            'message': f'Successfully updated {updated_count} categories',
            'updated_count': updated_count
        })
    
    except json.JSONDecodeError:
        logger.error("Invalid JSON data received")
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'})
    except Exception as e:
        logger.error(f"Error updating category order: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'message': f'Error updating category order: {str(e)}'})
