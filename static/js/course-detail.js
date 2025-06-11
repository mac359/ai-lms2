// Course Detail Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-refresh course data every 30 seconds
    setInterval(function() {
        refreshCourseData();
    }, 30000);

    // Add smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Tab switching with URL hash
    const hash = window.location.hash;
    if (hash) {
        const tab = document.querySelector(`[data-bs-target="${hash}"]`);
        if (tab) {
            const tabInstance = new bootstrap.Tab(tab);
            tabInstance.show();
        }
    }

    // Update URL hash when tabs are clicked
    document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
        tab.addEventListener('shown.bs.tab', function (e) {
            const target = e.target.getAttribute('data-bs-target');
            if (target) {
                window.location.hash = target;
            }
        });
    });

    // Progress bar animations
    animateProgressBars();

    // Initialize card hover effects
    initializeCardEffects();

    // Setup deadline countdowns
    setupDeadlineCountdowns();

    // Initialize search functionality
    initializeSearch();
});

function refreshCourseData() {
    console.log('Refreshing course data...');
    // You can add AJAX calls here to refresh course data
    // For example, fetch new announcements, updated grades, etc.
}

function animateProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(bar => {
        const width = bar.style.width;
        bar.style.width = '0%';
        setTimeout(() => {
            bar.style.width = width;
        }, 100);
    });
}

function initializeCardEffects() {
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

function setupDeadlineCountdowns() {
    const deadlineElements = document.querySelectorAll('[data-deadline]');
    deadlineElements.forEach(element => {
        const deadline = new Date(element.getAttribute('data-deadline'));
        updateCountdown(element, deadline);
        
        // Update countdown every minute
        setInterval(() => {
            updateCountdown(element, deadline);
        }, 60000);
    });
}

function updateCountdown(element, deadline) {
    const now = new Date();
    const timeLeft = deadline - now;
    
    if (timeLeft <= 0) {
        element.textContent = 'Overdue';
        element.classList.add('text-danger');
        return;
    }
    
    const days = Math.floor(timeLeft / (1000 * 60 * 60 * 24));
    const hours = Math.floor((timeLeft % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
    
    let countdownText = '';
    if (days > 0) {
        countdownText = `${days}d ${hours}h`;
    } else if (hours > 0) {
        countdownText = `${hours}h ${minutes}m`;
    } else {
        countdownText = `${minutes}m`;
    }
    
    element.textContent = countdownText;
    
    // Color coding based on urgency
    if (days <= 1) {
        element.classList.add('text-danger');
    } else if (days <= 3) {
        element.classList.add('text-warning');
    } else {
        element.classList.add('text-success');
    }
}

function initializeSearch() {
    const searchInput = document.getElementById('courseSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const cards = document.querySelectorAll('.card');
            
            cards.forEach(card => {
                const text = card.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }
}

// Filter functionality for assignments and quizzes
function filterItems(type, status) {
    const items = document.querySelectorAll(`[data-type="${type}"]`);
    items.forEach(item => {
        if (status === 'all' || item.getAttribute('data-status') === status) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
    
    // Update active filter button
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
}

// Export functions for use in templates
window.courseDetail = {
    filterItems: filterItems,
    refreshCourseData: refreshCourseData,
    updateCountdown: updateCountdown
};

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + 1-6 to switch tabs
    if ((e.ctrlKey || e.metaKey) && e.key >= '1' && e.key <= '6') {
        e.preventDefault();
        const tabIndex = parseInt(e.key) - 1;
        const tabs = document.querySelectorAll('[data-bs-toggle="tab"]');
        if (tabs[tabIndex]) {
            const tabInstance = new bootstrap.Tab(tabs[tabIndex]);
            tabInstance.show();
        }
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        });
    }
});

// Print functionality
function printCourseDetails() {
    window.print();
}

// Share functionality
function shareCourse() {
    if (navigator.share) {
        navigator.share({
            title: document.title,
            url: window.location.href
        });
    } else {
        // Fallback: copy to clipboard
        navigator.clipboard.writeText(window.location.href).then(() => {
            alert('Course URL copied to clipboard!');
        });
    }
}

// Bookmark functionality
function toggleBookmark() {
    const bookmarkBtn = document.getElementById('bookmarkBtn');
    const isBookmarked = bookmarkBtn.classList.contains('active');
    
    if (isBookmarked) {
        bookmarkBtn.classList.remove('active');
        bookmarkBtn.innerHTML = '<i class="far fa-bookmark"></i>';
    } else {
        bookmarkBtn.classList.add('active');
        bookmarkBtn.innerHTML = '<i class="fas fa-bookmark"></i>';
    }
    
    // You can add AJAX call here to save bookmark state
    console.log('Bookmark toggled:', !isBookmarked);
}

// Export additional functions
window.courseDetail.printCourseDetails = printCourseDetails;
window.courseDetail.shareCourse = shareCourse;
window.courseDetail.toggleBookmark = toggleBookmark; 