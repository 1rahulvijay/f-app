const exportToPDF = async () => {
    try {
        if (!window.jspdf?.jsPDF) throw new Error('jsPDF not loaded');
        if (!window.html2canvas) throw new Error('html2canvas not loaded');

        const { jsPDF } = window.jspdf;
        const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'tabloid' });

        const pages = [
            { path: '/', title: 'Home Dashboard' },
            { path: '/productivity', title: 'Productivity Dashboard' },
            { path: '/fte', title: 'FTE Dashboard' },
            { path: '/sankey', title: 'Sankey Dashboard' }
        ];

        for (let i = 0; i < pages.length; i++) {
            const { path, title } = pages[i];
            const iframe = document.createElement('iframe');
            iframe.style.width = '1280px';
            iframe.style.height = '720px';
            iframe.style.position = 'absolute';
            iframe.style.left = '-9999px';
            iframe.src = path;

            document.body.appendChild(iframe);

            await new Promise((resolve, reject) => {
                iframe.onload = () => {
                    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;

                    // Hide the details container before capturing
                    const detailsContainer = iframeDoc.querySelector('#details');
                    if (detailsContainer) {
                        detailsContainer.classList.remove('open');
                        detailsContainer.style.display = 'none'; // Ensure it's hidden
                    }

                    // Simplify styles by removing color-mix to ensure compatibility with html2canvas
                    const styleSheets = iframeDoc.styleSheets;
                    for (let sheet of styleSheets) {
                        try {
                            const rules = sheet.cssRules || sheet.rules;
                            for (let rule of rules) {
                                if (rule.style && rule.style.background && rule.style.background.includes('color-mix')) {
                                    const theme = iframeDoc.body.className || 'light-theme';
                                    let fallbackColor;
                                    switch (theme) {
                                        case 'light-theme':
                                            fallbackColor = '#5e97f8';
                                            break;
                                        case 'dark-theme':
                                            fallbackColor = '#7db5fb';
                                            break;
                                        case 'corporate-theme':
                                            fallbackColor = '#497ee9';
                                            break;
                                        case 'neutral-theme':
                                            fallbackColor = '#858b98';
                                            break;
                                        default:
                                            fallbackColor = '#5e97f8';
                                    }
                                    rule.style.background = fallbackColor;
                                }
                            }
                        } catch (e) {
                            console.warn('Could not access stylesheet rules:', e);
                        }
                    }

                    // Wait for charts to render
                    const checkCharts = setInterval(() => {
                        const chartContainers = iframeDoc.querySelectorAll('#line-chart, #bar-chart, #area-chart, #scatter-chart, #sankey-chart');
                        const allRendered = Array.from(chartContainers).every(container => container.innerHTML !== '');
                        if (allRendered) {
                            clearInterval(checkCharts);
                            // Double-check that the details container is hidden
                            if (detailsContainer) {
                                detailsContainer.classList.remove('open');
                                detailsContainer.style.display = 'none';
                            }
                            resolve();
                        }
                    }, 500);

                    // Timeout to prevent infinite waiting
                    setTimeout(() => {
                        clearInterval(checkCharts);
                        resolve();
                    }, 10000);
                };
                iframe.onerror = () => reject(new Error(`Failed to load iframe for ${path}`));
            });

            const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
            const canvas = await html2canvas(iframeDoc.body, { scale: 1, useCORS: true });
            const imgData = canvas.toDataURL('image/png');
            const pdfWidth = doc.internal.pageSize.getWidth();
            const pdfHeight = doc.internal.pageSize.getHeight();
            const imgProps = doc.getImageProperties(imgData);
            const imgHeight = (imgProps.height * pdfWidth) / imgProps.width;

            if (i > 0) doc.addPage();
            doc.setFontSize(14);
            doc.text(title, 10, 10);
            doc.addImage(imgData, 'PNG', 10, 20, pdfWidth - 20, Math.min(pdfHeight - 30, imgHeight));

            document.body.removeChild(iframe);
        }

        doc.save('InsightDash_Dashboard.pdf');
    } catch (error) {
        console.error('Error in exportToPDF:', error);
        alert('Failed to export to PDF: ' + error.message);
    }
};
