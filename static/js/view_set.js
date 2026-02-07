// view_set.js - Interactive functionality for flashcard set viewer

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all interactive elements
    initFlashcardInteractions();
    initButtonInteractions();
    initProgressAnimation();
    initSetActions();
});

/**
 * Initialize flashcard flip interactions
 */
function initFlashcardInteractions() {
    const flashcards = document.querySelectorAll('.flashcard');
    
    flashcards.forEach(card => {
        // Add click effect to flip cards
        card.addEventListener('click', function(e) {
            // Don't trigger if clicking on buttons or header
            if (!e.target.closest('.card-btn') && !e.target.closest('.card-header')) {
                toggleCardFlip(this);
            }
        });
        
        // Add hover effect to card buttons
        const cardButtons = card.querySelectorAll('.card-btn');
        cardButtons.forEach(btn => {
            btn.addEventListener('mouseenter', function() {
                this.style.transform = 'scale(1.1)';
            });
            
            btn.addEventListener('mouseleave', function() {
                this.style.transform = 'scale(1)';
            });
        });
        
        // Add click handlers for edit/delete buttons
        const editBtn = card.querySelector('.edit-btn');
        const deleteBtn = card.querySelector('.delete-btn');
        
        if (editBtn) {
            editBtn.addEventListener('click', handleEditCard);
        }
        
        if (deleteBtn) {
            deleteBtn.addEventListener('click', handleDeleteCard);
        }
    });
}

/**
 * Toggle flip state of a flashcard
 * @param {HTMLElement} card - The flashcard element
 */
function toggleCardFlip(card) {
    card.classList.toggle('flipped');
    
    // Add a subtle animation effect
    if (card.classList.contains('flipped')) {
        card.style.transform = 'translateY(-8px) rotateX(2deg)';
        setTimeout(() => {
            card.style.transform = 'translateY(-8px)';
        }, 300);
    } else {
        card.style.transform = 'translateY(-8px) rotateX(-2deg)';
        setTimeout(() => {
            card.style.transform = 'translateY(-8px)';
        }, 300);
    }
}

/**
 * Initialize button interactions
 */
function initButtonInteractions() {
    // Add hover effects to action buttons
    const actionButtons = document.querySelectorAll('.btn-icon');
    actionButtons.forEach(btn => {
        btn.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px) rotate(5deg)';
        });
        
        btn.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) rotate(0)';
        });
    });
    
    // Add pulse animation to review button
    const reviewBtn = document.querySelector('.btn-review');
    if (reviewBtn) {
        reviewBtn.addEventListener('mouseenter', function() {
            this.style.animation = 'pulse 1s infinite';
        });
        
        reviewBtn.addEventListener('mouseleave', function() {
            this.style.animation = 'pulse 2s infinite';
        });
    }
}

/**
 * Initialize progress bar animation
 */
function initProgressAnimation() {
    const progressFill = document.getElementById('progress-fill');
    if (progressFill) {
        // Animate the progress bar after a short delay
        setTimeout(() => {
            const currentWidth = progressFill.style.width;
            progressFill.style.width = '0%';
            
            // Force reflow
            progressFill.offsetHeight;
            
            // Animate to the actual width
            setTimeout(() => {
                progressFill.style.width = currentWidth;
            }, 100);
        }, 500);
    }
}

/**
 * Initialize set action buttons (edit, share)
 */
function initSetActions() {
    const editSetBtn = document.getElementById('edit-set-btn');
    const shareSetBtn = document.getElementById('share-set-btn');
    
    if (editSetBtn) {
        editSetBtn.addEventListener('click', handleEditSet);
    }
    
    if (shareSetBtn) {
        shareSetBtn.addEventListener('click', handleShareSet);
    }
}

/**
 * Handle edit card button click
 * @param {Event} e - Click event
 */
function handleEditCard(e) {
    e.stopPropagation(); // Prevent card flip
    const cardId = this.getAttribute('data-card-id');
    
    console.log(`Edit button clicked for card ID: ${cardId}`);
    
    // Show confirmation and redirect to edit page
    if (confirm('Edit this flashcard?')) {
        // In a real app, this would redirect to the edit page
        // window.location.href = `/edit-flashcard/${cardId}`;
        console.log(`Editing card with ID: ${cardId}`);
        
        // For demo purposes, show a message
        showNotification(`Editing card ${cardId}`, 'info');
    }
}

/**
 * Handle delete card button click
 * @param {Event} e - Click event
 */
function handleDeleteCard(e) {
    e.stopPropagation(); // Prevent card flip
    const cardId = this.getAttribute('data-card-id');
    const cardElement = this.closest('.flashcard');
    
    console.log(`Delete button clicked for card ID: ${cardId}`);
    
    // Show confirmation dialog
    if (confirm('Are you sure you want to delete this flashcard?')) {
        // Add delete animation
        cardElement.style.transform = 'scale(0.8)';
        cardElement.style.opacity = '0';
        
        // In a real app, this would make an API call
        setTimeout(() => {
            // Simulate API call
            console.log(`Deleting card with ID: ${cardId}`);
            
            // Remove card from DOM
            cardElement.remove();
            
            // Update card numbers
            updateCardNumbers();
            
            // Update stats
            updateStats();
            
            // Show success message
            showNotification('Flashcard deleted successfully', 'success');
        }, 300);
    }
}

/**
 * Handle edit set button click
 */
function handleEditSet() {
    console.log('Edit set button clicked');
    showNotification('Set edit functionality would open here', 'info');
}

/**
 * Handle share set button click
 */
function handleShareSet() {
    console.log('Share set button clicked');
    
    // Check if Web Share API is available
    if (navigator.share) {
        navigator.share({
            title: document.querySelector('.top-bar h2').textContent,
            text: `Check out my flashcard set: ${document.querySelector('.top-bar h2').textContent}`,
            url: window.location.href,
        })
        .then(() => console.log('Share successful'))
        .catch(error => {
            console.log('Error sharing:', error);
            fallbackShare();
        });
    } else {
        fallbackShare();
    }
}

/**
 * Fallback share method (copy to clipboard)
 */
function fallbackShare() {
    const url = window.location.href;
    navigator.clipboard.writeText(url)
        .then(() => {
            showNotification('Link copied to clipboard!', 'success');
        })
        .catch(err => {
            console.error('Failed to copy: ', err);
            showNotification('Failed to copy link', 'error');
        });
}

/**
 * Update card numbers after deletion
 */
function updateCardNumbers() {
    const cards = document.querySelectorAll('.flashcard');
    cards.forEach((card, index) => {
        const cardNumber = card.querySelector('.card-number');
        if (cardNumber) {
            cardNumber.textContent = `#${index + 1}`;
        }
    });
}

/**
 * Update statistics after changes
 */
function updateStats() {
    const cards = document.querySelectorAll('.flashcard');
    const totalCards = cards.length;
    
    // Update total cards in stats footer
    const statValues = document.querySelectorAll('.stat-value');
    if (statValues.length > 0) {
        statValues[0].textContent = totalCards;
    }
    
    // Update review ready status
    const reviewReady = document.querySelectorAll('.stat-item')[2];
    if (reviewReady) {
        const checkmark = reviewReady.querySelector('.stat-value');
        if (checkmark) {
            checkmark.textContent = totalCards >= 5 ? '✓' : '✗';
        }
    }
    
    // Update progress bar
    const progressFill = document.getElementById('progress-fill');
    if (progressFill) {
        const progressPercentage = Math.min((totalCards / 10) * 100, 100);
        progressFill.style.width = `${progressPercentage}%`;
    }
    
    // Update progress text
    const progressText = document.querySelector('.progress-text');
    if (progressText) {
        const statusSpan = progressText.querySelector('.status-ready, .status-add');
        const countSpan = progressText.querySelector('.progress-count');
        
        if (countSpan) {
            countSpan.textContent = `${totalCards} cards`;
        }
        
        if (statusSpan) {
            if (totalCards >= 5) {
                statusSpan.className = 'status-ready';
                statusSpan.textContent = 'Ready for review!';
            } else {
                statusSpan.className = 'status-add';
                statusSpan.textContent = `Add ${5 - totalCards} more cards for optimal review`;
            }
        }
    }
}

/**
 * Show notification message
 * @param {string} message - Notification message
 * @param {string} type - Notification type (success, error, info)
 */
function showNotification(message, type = 'info') {
    // Remove existing notification
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 1000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        animation: slideIn 0.3s ease-out;
    `;
    
    // Set background color based on type
    const colors = {
        success: '#4CAF50',
        error: '#F44336',
        info: '#2196F3'
    };
    notification.style.backgroundColor = colors[type] || colors.info;
    
    // Add to DOM
    document.body.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    }, 3000);
    
    // Add CSS for animations
    if (!document.querySelector('#notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            @keyframes slideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
}