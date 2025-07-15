/**
 * Somerset Shrimp Shack - Main Frontend JavaScript
 * Handles all frontend user interactions including navigation, filtering,
 * and product display functionality
 */
document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const elements = {
        // Navigation elements
        mobileMenuBtn: document.querySelector('.mobile-menu-btn'),
        navbarMenu: document.querySelector('.navbar-menu'),
        navbar: document.querySelector('.navbar'),
        categoryBtn: document.querySelector('.category-btn'),
        categoryDropdown: document.querySelector('.category-dropdown'),
        userMenuBtn: document.querySelector('.user-menu-btn'),
        userDropdown: document.querySelector('.user-dropdown'),
        
        // Product elements
        productCards: document.querySelectorAll('.product-card'),
        searchInput: document.querySelector('.search-input'),
        priceRange: document.querySelector('#price-range'),
        priceValue: document.querySelector('#price-value'),
        categoryFilters: document.querySelectorAll('.category-filter'),
        categorySections: document.querySelectorAll('.category-section'),
        
        // UI elements
        closeMessageBtns: document.querySelectorAll('.close-message'),
        quantityInputs: document.querySelectorAll('input[type="number"]'),
        forms: document.querySelectorAll('form')
    };
    
    // --- Initialize UI Components ---
    initNavigation(elements);
    initMessageSystem(elements);
    initProductFilters(elements);
    initFormHandlers(elements);
    
    // --- Navigation Functions ---
    function initNavigation(elements) {
        // Mobile menu toggle
        if (elements.mobileMenuBtn && elements.navbarMenu) {
            elements.mobileMenuBtn.addEventListener('click', () => {
                elements.navbarMenu.classList.toggle('active');
            });
        }
        
        // Category dropdown toggle - handled by base.html inline script
        // User dropdown toggle - handled by base.html inline script
        
        // User dropdown toggle
        if (elements.userMenuBtn && elements.userDropdown) {
            elements.userMenuBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                elements.userDropdown.classList.toggle('show');
            });
        }
        
        // Close dropdowns when clicking outside
        document.addEventListener('click', (e) => {
            // Close category dropdown
            if (elements.categoryDropdown && elements.categoryBtn && 
                !elements.categoryDropdown.contains(e.target) && !elements.categoryBtn.contains(e.target)) {
                elements.categoryDropdown.classList.remove('show');
            }
            
            // Close user dropdown
            if (elements.userDropdown && elements.userMenuBtn &&
                !elements.userDropdown.contains(e.target) && !elements.userMenuBtn.contains(e.target)) {
                elements.userDropdown.classList.remove('show');
            }
        });
        
        // Navbar scroll effect
        window.addEventListener('scroll', () => {
            if (elements.navbar) {
                if (window.scrollY > 50) {
                    elements.navbar.classList.add('navbar-scrolled');
                } else {
                    elements.navbar.classList.remove('navbar-scrolled');
                }
            }
        });
    }
    
    // --- Message System Functions ---
    function initMessageSystem(elements) {
        if (elements.closeMessageBtns.length > 0) {
            // Close message buttons
            elements.closeMessageBtns.forEach(button => {
                button.addEventListener('click', () => {
                    const message = button.closest('.message');
                    fadeOutAndRemove(message);
                });
            });
            
            // Auto-hide messages after 5 seconds
            setTimeout(() => {
                document.querySelectorAll('.message').forEach(message => {
                    fadeOutAndRemove(message);
                });
            }, 5000);
        }
        
        function fadeOutAndRemove(element) {
            element.style.opacity = '0';
            setTimeout(() => element.remove(), 300);
        }
    }
    
    // --- Product Filter Functions ---
    function initProductFilters(elements) {
        // Search functionality
        if (elements.searchInput && elements.productCards.length > 0) {
            elements.searchInput.addEventListener('input', (e) => {
                filterProducts();
            });
        }
        
        // Price range filter
        if (elements.priceRange && elements.priceValue && elements.productCards.length > 0) {
            // Initialize price value display
            elements.priceValue.textContent = `£${elements.priceRange.value}`;
            
            elements.priceRange.addEventListener('input', () => {
                const maxPrice = parseFloat(elements.priceRange.value);
                elements.priceValue.textContent = `£${maxPrice}`;
                filterProducts();
            });
        }
        
        // Category filter
        if (elements.categoryFilters.length > 0 && elements.productCards.length > 0) {
            elements.categoryFilters.forEach(filter => {
                filter.addEventListener('change', () => {
                    filterProducts();
                });
            });
        }
        
        // Combined filter function
        function filterProducts() {
            // Get filter values
            const searchTerm = elements.searchInput ? elements.searchInput.value.toLowerCase() : '';
            const maxPrice = elements.priceRange ? parseFloat(elements.priceRange.value) : Infinity;
            
            // Get checked categories
            const checkedCategories = Array.from(elements.categoryFilters || [])
                .filter(f => f.checked)
                .map(f => f.value);
            
            // Apply filters to each product card
            elements.productCards.forEach(card => {
                // Get product data
                const title = card.querySelector('.product-title').textContent.toLowerCase();
                const description = card.querySelector('.product-description')?.textContent.toLowerCase() || '';
                const productPrice = parseFloat(card.querySelector('.product-price')?.dataset.price || '0');
                const cardCategory = card.dataset.category;
                
                // Check if product matches all filters
                const matchesSearch = title.includes(searchTerm) || description.includes(searchTerm);
                const matchesPrice = productPrice <= maxPrice;
                const matchesCategory = checkedCategories.length === 0 || checkedCategories.includes(cardCategory);
                
                // Show or hide product based on filters
                if (matchesSearch && matchesPrice && matchesCategory) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
            
            // Update category sections visibility
            updateCategorySections(checkedCategories);
        }
        
        // Helper function to update category sections visibility
        function updateCategorySections(checkedCategories = null) {
            elements.categorySections.forEach(section => {
                // If specific categories are checked, handle that case
                if (checkedCategories && checkedCategories.length > 0) {
                    const categoryName = section.querySelector('.category-title').textContent.toLowerCase().replace(/\s+/g, '_');
                    if (checkedCategories.includes(categoryName)) {
                        section.style.display = 'block';
                    } else {
                        section.style.display = 'none';
                    }
                    return;
                }
                
                // Otherwise, check if any products are visible
                const visibleProducts = section.querySelectorAll('.product-card[style="display: flex;"]');
                section.style.display = visibleProducts.length > 0 ? 'block' : 'none';
            });
        }
    }
    
    // --- Form Handling Functions ---
    function initFormHandlers(elements) {
        // Quantity input validation
        elements.quantityInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                const value = parseInt(e.target.value);
                const min = parseInt(e.target.min) || 1;
                if (value < min) {
                    e.target.value = min;
                }
            });
        });
        
        // Form submission loading states
        elements.forms.forEach(form => {
            form.addEventListener('submit', () => {
                const submitButton = form.querySelector('button[type="submit"]');
                if (submitButton) {
                    submitButton.classList.add('loading');
                    submitButton.disabled = true;
                }
            });
        });
    }
});