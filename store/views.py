from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings
from .models import Product, Order
from .cart import Cart
import stripe

# Set up Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY

# Helper Functions
def is_staff(user):
    return user.is_staff

# Public Views
def product_list(request):
    category_filter = request.GET.get('category')
    
    if category_filter:
        products = Product.objects.filter(category=category_filter, available=True)
        categorized_products = {
            category_filter.replace('_', ' ').title(): products
        }
    else:
        categorized_products = {
            "Neocaridina Shrimp": Product.objects.filter(category="neocaridina", available=True),
            "Caridina Shrimp": Product.objects.filter(category="caridina", available=True),
            "Floating Plants": Product.objects.filter(category="floating_plants", available=True),
            "Stem Plants": Product.objects.filter(category="stem_plants", available=True),
            "Rosette Plants": Product.objects.filter(category="rosette_plants", available=True),
            "Botanicals": Product.objects.filter(category="botanicals", available=True),
            "Shrimp Food": Product.objects.filter(category="food", available=True),
            "Merchandise": Product.objects.filter(category="merchandise", available=True),
        }
    
    return render(request, "store/product_list.html", {
        "categorized_products": categorized_products
    })

# Cart Views
def cart_view(request):
    cart = Cart(request)
    return render(request, "store/cart.html", {"cart": cart})

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if product.stock <= 0:
        messages.error(request, "This product is out of stock.")
        return redirect("store:product_list")
    
    cart = Cart(request)
    cart.add(product)
    messages.success(request, f"{product.name} added to cart.")
    return redirect("store:cart_view")

def remove_from_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    cart.remove(product)
    messages.success(request, f"{product.name} removed from cart.")
    return redirect("store:cart_view")

def clear_cart(request):
    cart = Cart(request)
    cart.clear()
    messages.success(request, "Cart cleared successfully.")
    return redirect("store:cart_view")

def update_cart(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        try:
            new_quantity = int(request.POST.get("quantity", 1))
            if new_quantity <= 0:
                messages.error(request, "Quantity must be greater than 0.")
                return redirect("store:cart_view")
            if new_quantity > product.stock:
                messages.error(request, f"Only {product.stock} items available.")
                new_quantity = product.stock
            cart.update(product_id, new_quantity)
            messages.success(request, "Cart updated successfully.")
        except ValueError:
            messages.error(request, "Invalid quantity provided.")

    return redirect("store:cart_view")

# Checkout Views
def checkout(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if product.stock <= 0:
        messages.error(request, "This product is out of stock.")
        return redirect("store:product_list")

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'gbp',
                    'product_data': {'name': product.name},
                    'unit_amount': int(product.price * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri('/success/'),
            cancel_url=request.build_absolute_uri('/cancel/'),
        )
        return redirect(session.url, code=303)
    except stripe.error.StripeError as e:
        messages.error(request, "Payment processing error. Please try again.")
        return redirect("store:product_list")

def checkout_cart(request):
    cart = Cart(request)
    if not cart.get_items():
        messages.error(request, "Your cart is empty.")
        return redirect("store:cart_view")

    line_items = []
    for item in cart.get_items():
        product = get_object_or_404(Product, id=item['id'])
        if item['quantity'] > product.stock:
            messages.error(request, f"Only {product.stock} {product.name}(s) available.")
            return redirect("store:cart_view")
            
        line_items.append({
            'price_data': {
                'currency': 'gbp',
                'product_data': {'name': item['name']},
                'unit_amount': int(float(item['price']) * 100),
            },
            'quantity': item['quantity'],
        })

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri('/success/'),
            cancel_url=request.build_absolute_uri('/cancel/'),
        )

        # Create orders
        for item in cart.get_items():
            Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                product=Product.objects.get(id=item["id"]),
                stripe_checkout_id=session.id,
                email=request.user.email if request.user.is_authenticated else "guest@example.com",
                paid=False
            )

        cart.clear()
        return redirect(session.url, code=303)
    except stripe.error.StripeError as e:
        messages.error(request, "Payment processing error. Please try again.")
        return redirect("store:cart_view")

def payment_success(request):
    messages.success(request, "Payment successful! Thank you for your order.")
    return render(request, 'store/success.html')

def payment_cancel(request):
    messages.warning(request, "Payment cancelled.")
    return render(request, 'store/cancel.html')

# Order Views
@login_required
def order_history(request):
    orders = Order.objects.filter(
        user=request.user, 
        paid=True
    ).order_by('-created_at')
    return render(request, 'store/order_history.html', {'orders': orders})

def order_summary(request):
    cart = Cart(request)
    return render(request, "store/order_summary.html", {"cart": cart})

# Admin Views
@login_required
@user_passes_test(is_staff)
def dashboard(request):
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_revenue = sum(order.product.price for order in Order.objects.filter(paid=True))
    
    return render(request, 'store/dashboard.html', {
        'total_products': total_products,
        'total_orders': total_orders,
        'total_revenue': total_revenue
    })

@login_required
@user_passes_test(is_staff)
def stock_management(request):
    products = Product.objects.all().order_by('name')
    return render(request, 'store/stock_management.html', {'products': products})

@login_required
@user_passes_test(is_staff)
def update_stock(request, product_id):
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    
    product = get_object_or_404(Product, id=product_id)
    try:
        new_stock = int(request.POST.get("stock", 0))
        if new_stock < 0:
            raise ValueError("Stock cannot be negative")
        
        product.stock = new_stock
        product.available = new_stock > 0
        product.save()
        
        messages.success(request, f"Stock updated for {product.name}")
    except ValueError as e:
        messages.error(request, str(e))
    
    return redirect('store:stock_management')

@login_required
@user_passes_test(is_staff)
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == "POST":
        try:
            product.name = request.POST.get("name")
            product.description = request.POST.get("description")
            product.price = float(request.POST.get("price"))
            product.stock = int(request.POST.get("stock"))
            product.available = product.stock > 0

            if 'image' in request.FILES:
                product.image = request.FILES['image']

            product.save()
            messages.success(request, f"{product.name} updated successfully.")
            return redirect('store:stock_management')
        except ValueError:
            messages.error(request, "Invalid values provided.")
    
    return render(request, 'store/edit_product.html', {'product': product})

@login_required
@user_passes_test(is_staff)
def add_product(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description')
            price = float(request.POST.get('price'))
            stock = int(request.POST.get('stock'))
            category = request.POST.get('category')
            image = request.FILES.get('image')
            
            if price < 0:
                raise ValueError("Price cannot be negative")
            if stock < 0:
                raise ValueError("Stock cannot be negative")
                
            product = Product.objects.create(
                name=name,
                description=description,
                price=price,
                stock=stock,
                category=category,
                image=image if image else None,
                available=stock > 0
            )
            
            messages.success(request, f"{product.name} added successfully.")
            return redirect('store:stock_management')
        except ValueError as e:
            messages.error(request, str(e))
        
    return render(request, 'store/add_product.html', {
        'categories': Product.CATEGORY_CHOICES
    })

@login_required
@user_passes_test(is_staff)
def delete_product(request, product_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
        
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, f"{product.name} deleted successfully.")
    return JsonResponse({'status': 'success'})