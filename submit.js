// dashboard.js (only the modified submitComment function and related changes)

// Add a base URL configuration at the top of dashboard.js
const BASE_URL = window.location.origin; // Dynamically use the current origin, e.g., http://localhost:8000
// If your Flask app runs under a subpath (e.g., /dashboard), set it explicitly:
// const BASE_URL = window.location.origin + '/dashboard';

// Modified submitComment function
const submitComment = async (event) => {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    
    // Validate required fields
    const commentData = {
        chart_id: formData.get('chart_id'),
        page: window.location.pathname,
        text: formData.get('comments')?.trim(),
        user: formData.get('username') || 'Anonymous',
        reason: formData.get('reason'),
        exclusion: formData.get('exclusion'),
        why: formData.get('why'),
        quick_fix: formData.get('quick_fix'),
        to_do: formData.get('to_do')
    };

    // Check for required fields
    if (!commentData.chart_id || !commentData.page || !commentData.text) {
        console.error('Missing required fields:', commentData);
        alert('Error: Please fill in all required fields (Chart ID, Page, Comment).');
        return;
    }

    if (commentData.text.length > 500) {
        console.error('Comment text too long:', commentData.text.length);
        alert('Error: Comment text is too long (max 500 characters).');
        return;
    }

    try {
        console.log('Submitting comment to:', `${BASE_URL}/api/annotations`);
        console.log('Comment data:', commentData);

        const response = await fetch(`${BASE_URL}/api/annotations`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(commentData)
        });

        console.log('Response status:', response.status);
        const result = await response.json();
        console.log('Response data:', result);

        if (!response.ok) {
            throw new Error(`Failed to submit comment: ${result.error || response.statusText} (${response.status})`);
        }

        alert('Comment added successfully!');
        closeCommentForm();
        fetchComments(commentData.chart_id === 'all-charts' ? 'all-charts' : commentData.chart_id);
        const details = document.getElementById('details');
        if (details && !details.classList.contains('open')) {
            details.classList.add('open');
            switchTab('comments');
        }
    } catch (error) {
        console.error('Error submitting comment:', error);
        alert('Failed to submit comment: ' + error.message);
    }
};

// Ensure the DOMContentLoaded listener includes the updated logic
document.addEventListener('DOMContentLoaded', () => {
    const addCommentsButton = document.querySelector('.header-actions button:nth-child(3)');
    if (addCommentsButton) {
        addCommentsButton.addEventListener('click', async () => {
            const chartId = 'all-charts';
            const container = document.querySelector('#comments-content');
            try {
                const details = document.getElementById('details');
                if (details) {
                    details.classList.add('open');
                    switchTab('comments');
                }
                const commentsLoaded = await fetchComments(chartId, container);
                if (commentsLoaded) {
                    await new Promise(resolve => {
                        const checkTable = () => {
                            const table = container.querySelector('table');
                            if (table) resolve();
                            else requestAnimationFrame(checkTable);
                        };
                        checkTable();
                    });
                    showCommentForm(chartId);
                } else {
                    alert('Comments failed to load. Please try again later.');
                }
            } catch (error) {
                console.error('Error loading comments before showing form:', error);
                alert('Failed to load comments: ' + error.message);
            }
        });
    }

    createTooltip();
    initializeCharts();
});
