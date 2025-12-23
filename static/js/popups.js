/**
 * Modern Popup Notification System
 * Handles beautiful, animated popup notifications for flash messages
 */

class PopupManager {
  constructor() {
    this.container = null;
    this.init();
  }

  init() {
    // Create popup container if it doesn't exist
    if (!document.querySelector('.popup-container')) {
      this.container = document.createElement('div');
      this.container.className = 'popup-container';
      document.body.appendChild(this.container);
    } else {
      this.container = document.querySelector('.popup-container');
    }

    // Process existing flash messages from Flask
    this.processFlashMessages();
  }

  processFlashMessages() {
    // Find all alert divs that Flask created
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
      const category = this.extractCategory(alert.className);
      const message = alert.textContent.trim();
      
      if (message) {
        this.show(message, category);
      }
      
      // Remove the original alert
      alert.remove();
    });
  }

  extractCategory(className) {
    if (className.includes('alert--success')) return 'success';
    if (className.includes('alert--danger')) return 'danger';
    if (className.includes('alert--warning')) return 'warning';
    if (className.includes('alert--info')) return 'info';
    return 'info'; // default
  }

  show(message, category = 'info', duration = 5000) {
    const popup = document.createElement('div');
    popup.className = `popup popup--${category}`;
    
    // Determine if we should auto-dismiss (danger messages stay longer)
    const autoDismiss = category !== 'danger';
    if (!autoDismiss) {
      popup.classList.add('popup--no-auto-dismiss');
      duration = 8000; // Danger messages stay longer
    }

    // Get icon based on category
    const icon = this.getIcon(category);
    const title = this.getTitle(category);

    popup.innerHTML = `
      <div class="popup__icon">${icon}</div>
      <div class="popup__content">
        <div class="popup__title">${title}</div>
        <div class="popup__message">${this.escapeHtml(message)}</div>
      </div>
      <button class="popup__close" aria-label="Close">×</button>
      ${autoDismiss ? '<div class="popup__progress-bar"></div>' : ''}
    `;

    // Add to container
    this.container.appendChild(popup);

    // Trigger animation
    requestAnimationFrame(() => {
      popup.style.opacity = '1';
    });

    // Close button handler
    const closeBtn = popup.querySelector('.popup__close');
    closeBtn.addEventListener('click', () => {
      this.close(popup);
    });

    // Auto-dismiss for non-danger messages
    if (autoDismiss) {
      setTimeout(() => {
        this.close(popup);
      }, duration);
    }

    // Click outside to close (optional - can be removed if not desired)
    // popup.addEventListener('click', (e) => {
    //   if (e.target === popup) {
    //     this.close(popup);
    //   }
    // });
  }

  close(popup) {
    if (!popup || !popup.parentNode) return;
    
    popup.classList.add('popup--exiting');
    
    setTimeout(() => {
      if (popup.parentNode) {
        popup.parentNode.removeChild(popup);
      }
    }, 300);
  }

  getIcon(category) {
    const icons = {
      success: '✓',
      danger: '✕',
      warning: '⚠',
      info: 'ℹ'
    };
    return icons[category] || icons.info;
  }

  getTitle(category) {
    const titles = {
      success: 'Success',
      danger: 'Error',
      warning: 'Warning',
      info: 'Information'
    };
    return titles[category] || titles.info;
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Public API methods
  success(message, duration) {
    this.show(message, 'success', duration);
  }

  error(message, duration) {
    this.show(message, 'danger', duration);
  }

  warning(message, duration) {
    this.show(message, 'warning', duration);
  }

  info(message, duration) {
    this.show(message, 'info', duration);
  }
}

// Initialize popup manager when DOM is ready
let popupManager;

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    popupManager = new PopupManager();
    window.popupManager = popupManager; // Make it globally available
  });
} else {
  popupManager = new PopupManager();
  window.popupManager = popupManager; // Make it globally available
}

