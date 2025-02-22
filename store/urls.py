from django.urls import path
from . import views

app_name = 'store'  # Add this line to register the namespace

urlpatterns = [
    # Shop URLs
    path('', views.product_list, name='product_list'),
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('checkout/<int:product_id>/', views.checkout, name='checkout'),
    path('checkout/cart/', views.checkout_cart, name='checkout_cart'),
    path('success/', views.payment_success, name='payment_success'),
    path('cancel/', views.payment_cancel, name='payment_cancel'),
    path('order-history/', views.order_history, name='order_history'),
    path('order-summary/', views.order_summary, name='order_summary'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('stock/', views.stock_management, name='stock_management'),
    path('stock/update/<int:product_id>/', views.update_stock, name='update_stock'),
    path('edit_product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/<int:product_id>/delete/', views.delete_product, name='delete_product'),
]