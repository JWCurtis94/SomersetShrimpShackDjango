class Cart:
    def __init__(self, request):
        """Initialize the cart using Django's session"""
        self.session = request.session
        cart = self.session.get("cart")

        if not cart:
            cart = self.session["cart"] = {}  # Initialize empty cart

        self.cart = cart

    def add(self, product, quantity=1):
        """Add a product to the cart"""
        product_id = str(product.id)  # Convert to string (session keys must be strings)

        if product_id in self.cart:
            self.cart[product_id]["quantity"] += quantity
        else:
            self.cart[product_id] = {
                "id": product.id,  # Store product ID
                "name": product.name,
                "price": str(product.price),
                "quantity": quantity
            }

        self.save()

    def update(self, product_id, quantity):
        """Update the quantity of a product in the cart"""
        product_id = str(product_id)  # Ensure ID is a string

        if product_id in self.cart:
            self.cart[product_id]["quantity"] = quantity  # Update quantity
            self.save()

    def remove(self, product):
        """Remove a product from the cart"""
        product_id = str(product.id)

        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def save(self):
        """Save the cart in the session"""
        self.session["cart"] = self.cart
        self.session.modified = True

    def clear(self):
        """Remove all items from the cart"""
        self.session["cart"] = {}
        self.session.modified = True

    def get_items(self):
        """Return all cart items"""
        return self.cart.values()

    def get_total_price(self):
        """Calculate the total cost of all items in the cart"""
        return sum(float(item["price"]) * item["quantity"] for item in self.cart.values())
