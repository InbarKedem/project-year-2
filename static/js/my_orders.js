// My Orders Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const filterForm = document.getElementById('filterForm');
    const filterToggle = document.querySelector('.filter-toggle');
    const toggleText = document.getElementById('toggle-text');
    const toggleIcon = document.querySelector('.toggle-icon');
    const toggleAdvancedBtn = document.getElementById('toggleAdvancedBtn');
    const toggleAdvancedText = document.getElementById('toggle-advanced-text');
    const advancedFilters = document.getElementById('advancedFilters');
    const toggleAdvancedIcon = toggleAdvancedBtn ? toggleAdvancedBtn.querySelector('.toggle-icon') : null;
    
    // Check if any advanced filters have values - if so, show them
    const hasAdvancedFilters = checkAdvancedFilters();
    if (hasAdvancedFilters && advancedFilters) {
        advancedFilters.style.display = 'block';
        if (toggleAdvancedText) toggleAdvancedText.textContent = 'Hide Advanced Filters';
        if (toggleAdvancedIcon) toggleAdvancedIcon.textContent = '▲';
    }
    
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
    
    // Toggle advanced filters visibility
    if (toggleAdvancedBtn && advancedFilters) {
        toggleAdvancedBtn.addEventListener('click', function() {
            if (advancedFilters.style.display === 'none') {
                advancedFilters.style.display = 'block';
                toggleAdvancedText.textContent = 'Hide Advanced Filters';
                toggleAdvancedIcon.textContent = '▲';
            } else {
                advancedFilters.style.display = 'none';
                toggleAdvancedText.textContent = 'Show Advanced Filters';
                toggleAdvancedIcon.textContent = '▼';
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

// Check if any advanced filter fields have values
function checkAdvancedFilters() {
    const advancedFields = ['order_code', 'seat_class', 'source_airport', 'dest_airport', 
                           'date_from', 'date_to', 'departure_from', 'departure_to', 
                           'min_price', 'max_price'];
    
    const urlParams = new URLSearchParams(window.location.search);
    return advancedFields.some(field => urlParams.has(field) && urlParams.get(field) !== '');
}

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
