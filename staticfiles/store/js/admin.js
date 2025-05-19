/**
 * Somerset Shrimp Shack - Admin Dashboard JavaScript
 * Handles admin-specific functionality including product management,
 * image uploads, and dashboard interactions
 */
document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const elements = {
        // Admin UI elements
        adminSidebarToggle: document.querySelector('.admin-sidebar-toggle'),
        adminSidebar: document.querySelector('.admin-sidebar'),
        
        // Product management
        productForm: document.querySelector('#product-form'),
        imageInput: document.querySelector('input[type="file"]'),
        imagePreview: document.querySelector('.admin-product-image'),
        
        // Status and visibility controls
        availableCheckbox: document.querySelector('#id_available'),
        featuredCheckbox: document.querySelector('#id_featured'),
        stockInput: document.querySelector('#id_stock'),
        categorySelect: document.querySelector('select[name="category"]'), // Added category selector
        
        // Product list
        productList: document.querySelector('.product-list'),
        productItems: document.querySelectorAll('.product-item')
    };
    
    // --- Initialize Admin Components ---
    initAdminUI(elements);
    initProductManagement(elements);
    initAvailabilityControls(elements);
    initCategoryControls(elements); // Added category initialization
    
    // --- Admin UI Functions ---
    function initAdminUI(elements) {
        // Admin sidebar toggle
        if (elements.adminSidebarToggle && elements.adminSidebar) {
            elements.adminSidebarToggle.addEventListener('click', () => {
                elements.adminSidebar.classList.toggle('active');
            });
        }
        
        // Add confirm dialog for delete actions
        document.querySelectorAll('.delete-action').forEach(btn => {
            btn.addEventListener('click', (e) => {
                if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                    e.preventDefault();
                }
            });
        });
        
        // Initialize datepickers if present
        if (typeof flatpickr !== 'undefined') {
            flatpickr('.datepicker', {
                altInput: true,
                altFormat: 'F j, Y',
                dateFormat: 'Y-m-d',
            });
        }
    }
    
    // --- Category Functions ---
    function initCategoryControls(elements) {
        // Ensure category dropdown is properly displayed
        if (elements.categorySelect) {
            // Force redraw of select element
            const currentValue = elements.categorySelect.value;
            elements.categorySelect.style.display = 'none';
            setTimeout(() => {
                elements.categorySelect.style.display = '';
                elements.categorySelect.value = currentValue;
            }, 0);
            
            // Add change event listener
            elements.categorySelect.addEventListener('change', () => {
                console.log('Category changed to:', elements.categorySelect.value);
            });
        } else {
            console.warn('Category select element not found in the form');
        }
    }
    
    // --- Product Management Functions ---
    function initProductManagement(elements) {
        // Image preview for product editing
        if (elements.imageInput && elements.imagePreview) {
            elements.imageInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        elements.imagePreview.src = e.target.result;
                        elements.imagePreview.style.display = 'block';
                    };
                    reader.readAsDataURL(file);
                }
            });
        }
        
        // Slug generation from name
        const nameInput = document.querySelector('#id_name');
        const slugInput = document.querySelector('#id_slug');
        
        if (nameInput && slugInput && !slugInput.value) {
            nameInput.addEventListener('blur', () => {
                // Only auto-fill if slug is empty and user hasn't modified it
                if (!slugInput.value || !slugInput.dataset.modified) {
                    slugInput.value = generateSlug(nameInput.value);
                }
            });
            
            slugInput.addEventListener('input', () => {
                // Mark slug as modified by user
                slugInput.dataset.modified = 'true';
            });
        }
        
        // Helper function to generate slug
        function generateSlug(text) {
            return text.toLowerCase()
                .replace(/[^\w\s-]/g, '') // Remove special characters
                .replace(/\s+/g, '-')     // Replace spaces with hyphens
                .replace(/-+/g, '-')      // Remove consecutive hyphens
                .trim();                  // Trim whitespace
        }
    }
    
    // --- Availability Controls Functions ---
    function initAvailabilityControls(elements) {
        // Auto-check available if stock is added
        if (elements.stockInput && elements.availableCheckbox) {
            elements.stockInput.addEventListener('change', () => {
                const stockValue = parseInt(elements.stockInput.value) || 0;
                
                // If stock is added and available is not checked, suggest checking it
                if (stockValue > 0 && !elements.availableCheckbox.checked) {
                    const makeAvailable = confirm(
                        'You added stock to this product. Would you like to make it available in the store?'
                    );
                    
                    if (makeAvailable) {
                        elements.availableCheckbox.checked = true;
                    }
                }
                
                // If stock is 0, warn about keeping product available
                if (stockValue === 0 && elements.availableCheckbox.checked) {
                    const warning = confirm(
                        'This product has 0 stock. Do you want to keep it available in the store?'
                    );
                    
                    if (!warning) {
                        elements.availableCheckbox.checked = false;
                    }
                }
            });
        }
        
        // Product form submission checks
        if (elements.productForm) {
            elements.productForm.addEventListener('submit', (e) => {
                const stockValue = parseInt(elements.stockInput?.value) || 0;
                const isAvailable = elements.availableCheckbox?.checked || false;
                
                // Ensure category is selected
                if (elements.categorySelect && elements.categorySelect.value === "") {
                    e.preventDefault();
                    alert('Please select a category for this product.');
                    return;
                }
                
                // Warn if product is available but has no stock
                if (isAvailable && stockValue === 0) {
                    const proceed = confirm(
                        'Warning: You are making this product available with 0 stock. Proceed?'
                    );
                    
                    if (!proceed) {
                        e.preventDefault();
                        return;
                    }
                }
                
                // Add loading state to submit button
                const submitButton = e.target.querySelector('button[type="submit"]');
                if (submitButton) {
                    submitButton.classList.add('loading');
                    submitButton.disabled = true;
                }
            });
        }
    }
});