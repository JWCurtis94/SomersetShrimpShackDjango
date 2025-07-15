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
        productForm: document.querySelector('form[action*="add_product"], form[action*="edit_product"]'),
        imageInput: document.querySelector('input[type="file"]'),
        imagePreview: document.querySelector('.admin-product-image, #image-preview'),
        
        // Status and visibility controls
        availableCheckbox: document.querySelector('#available, #id_available'),
        featuredCheckbox: document.querySelector('#featured, #id_featured'),
        stockInput: document.querySelector('#stock, #id_stock'),
        categorySelect: document.querySelector('select[name="category"]'),
        
        // Product list
        productList: document.querySelector('.product-list'),
        productItems: document.querySelectorAll('.product-item')
    };
    
    // --- Initialize Admin Components ---
    initAdminUI(elements);
    initProductManagement(elements);
    initAvailabilityControls(elements);
    initCategoryControls(elements);
    
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
            // Add enhanced styling to make sure dropdown is visible
            elements.categorySelect.style.color = '#4a4a4a';
            elements.categorySelect.style.backgroundColor = '#ffffff';
            elements.categorySelect.style.border = '1px solid #ced4da';
            elements.categorySelect.style.borderRadius = '6px';
            elements.categorySelect.style.padding = '0.75rem 1rem';
            elements.categorySelect.style.appearance = 'auto';
            
            // Add change event listener
            elements.categorySelect.addEventListener('change', () => {
                console.log('Category changed to:', elements.categorySelect.value);
                // Make sure the category has an actual value
                if (elements.categorySelect.value) {
                    elements.categorySelect.classList.remove('is-invalid');
                    const errorMessage = elements.categorySelect.parentElement.querySelector('.error-message');
                    if (errorMessage) {
                        errorMessage.remove();
                    }
                }
            });
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
        const nameInput = document.querySelector('#id_name, #name');
        const slugInput = document.querySelector('#id_slug, #slug');
        
        if (nameInput && slugInput) {
            nameInput.addEventListener('blur', () => {
                // Only auto-fill if slug is empty and user hasn't modified it
                if (!slugInput.value || !slugInput.dataset.modified) {
                    slugInput.value = generateSlug(nameInput.value);
                }
            });
            
            if (slugInput) {
                slugInput.addEventListener('input', () => {
                    // Mark slug as modified by user
                    slugInput.dataset.modified = 'true';
                });
            }
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
        // Auto-check available for new products with stock
        if (elements.stockInput) {
            // First, ensure we have an availability checkbox (add it if not found)
            if (!elements.availableCheckbox) {
                // This might be on the add_product form where the checkbox is just named 'available'
                elements.availableCheckbox = document.querySelector('#available');
            }
            
            // Create a hidden input for availability if checkbox doesn't exist
            if (!elements.availableCheckbox && elements.stockInput.form) {
                const hiddenAvailable = document.createElement('input');
                hiddenAvailable.type = 'hidden';
                hiddenAvailable.name = 'available';
                hiddenAvailable.value = 'on'; // Default to available
                elements.stockInput.form.appendChild(hiddenAvailable);
                elements.availableCheckbox = hiddenAvailable;
            }
            
            // Add stock change handler
            elements.stockInput.addEventListener('change', () => {
                const stockValue = parseInt(elements.stockInput.value) || 0;
                
                if (elements.availableCheckbox && elements.availableCheckbox.type !== 'hidden') {
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
                } else if (elements.availableCheckbox) {
                    // For hidden input
                    if (stockValue > 0) {
                        elements.availableCheckbox.value = 'on';
                    }
                }
            });
        }
        
        // Product form submission checks
        if (elements.productForm) {
            elements.productForm.addEventListener('submit', (e) => {
                const stockValue = parseInt(elements.stockInput?.value) || 0;
                const isAvailableElement = elements.availableCheckbox || document.querySelector('#available, #id_available');
                let isAvailable = false;
                
                // Handle different types of available controls
                if (isAvailableElement) {
                    if (isAvailableElement.type === 'checkbox') {
                        isAvailable = isAvailableElement.checked;
                    } else if (isAvailableElement.type === 'hidden') {
                        isAvailable = isAvailableElement.value === 'on';
                    }
                } else {
                    // If no available checkbox exists, create and add a hidden one
                    const hiddenAvailable = document.createElement('input');
                    hiddenAvailable.type = 'hidden';
                    hiddenAvailable.name = 'available';
                    hiddenAvailable.value = stockValue > 0 ? 'on' : 'off';
                    e.target.appendChild(hiddenAvailable);
                    isAvailable = stockValue > 0;
                }
                
                // Ensure category is selected
                if (elements.categorySelect && elements.categorySelect.value === "") {
                    e.preventDefault();
                    alert('Please select a category for this product.');
                    elements.categorySelect.classList.add('is-invalid');
                    elements.categorySelect.focus();
                    return;
                }
                
                // Ensure stock is a valid number
                if (elements.stockInput && (isNaN(stockValue) || stockValue < 0)) {
                    e.preventDefault();
                    alert('Please enter a valid stock value (0 or positive number).');
                    elements.stockInput.classList.add('is-invalid');
                    elements.stockInput.focus();
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
                
                // Auto-set available based on stock for new products
                if (stockValue > 0 && isAvailableElement && !isAvailable) {
                    if (confirm('This product has stock. Do you want to make it available in the store?')) {
                        if (isAvailableElement.type === 'checkbox') {
                            isAvailableElement.checked = true;
                        } else if (isAvailableElement.type === 'hidden') {
                            isAvailableElement.value = 'on';
                        }
                    }
                }
                
                // Add loading state to submit button
                const submitButton = e.target.querySelector('button[type="submit"]');
                if (submitButton) {
                    submitButton.classList.add('loading');
                    submitButton.disabled = true;
                }
                
                console.log('Submitting product with:', {
                    stock: stockValue,
                    available: isAvailable,
                    category: elements.categorySelect?.value
                });
            });
        }
    }
});