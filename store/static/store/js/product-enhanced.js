/**
 * Enhanced Products Page JavaScript
 * Modern interactive features for Somerset Shrimp Shack
 */

class ProductPageEnhancer {
    constructor() {
        this.init();
    }

    init() {
        this.setupIntersectionObserver();
        this.setupLazyLoading();
        this.setupFilterToggle();
        this.setupPriceRange();
        this.setupQuickActions();
        this.setupProductGrid();
        this.setupSmoothScroll();
    }

    setupIntersectionObserver() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry, index) => {
                if (entry.isIntersecting) {
                    setTimeout(() => {
                        entry.target.classList.add('animate-in');
                    }, index * 100);
                }
            });
        }, observerOptions);

        // Observe elements for animation
        const elementsToObserve = [
            '.product-card-modern',
            '.category-card-modern',
            '.category-section-modern'
        ];

        elementsToObserve.forEach(selector => {
            document.querySelectorAll(selector).forEach(el => {
                observer.observe(el);
            });
        });
    }

    setupLazyLoading() {
        const images = document.querySelectorAll('img[loading="lazy"]');
        
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src || img.src;
                        img.classList.remove('loading');
                        imageObserver.unobserve(img);
                    }
                });
            });

            images.forEach(img => {
                img.classList.add('loading');
                imageObserver.observe(img);
            });
        }
    }

    setupFilterToggle() {
        const toggleBtn = document.getElementById('toggle-filters');
        const filterContent = document.getElementById('filter-content');
        
        if (toggleBtn && filterContent) {
            let isVisible = true;
            
            toggleBtn.addEventListener('click', () => {
                isVisible = !isVisible;
                
                if (isVisible) {
                    filterContent.style.maxHeight = filterContent.scrollHeight + 'px';
                    filterContent.classList.remove('hidden');
                    toggleBtn.querySelector('span').textContent = 'Hide Filters';
                    toggleBtn.querySelector('i').className = 'fas fa-chevron-up';
                } else {
                    filterContent.style.maxHeight = '0';
                    filterContent.classList.add('hidden');
                    toggleBtn.querySelector('span').textContent = 'Show Filters';
                    toggleBtn.querySelector('i').className = 'fas fa-chevron-down';
                }
            });
        }
    }

    setupPriceRange() {
        const priceRange = document.getElementById('price-range-modern');
        const priceDisplay = document.getElementById('price-display');
        
        if (priceRange && priceDisplay) {
            const updatePrice = () => {
                const value = priceRange.value;
                priceDisplay.textContent = `£${value}`;
                
                // Update the background gradient
                const percentage = (value - priceRange.min) / (priceRange.max - priceRange.min) * 100;
                priceRange.style.background = `linear-gradient(to right, var(--primary) 0%, var(--primary) ${percentage}%, var(--border-color) ${percentage}%, var(--border-color) 100%)`;
            };
            
            priceRange.addEventListener('input', updatePrice);
            updatePrice(); // Initialize
        }
    }

    setupQuickActions() {
        document.querySelectorAll('.quick-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                const title = btn.getAttribute('title');
                
                if (title === 'Add to Wishlist') {
                    this.toggleWishlist(btn);
                } else if (title === 'Quick View') {
                    this.showQuickView(btn);
                }
            });
        });
    }

    toggleWishlist(btn) {
        btn.classList.toggle('active');
        const icon = btn.querySelector('i');
        
        if (btn.classList.contains('active')) {
            icon.className = 'fas fa-heart';
            this.showToast('Added to wishlist!');
        } else {
            icon.className = 'far fa-heart';
            this.showToast('Removed from wishlist');
        }
    }

    showQuickView(btn) {
        // Placeholder for quick view functionality
        this.showToast('Quick view coming soon!');
    }

    setupProductGrid() {
        const addToCartButtons = document.querySelectorAll('.btn-add-to-cart-modern');
        
        addToCartButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault(); // Prevent default form submission
                
                if (!btn.disabled) {
                    this.addToCartAjax(btn);
                }
            });
        });
    }

    addToCartAjax(btn) {
        const form = btn.closest('form');
        if (!form) return;
        
        // Show loading state
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>Adding...</span>';
        btn.disabled = true;
        
        // Get form data
        const formData = new FormData(form);
        const url = form.action;
        
        // Make AJAX request
        fetch(url, {
            method: 'POST',
            body: formData,
            credentials: 'same-origin', // Include cookies/session
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (response.ok) {
                // Success animation
                btn.innerHTML = '<i class="fas fa-check"></i><span>Added!</span>';
                btn.style.background = 'linear-gradient(45deg, var(--success), var(--success-light))';
                
                // Show success message or update cart counter if you have one
                this.showSuccessMessage('Item added to cart!');
                
                // Restore button after delay
                setTimeout(() => {
                    btn.innerHTML = originalText;
                    btn.style.background = '';
                    btn.disabled = false;
                }, 2000);
            } else {
                throw new Error('Failed to add to cart');
            }
        })
        .catch(error => {
            console.error('Error adding to cart:', error);
            // Error state
            btn.innerHTML = '<i class="fas fa-exclamation"></i><span>Error</span>';
            btn.style.background = 'linear-gradient(45deg, #dc3545, #ff6b7a)';
            
            // Show error message
            this.showErrorMessage('Failed to add item to cart. Please try again.');
            
            // Restore button after delay
            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.style.background = '';
                btn.disabled = false;
            }, 3000);
        });
    }
    
    showSuccessMessage(message) {
        this.showMessage(message, 'success');
    }
    
    showErrorMessage(message) {
        this.showMessage(message, 'error');
    }
    
    showMessage(message, type) {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
            <span>${message}</span>
        `;
        
        // Add styles
        Object.assign(toast.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            background: type === 'success' ? '#28a745' : '#dc3545',
            color: 'white',
            padding: '12px 20px',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            zIndex: '10000',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            transform: 'translateX(100%)',
            transition: 'transform 0.3s ease'
        });
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 100);
        
        // Remove after delay
        setTimeout(() => {
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 3000);
    }

    animateAddToCart(btn) {
        // Legacy method - now handled by addToCartAjax
    }

    setupSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(anchor.getAttribute('href'));
                
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        // Style the toast
        Object.assign(toast.style, {
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            background: type === 'error' ? '#ef4444' : '#10b981',
            color: 'white',
            padding: '12px 24px',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            zIndex: '9999',
            transform: 'translateX(100%)',
            transition: 'transform 0.3s ease'
        });
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 100);
        
        // Remove after delay
        setTimeout(() => {
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 3000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ProductPageEnhancer();
});

// Export for potential use in other scripts
window.ProductPageEnhancer = ProductPageEnhancer;
