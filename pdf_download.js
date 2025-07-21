function exportToPDF() {
    fetch('/api/export_pdf')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to generate PDF');
            }
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'InsightDash_Dashboard.pdf';
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        })
        .catch(error => {
            console.error('PDF export failed:', error);
            showNotification('Failed to generate PDF: ' + error.message);
        });
}

// ... (rest of your existing dashboard.js code)
