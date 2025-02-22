// Mobile menu toggle
const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
const navbarMenu = document.querySelector('.navbar-menu');

if (mobileMenuBtn) {
    mobileMenuBtn.addEventListener('click', () => {
        navbarMenu.classList.toggle('active');
    });
}

// Close messages
document.querySelectorAll('.close-message').forEach(button => {
    button.addEventListener('click', () => {
        const message = button.closest('.message');
        message.style.opacity = '0';
        setTimeout(() => message.remove(), 300);
    });
});

// Auto-hide messages after 5 seconds
setTimeout(() => {
    document.querySelectorAll('.message').forEach(message => {
        message.style.opacity = '0';
        setTimeout(() => message.remove(), 300);
    });
}, 5000);

// Product search functionality
const searchInput = document.querySelector('.search-input');
const productCards = document.querySelectorAll('.product-card');

if (searchInput) {
    searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        
        productCards.forEach(card => {
            const title = card.querySelector('.product-title').textContent.toLowerCase();
            const description = card.querySelector('.product-description')?.textContent.toLowerCase() || '';
            
            if (title.includes(searchTerm) || description.includes(searchTerm)) {
                card.style.display = '';
            } else {
                card.style.display = 'none';
            }
        });
    });
}

// Price range filter
const priceRange = document.querySelector('#price-range');
const priceValue = document.querySelector('#price-value');

if (priceRange && priceValue) {
    priceRange.addEventListener('input', (e) => {
        const value = e.target.value;
        priceValue.textContent = `£${value}`;
        
        productCards.forEach(card => {
            const price = parseFloat(card.querySelector('.product-price').dataset.price);
            card.style.display = price <= value ? '' : 'none';
        });
    });
}

// Category filter
const categoryFilters = document.querySelectorAll('.category-filter');

categoryFilters.forEach(filter => {
    filter.addEventListener('change', () => {
        const selectedCategories = Array.from(categoryFilters)
            .filter(f => f.checked)
            .map(f => f.value);
            
        productCards.forEach(card => {
            const category = card.dataset.category;
            card.style.display = selectedCategories.length === 0 || selectedCategories.includes(category) ? '' : 'none';
        });
    });
});

// Quantity input validation
document.querySelectorAll('input[type="number"]').forEach(input => {
    input.addEventListener('change', (e) => {
        const value = parseInt(e.target.value);
        const min = parseInt(e.target.min) || 1;
        if (value < min) {
            e.target.value = min;
        }
    });
});

// Form submission loading states
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', () => {
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.classList.add('loading');
            submitButton.disabled = true;
        }
    });
});

// Admin sidebar toggle
const adminSidebarToggle = document.querySelector('.admin-sidebar-toggle');
const adminSidebar = document.querySelector('.admin-sidebar');

if (adminSidebarToggle && adminSidebar) {
    adminSidebarToggle.addEventListener('click', () => {
        adminSidebar.classList.toggle('active');
    });
}

// Image preview for product editing
const imageInput = document.querySelector('input[type="file"]');
const imagePreview = document.querySelector('.admin-product-image');

if (imageInput && imagePreview) {
    imageInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                imagePreview.src = e.target.result;
            };
            reader.readAsDataURL(file);
        }
    });
}