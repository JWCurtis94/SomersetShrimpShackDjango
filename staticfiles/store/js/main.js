document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const navbarMenu = document.querySelector('.navbar-menu');
    const categoryBtn = document.querySelector('.category-btn');
    const categoryDropdown = document.querySelector('.category-dropdown');
    const userMenuBtn = document.querySelector('.user-menu-btn');
    const userDropdown = document.querySelector('.user-dropdown');
    const closeMessageBtns = document.querySelectorAll('.close-message');
    const searchInput = document.querySelector('.search-input');
    const productCards = document.querySelectorAll('.product-card');
    const priceRange = document.querySelector('#price-range');
    const priceValue = document.querySelector('#price-value');
    const categoryFilters = document.querySelectorAll('.category-filter');
    const adminSidebarToggle = document.querySelector('.admin-sidebar-toggle');
    const adminSidebar = document.querySelector('.admin-sidebar');
    const imageInput = document.querySelector('input[type="file"]');
    const imagePreview = document.querySelector('.admin-product-image');
    
    // --- Mobile menu toggle ---
    if (mobileMenuBtn && navbarMenu) {
        mobileMenuBtn.addEventListener('click', () => {
            navbarMenu.classList.toggle('active');
        });
    }
    
    // --- Category dropdown toggle ---
    if (categoryBtn && categoryDropdown) {
        categoryBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            categoryDropdown.classList.toggle('active');
        });
    }
    
    // --- User dropdown toggle ---
    if (userMenuBtn && userDropdown) {
        userMenuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            userDropdown.classList.toggle('active');
        });
    }
    
    // --- Close dropdowns when clicking outside ---
    document.addEventListener('click', (e) => {
        // Close category dropdown
        if (categoryDropdown && categoryBtn && 
            !categoryDropdown.contains(e.target) && !categoryBtn.contains(e.target)) {
            categoryDropdown.classList.remove('active');
        }
        
        // Close user dropdown
        if (userDropdown && userMenuBtn &&
            !userDropdown.contains(e.target) && !userMenuBtn.contains(e.target)) {
            userDropdown.classList.remove('active');
        }
    });
    
    // --- Message handling ---
    if (closeMessageBtns.length > 0) {
        // Close message buttons
        closeMessageBtns.forEach(button => {
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
    }
    
    // --- Product search functionality ---
    if (searchInput && productCards.length > 0) {
        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            
            productCards.forEach(card => {
                const title = card.querySelector('.product-title').textContent.toLowerCase();
                const description = card.querySelector('.product-description')?.textContent.toLowerCase() || '';
                
                if (title.includes(searchTerm) || description.includes(searchTerm)) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
            
            updateCategorySections();
        });
    }
    
    // --- Price range filter ---
    if (priceRange && priceValue && productCards.length > 0) {
        // Initialize price value display
        priceValue.textContent = `£${priceRange.value}`;
        
        priceRange.addEventListener('input', () => {
            const maxPrice = parseFloat(priceRange.value);
            priceValue.textContent = `£${maxPrice}`;
            
            // Filter products by price
            productCards.forEach(card => {
                const productPrice = parseFloat(card.querySelector('.product-price').dataset.price);
                if (productPrice <= maxPrice) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
            
            updateCategorySections();
        });
    }
    
    // --- Category filter ---
    if (categoryFilters.length > 0 && productCards.length > 0) {
        categoryFilters.forEach(filter => {
            filter.addEventListener('change', () => {
                // Get all checked categories
                const checkedCategories = Array.from(categoryFilters)
                    .filter(f => f.checked)
                    .map(f => f.value);
                
                // If no categories are checked, show all products
                if (checkedCategories.length === 0) {
                    productCards.forEach(card => {
                        card.style.display = 'flex';
                    });
                } else {
                    // Filter products by selected categories
                    productCards.forEach(card => {
                        const cardCategory = card.dataset.category;
                        if (checkedCategories.includes(cardCategory)) {
                            card.style.display = 'flex';
                        } else {
                            card.style.display = 'none';
                        }
                    });
                }
                
                updateCategorySections(checkedCategories);
            });
        });
    }
    
    // Helper function to update category sections visibility
    function updateCategorySections(checkedCategories = null) {
        document.querySelectorAll('.category-section').forEach(section => {
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
    
    // --- Quantity input validation ---
    document.querySelectorAll('input[type="number"]').forEach(input => {
        input.addEventListener('change', (e) => {
            const value = parseInt(e.target.value);
            const min = parseInt(e.target.min) || 1;
            if (value < min) {
                e.target.value = min;
            }
        });
    });
    
    // --- Form submission loading states ---
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', () => {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.classList.add('loading');
                submitButton.disabled = true;
            }
        });
    });
    
    // --- Admin sidebar toggle ---
    if (adminSidebarToggle && adminSidebar) {
        adminSidebarToggle.addEventListener('click', () => {
            adminSidebar.classList.toggle('active');
        });
    }
    
    // --- Image preview for product editing ---
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
});