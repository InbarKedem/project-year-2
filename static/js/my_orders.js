// My Orders Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const filterForm = document.getElementById('filterForm');
    const filterToggle = document.querySelector('.filter-toggle');
    const toggleText = document.getElementById('toggle-text');
    const toggleIcon = document.querySelector('.toggle-icon');
    
    // Toggle filter form visibility
    if (filterToggle) {
        filterToggle.addEventListener('click', function() {
            if (filterForm.style.display === 'none') {
                filterForm.style.display = 'flex';
                toggleText.textContent = 'Collapse';
                toggleIcon.textContent = '▼';
            } else {
                filterForm.style.display = 'none';
                toggleText.textContent = 'Expand';
                toggleIcon.textContent = '▶';
            }
        });
    }
    
    // Handle cancel order confirmation
    const cancelForms = document.querySelectorAll('form[action*="cancel_order"]');
    cancelForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!confirm('Are you sure you want to cancel this order? A 5% cancellation fee will be applied.')) {
                e.preventDefault();
            }
        });
    });
});

// Global functions for backward compatibility (if needed)
function toggleFilters() {
    const form = document.getElementById('filterForm');
    const toggleText = document.getElementById('toggle-text');
    const toggleIcon = document.querySelector('.toggle-icon');
    
    if (form.style.display === 'none') {
        form.style.display = 'flex';
        toggleText.textContent = 'Collapse';
        toggleIcon.textContent = '▼';
    } else {
        form.style.display = 'none';
        toggleText.textContent = 'Expand';
        toggleIcon.textContent = '▶';
    }
}

function resetFilters() {
    const form = document.getElementById('filterForm');
    if (form) {
        form.reset();
        const baseUrl = form.getAttribute('action') || window.location.pathname;
        window.location.href = baseUrl;
    }
}
