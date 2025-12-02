/**
 * BMS WELCOME UI SCRIPT
 * Enhanced interactions for welcome card
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize welcome UI
    initWelcomeUI();
    
    // Add interactive effects
    setupCardInteractions();
    setupButtonEffects();
});

/**
 * Initialize main welcome UI components
 */
function initWelcomeUI() {
    console.log('BMS Welcome UI Initialized');
    
    // Preload resources if needed
    preloadResources();
    
    // Add loading state management
    handleLoadingStates();
}

/**
 * Setup card hover and interactive effects
 */
function setupCardInteractions() {
    const welcomeCard = document.querySelector('.welcome-card');
    const buttons = document.querySelectorAll('.btn');
    
    if (!welcomeCard) return;
    
    // Card mouse move parallax effect
    welcomeCard.addEventListener('mousemove', (e) => {
        const cardRect = welcomeCard.getBoundingClientRect();
        const cardCenterX = cardRect.left + cardRect.width / 2;
        const cardCenterY = cardRect.top + cardRect.height / 2;
        
        const mouseX = e.clientX - cardCenterX;
        const mouseY = e.clientY - cardCenterY;
        
        // Subtle tilt effect
        const tiltX = (mouseY / cardRect.height) * 2;
        const tiltY = (mouseX / cardRect.width) * -2;
        
        welcomeCard.style.transform = `
            perspective(1000px)
            rotateX(${tiltX}deg)
            rotateY(${tiltY}deg)
            translateY(-2px)
        `;
        
        // Subtle glow follow effect
        const glowX = (mouseX / cardRect.width) * 20;
        const glowY = (mouseY / cardRect.height) * 20;
        
        welcomeCard.style.boxShadow = `
            ${glowX}px ${glowY}px 40px rgba(0, 0, 0, 0.4),
            0 0 40px rgba(0, 200, 255, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.15)
        `;
    });
    
    // Reset card position when mouse leaves
    welcomeCard.addEventListener('mouseleave', () => {
        welcomeCard.style.transform = `
            perspective(1000px)
            rotateX(0deg)
            rotateY(0deg)
            translateY(0)
        `;
        welcomeCard.style.boxShadow = `
            0 8px 32px rgba(0, 0, 0, 0.3),
            0 0 30px rgba(0, 200, 255, 0.15),
            inset 0 1px 0 rgba(255, 255, 255, 0.1)
        `;
    });
}

/**
 * Enhanced button effects and interactions
 */
function setupButtonEffects() {
    const buttons = document.querySelectorAll('.btn');
    
    buttons.forEach(button => {
        // Ripple effect on click
        button.addEventListener('click', function(e) {
            createRippleEffect(e, this);
        });
        
        // Enhanced hover sound simulation (visual feedback)
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-3px) scale(1.02)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
        
        // Keyboard navigation support
        button.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                this.click();
            }
        });
    });
}

/**
 * Create ripple effect on button click
 */
function createRippleEffect(event, button) {
    const ripple = document.createElement('span');
    const rect = button.getBoundingClientRect();
    
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;
    
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    ripple.classList.add('ripple-effect');
    
    // Remove existing ripples
    const existingRipples = button.querySelectorAll('.ripple-effect');
    existingRipples.forEach(ripple => ripple.remove());
    
    button.appendChild(ripple);
    
    // Remove ripple after animation
    setTimeout(() => {
        ripple.remove();
    }, 600);
}

/**
 * Handle preloading of resources
 */
function preloadResources() {
    // Preload hover images or fonts if needed
    const preloadLinks = [
        // Add any resources that need preloading
    ];
    
    preloadLinks.forEach(href => {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.href = href;
        link.as = 'image';
        document.head.appendChild(link);
    });
}

/**
 * Manage loading states
 */
function handleLoadingStates() {
    // Remove any initial loading class from body
    document.body.classList.remove('loading');
    
    // Add loaded class for any post-load animations
    setTimeout(() => {
        document.body.classList.add('loaded');
    }, 100);
}

/**
 * Add CSS for ripple effect dynamically
 */
function injectRippleStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .ripple-effect {
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.6);
            transform: scale(0);
            animation: ripple-animation 0.6s linear;
            pointer-events: none;
        }
        
        @keyframes ripple-animation {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
        
        .btn {
            position: relative;
            overflow: hidden;
        }
        
        /* Loading state styles */
        body.loading .welcome-card {
            opacity: 0;
            transform: translateY(20px);
        }
        
        body.loaded .welcome-card {
            opacity: 1;
            transform: translateY(0);
        }
    `;
    document.head.appendChild(style);
}

// Inject ripple styles when script loads
injectRippleStyles();

/**
 * Utility function for page transitions
 */
function smoothPageTransition(url) {
    const welcomeCard = document.querySelector('.welcome-card');
    if (welcomeCard) {
        welcomeCard.style.transform = 'scale(0.9)';
        welcomeCard.style.opacity = '0';
        welcomeCard.style.transition = 'all 0.3s ease';
    }
    
    setTimeout(() => {
        window.location.href = url;
    }, 300);
}

// Export functions for potential use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initWelcomeUI,
        setupCardInteractions,
        setupButtonEffects
    };
}