from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from . import views
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import views as auth_views

app_name = 'store'

urlpatterns = [
    # Redirect root URL directly to product list (shop)
    path('', views.product_list, name='home'),
    
    # Shop URLs
    path('products/', views.product_list, name='product_list'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('care-guides/', views.care_guides, name='care_guides'),
    path('about-us/', views.about_us, name='about_us'),
    path('contact/', views.contact, name='contact'),
    
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='store/login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('signup/', views.signup, name='signup'),
    path('profile/', views.profile, name='profile'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='store/password_reset.html',
        email_template_name='store/password_reset_email.html',
        subject_template_name='store/password_reset_subject.txt'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='store/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='store/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='store/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # Cart URLs
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    
    # Checkout URLs
    path('checkout/<int:product_id>/', views.checkout_cart, name='checkout'),
    path('checkout/cart/', views.checkout_cart, name='checkout_cart'),
    path('success/', views.payment_success, name='payment_success'),
    path('cancel/', views.payment_cancel, name='payment_cancel'),
    path('webhook/stripe/', csrf_exempt(views.stripe_webhook), name='stripe_webhook'),
    
    # Order URLs
    path('order-history/', views.order_history, name='order_history'),
    path('order-detail/<str:order_reference>/', views.order_detail, name='order_detail'),
    path('order-summary/', views.order_summary, name='order_summary'),
    
    # Admin URLs
    path('dashboard/', staff_member_required(views.dashboard), name='dashboard'),
    
    # Stock Management URLs
    path('stock/', staff_member_required(views.stock_management), name='stock_management'),
    path('stock/update/<int:product_id>/', staff_member_required(views.update_stock), name='update_stock'),
    path('stock/bulk-update/', staff_member_required(views.update_stock_bulk), name='update_stock_bulk'),
    
    # Add this line - this is the URL your template is looking for
    path('stock/update/', staff_member_required(views.update_stock_bulk), name='update_stock_form'),
    
    # Product Management URLs
    path('products/manage/', staff_member_required(views.product_management), name='product_management'),
    path('products/edit/<int:product_id>/', staff_member_required(views.edit_product), name='edit_product'),
    path('products/add/', staff_member_required(views.add_product), name='add_product'),
    path('products/<int:product_id>/delete/', staff_member_required(views.delete_product), name='delete_product'),
    
    # Order Management URLs
    path('orders/', staff_member_required(views.order_management), name='order_management'),
    path('orders/<int:order_id>/update/', views.update_order_status, name='update_order_status'),
    path('order-status-update/<int:order_id>/', views.test_order_update, name='order_status_update'),

    # Category Management URLs
    path('categories/', staff_member_required(views.category_management), name='category_management'),
    path('categories/add/', staff_member_required(views.add_category), name='add_category'),
    path('categories/edit/<int:category_id>/', staff_member_required(views.edit_category), name='edit_category'),
    path('categories/delete/<int:category_id>/', staff_member_required(views.delete_category), name='delete_category'),
    path('categories/update-order/', csrf_exempt(staff_member_required(views.update_category_order)), name='update_category_order'),
    
    # Debug URLs
    path('debug-session/', views.debug_session, name='debug_session'),
    
    # Test URLs
    path('test-cart/', views.test_cart, name='test_cart'),
]
