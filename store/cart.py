from decimal import Decimal
from django.conf import settings
from .models import Product

class Cart:
    """
    Shopping cart implementation that stores cart data in the user's session.
    Provides methods to add, update, remove items and calculate totals.
    """
    def __init__(self, request):
        """Initialize the cart using Django's session"""
        self.session = request.session
        cart = self.session.get("cart")

        if not cart:
            cart = self.session["cart"] = {}  # Initialize empty cart

        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False, size=None):
        """
        Add a product to the cart or update its quantity.
        
        Args:
            product: Product object to add
            quantity: Number of items to add
            override_quantity: If True, replace the current quantity instead of adding
            size: Optional product size variant
        """
        product_id = str(product.id)
        
        # Create a unique identifier for product+size combinations
        cart_key = product_id
        if size:
            cart_key = f"{product_id}_{size}"
            
        # Add new item to cart if not already present
        if cart_key not in self.cart:
            self.cart[cart_key] = {
                'id': product_id,
                'name': product.name,
                'price': str(product.price),
                'quantity': 0,
                'size': size
            }
        
        # Update quantity based on override flag
        if override_quantity:
            self.cart[cart_key]['quantity'] = quantity
        else:
            self.cart[cart_key]['quantity'] += quantity
            
        self.save()

    def update(self, product_id, quantity, size=None):
        """
        Update the quantity of a product in the cart
        
        Args:
            product_id: ID of the product to update
            quantity: New quantity value
            size: Optional product size to identify the specific cart item
        """
        product_id = str(product_id)  # Ensure ID is a string
        
        # Create the cart key based on product ID and optional size
        cart_key = product_id
        if size:
            cart_key = f"{product_id}_{size}"
            
        # Update the item if it exists
        if cart_key in self.cart and int(quantity) > 0:
            self.cart[cart_key]["quantity"] = int(quantity)
            self.save()
            return True
        return False

    def remove(self, product, size=None):
        """
        Remove a product from the cart
        
        Args:
            product: Product object to remove
            size: Optional product size to identify specific item to remove
        """
        product_id = str(product.id)
        
        # Create the cart key based on product ID and optional size
        cart_key = product_id
        if size:
            cart_key = f"{product_id}_{size}"

        # Remove the item if it exists
        if cart_key in self.cart:
            del self.cart[cart_key]
            self.save()
            return True
        return False

    def save(self):
        """Save the cart in the session"""
        self.session["cart"] = self.cart
        self.session.modified = True

    def clear(self):
        """Remove all items from the cart"""
        self.session["cart"] = {}
        self.cart = self.session["cart"]  # Update the reference
        self.session.modified = True

    def is_in_cart(self, product, size=None):
        """
        Check if a product is already in the cart
        
        Args:
            product: Product object to check
            size: Optional product size to check for specific variant
            
        Returns:
            bool: True if the product is in the cart, False otherwise
        """
        product_id = str(product.id)
        
        # Create the cart key based on product ID and optional size
        cart_key = product_id
        if size:
            cart_key = f"{product_id}_{size}"
            
        return cart_key in self.cart

    def get_items(self):
        """Return all cart items"""
        return self.cart.values()

    def get_total_price(self):
        """Calculate the total cost of all items in the cart"""
        return sum(Decimal(item["price"]) * item["quantity"] for item in self.cart.values())
    
    def get_item_count(self):
        """Get total number of items in cart"""
        return sum(item["quantity"] for item in self.cart.values())
        
    def get_cart_items(self):
        """
        Return cart items as CartItem objects with full product information
        """
        cart_items = []
        for item in self.cart.values():
            try:
                product = Product.objects.get(id=item['id'])
                cart_items.append(CartItem(
                    product=product,
                    quantity=item['quantity'],
                    size=item.get('size')
                ))
            except Product.DoesNotExist:
                # Handle case where product no longer exists
                pass
        
        return cart_items
        
    def get_shipping_cost(self):
        """
        Calculate shipping cost based on cart contents
        Returns Decimal with shipping cost in GBP
        
        Shipping Rules:
        - Shrimp products: £12
        - All other items: £6
        - Mixed cart (shrimp + non-shrimp): £12 (shrimp shipping applies)
        """
        from decimal import Decimal
        
        # If cart is empty, no shipping cost
        if not self.cart:
            return Decimal('0.00')
        
        # Check if any item in the cart is a shrimp product
        cart_items = self.get_cart_items()
        has_shrimp = any(item.product.is_shrimp_product for item in cart_items)
        
        # Return appropriate shipping cost
        if has_shrimp:
            return Decimal('12')  # Shrimp shipping cost
        else:
            return Decimal('6')   # Standard shipping cost
        
    def __iter__(self):
        """
        Make Cart class iterable to loop through items
        """
        for item in self.cart.values():
            yield item
            
    def __len__(self):
        """
        Return the total number of items in the cart
        """
        return self.get_item_count()


class CartItem:
    """
    Class representing an item in the shopping cart
    Provides convenient access to product details and calculations
    """
    def __init__(self, product, quantity, size=None):
        self.product = product
        self.quantity = quantity
        self.size = size
        self.price = product.price
        self.total_price = product.price * quantity
    
    def __str__(self):
        size_text = f" ({self.size})" if self.size else ""
        return f"{self.quantity} x {self.product.name}{size_text}"