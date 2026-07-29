/* Main Utility Script for InterviewAI */

document.addEventListener('DOMContentLoaded', () => {
    // Enable Bootstrap tooltips if present
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

    // Toast Notification helper
    window.showToast = function(message, type = 'info') {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) return;

        const toastId = 'toast-' + Date.now();
        const bgClass = type === 'success' ? 'bg-success' : (type === 'danger' ? 'bg-danger' : 'bg-primary');
        
        const toastHTML = `
            <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0 show" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        toastContainer.insertAdjacentHTML('beforeend', toastHTML);
        
        setTimeout(() => {
            const el = document.getElementById(toastId);
            if (el) el.remove();
        }, 4000);
    };

    // Mark notification read via AJAX and navigate to relevant target URL
    window.markNotificationRead = function(notifId, targetUrl) {
        fetch(`/api/v1/notifications/mark-read/${notifId}`, { method: 'POST' })
            .then(r => r.json())
            .then(res => {
                if (targetUrl && targetUrl !== '#' && targetUrl !== 'javascript:void(0)') {
                    window.location.href = targetUrl;
                }
            })
            .catch(err => {
                if (targetUrl && targetUrl !== '#' && targetUrl !== 'javascript:void(0)') {
                    window.location.href = targetUrl;
                }
            });
    };

    document.querySelectorAll('.mark-read-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const notifId = btn.getAttribute('data-id');
            window.markNotificationRead(notifId);
        });
    });
});
