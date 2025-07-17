import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineView
from PyQt5.QtCore import QUrl, QTimer, QMarginsF, QSize
from PyQt5.QtGui import QPageSize, QPageLayout
import os
from PyPDF2 import PdfMerger
import time


class PDFExporter:
    def __init__(self, urls, output_file="InsightDash_Dashboard.pdf"):
        self.app = QApplication(sys.argv)
        self.urls = urls
        self.output_file = output_file
        self.current = 0
        self.max_retries = 5
        self.retry_count = 0
        self.page = QWebEnginePage()
        self.view = QWebEngineView()
        self.view.setPage(self.page)
        self.view.show()  # Show browser for debugging
        self.pdf_data = []
        self.page.loadFinished.connect(self.handle_load_finished)
        self.page_layout = QPageLayout(
            QPageSize(QPageSize.Tabloid), QPageLayout.Landscape, QMarginsF(5, 5, 5, 5)
        )
        self.view.resize(QSize(1920, 1080))
        self.page.javaScriptConsoleMessage = lambda level, msg, line, source: print(
            f"JS Console [{source}:{line}]: {msg}"
        )

    def start(self):
        self.load_next()

    def load_next(self):
        if self.current < len(self.urls):
            print(f"Loading: {self.urls[self.current][1]}")
            self.retry_count = 0
            self.iframe_index = 0  # Reset iframe index for new page
            self.page.load(QUrl(self.urls[self.current][0]))
        else:
            print("Combining pages into single PDF...")
            self.combine_pdf()
            print("PDF export complete.")
            self.app.quit()

    def handle_load_finished(self, ok):
        if not ok:
            print(f"Failed to load {self.urls[self.current][0]}")
            self.pdf_data.append(None)
            self.current += 1
            self.load_next()
            return

        inject_script = """
function processDocument(doc, context) {
    loadDependencies(doc, function(success) {
        if (success && typeof doc.defaultView.initializeCharts === 'function') {
            console.log(`Calling initializeCharts for ${context}`);
            doc.defaultView.originalInitializeCharts = doc.defaultView.initializeCharts;
            // Mock functions that might show the data container
            ['showDetails', 'openDetails', 'toggleDetails'].forEach(func => {
                doc.defaultView[func] = function() {
                    console.log(`${func} disabled for PDF export`);
                };
            });
            doc.defaultView.initializeCharts = function() {
                fetch('/api/data')
                    .then(response => {
                        if (!response.ok) {
                            console.warn('API not available, using mock data');
                            return {
                                idCount: 100,
                                idTrend: 5,
                                gfCount: 200,
                                gfTrend: -3,
                                lineData: [{ label: 'Jan', value: 30 }, { label: 'Feb', value: 50 }, { label: 'Mar', value: 70 }],
                                barData: [{ label: 'Jan', value: 40 }, { label: 'Feb', value: 60 }, { label: 'Mar', value: 80 }],
                                areaData: [{ label: 'Jan', value: 20 }, { label: 'Feb', value: 40 }, { label: 'Mar', value: 60 }],
                                scatterData: [
                                    { label: 'Jan', total_tf: 10, ocm_overall: 15 },
                                    { label: 'Feb', total_tf: 20, ocm_overall: 25 },
                                    { label: 'Mar', total_tf: 30, ocm_overall: 35 }
                                ]
                            };
                        }
                        return response.json();
                    })
                    .then(data => {
                        console.log(`[DrawCharts] Fetched data for ${context}:`, JSON.stringify(data));
                        const metricCards = doc.querySelectorAll('.metric-card p');
                        if (metricCards.length >= 2) {
                            metricCards[0].textContent = data.idCount !== undefined && data.idTrend !== undefined 
                                ? `${data.idCount} (${data.idTrend}%)`
                                : 'ID Count: N/A';
                            metricCards[1].textContent = data.gfCount !== undefined && data.gfTrend !== undefined 
                                ? `${data.gfCount} (${data.gfTrend}%)`
                                : 'GF Count: N/A';
                        } else {
                            console.warn(`[DrawCharts] Metric card elements not found in ${context}`);
                        }
                        doc.defaultView.originalInitializeCharts();
                        // Re-hide data container after chart initialization
                        ['#data-table', '.data-table', '#details', '.details-container', '.data-container', 
                         '[data-role="details"]', '.details', '[class*="data"]', '[class*="table"]', '[class*="details"]', 
                         '#data-table-container', '.table-container', 'table', '.table-responsive', '.data-tab', '#data-tab'].forEach(selector => {
                            const elements = doc.querySelectorAll(selector);
                            elements.forEach(el => {
                                el.style.display = 'none !important';
                                el.style.visibility = 'hidden !important';
                                el.style.opacity = '0 !important';
                                el.style.height = '0 !important';
                                el.style.width = '0 !important';
                                el.style.overflow = 'hidden !important';
                                el.classList.remove('open', 'active', 'visible', 'show');
                                console.log(`Re-hid element after initializeCharts: ${selector}`);
                            });
                        });
                        // Inject global CSS to ensure data containers and tables remain hidden
                        const style = doc.createElement('style');
                        style.textContent = `
                            #data-table, .data-table, #details, .details-container, .data-container,
                            [data-role="details"], .details, [class*="data"], [class*="table"], [class*="details"],
                            #data-table-container, .table-container, table, .table-responsive, .data-tab, #data-tab {
                                display: none !important;
                                visibility: hidden !important;
                                opacity: 0 !important;
                                height: 0 !important;
                                width: 0 !important;
                                overflow: hidden !important;
                            }
                        `;
                        doc.head.appendChild(style);
                        console.log('Injected global CSS to hide data containers after initializeCharts');
                        // Disable all event listeners to prevent dynamic showing
                        doc.querySelectorAll('*').forEach(el => {
                            el.style.pointerEvents = 'none';
                            el.onclick = null;
                            el.onmouseover = null;
                            el.onmouseout = null;
                            el.onchange = null;
                            el.onfocus = null;
                            el.onkeydown = null;
                            el.onkeyup = null;
                        });
                        // Stop all scripts to prevent further DOM changes
                        doc.querySelectorAll('script').forEach(script => {
                            if (!script.src.includes('socket.io') && !script.src.includes('d3') && !script.src.includes('dashboard.js')) {
                                script.remove();
                                console.log('Removed script to prevent DOM changes');
                            }
                        });
                        // Additional debugging for Productivity Dashboard
                        if (context.includes('productivity')) {
                            console.log(`Productivity Dashboard data container status:`, {
                                dataTable: !doc.querySelector('#data-table') || doc.querySelector('#data-table').style.display === 'none',
                                details: !doc.querySelector('#details') || doc.querySelector('#details').style.display === 'none',
                                dataContainer: !doc.querySelector('.data-container') || doc.querySelector('.data-container').style.display === 'none',
                                dataTab: !doc.querySelector('#data-tab') || doc.querySelector('#data-tab').style.display === 'none',
                                allTableElements: Array.from(doc.querySelectorAll('table, [class*="table"], .data-tab, #data-tab')).map(el => ({
                                    tag: el.tagName,
                                    id: el.id,
                                    class: el.className,
                                    display: el.style.display,
                                    visibility: el.style.visibility
                                }))
                            });
                        }
                    })
                    .catch(error => {
                        console.error(`[DrawCharts] Error fetching data for ${context}:`, error);
                        const metricCards = doc.querySelectorAll('.metric-card p');
                        if (metricCards.length >= 2) {
                            metricCards[0].textContent = 'ID Count: Error';
                            metricCards[1].textContent = 'GF Count: Error';
                        }
                        doc.defaultView.originalInitializeCharts();
                        // Re-hide data container after chart initialization
                        ['#data-table', '.data-table', '#details', '.details-container', '.data-container', 
                         '[data-role="details"]', '.details', '[class*="data"]', '[class*="table"]', '[class*="details"]', 
                         '#data-table-container', '.table-container', 'table', '.table-responsive', '.data-tab', '#data-tab'].forEach(selector => {
                            const elements = doc.querySelectorAll(selector);
                            elements.forEach(el => {
                                el.style.display = 'none !important';
                                el.style.visibility = 'hidden !important';
                                el.style.opacity = '0 !important';
                                el.style.height = '0 !important';
                                el.style.width = '0 !important';
                                el.style.overflow = 'hidden !important';
                                el.classList.remove('open', 'active', 'visible', 'show');
                                console.log(`Re-hid element after initializeCharts: ${selector}`);
                            });
                        });
                        // Inject global CSS to ensure data containers and tables remain hidden
                        const style = doc.createElement('style');
                        style.textContent = `
                            #data-table, .data-table, #details, .details-container, .data-container,
                            [data-role="details"], .details, [class*="data"], [class*="table"], [class*="details"],
                            #data-table-container, .table-container, table, .table-responsive, .data-tab, #data-tab {
                                display: none !important;
                                visibility: hidden !important;
                                opacity: 0 !important;
                                height: 0 !important;
                                width: 0 !important;
                                overflow: hidden !important;
                            }
                        `;
                        doc.head.appendChild(style);
                        console.log('Injected global CSS to hide data containers after initializeCharts (error case)');
                        // Disable all event listeners to prevent dynamic showing
                        doc.querySelectorAll('*').forEach(el => {
                            el.style.pointerEvents = 'none';
                            el.onclick = null;
                            el.onmouseover = null;
                            el.onmouseout = null;
                            el.onchange = null;
                            el.onfocus = null;
                            el.onkeydown = null;
                            el.onkeyup = null;
                        });
                        // Stop all scripts to prevent further DOM changes
                        doc.querySelectorAll('script').forEach(script => {
                            if (!script.src.includes('socket.io') && !script.src.includes('d3') && !script.src.includes('dashboard.js')) {
                                script.remove();
                                console.log('Removed script to prevent DOM changes');
                            }
                        });
                        // Additional debugging for Productivity Dashboard
                        if (context.includes('productivity')) {
                            console.log(`Productivity Dashboard data container status (error case):`, {
                                dataTable: !doc.querySelector('#data-table') || doc.querySelector('#data-table').style.display === 'none',
                                details: !doc.querySelector('#details') || doc.querySelector('#details').style.display === 'none',
                                dataContainer: !doc.querySelector('.data-container') || doc.querySelector('.data-container').style.display === 'none',
                                dataTab: !doc.querySelector('#data-tab') || doc.querySelector('#data-tab').style.display === 'none',
                                allTableElements: Array.from(doc.querySelectorAll('table, [class*="table"], .data-tab, #data-tab')).map(el => ({
                                    tag: el.tagName,
                                    id: el.id,
                                    class: el.className,
                                    display: el.style.display,
                                    visibility: el.style.visibility
                                }))
                            });
                        }
                    });
            };
            doc.defaultView.initializeCharts();
        } else {
            console.warn(`initializeCharts not defined or dependencies failed in ${context}`);
            window.customDashboard.initializationError = true;
            // Ensure data containers are hidden even if initialization fails
            ['#data-table', '.data-table', '#details', '.details-container', '.data-container', 
             '[data-role="details"]', '.details', '[class*="data"]', '[class*="table"]', '[class*="details"]', 
             '#data-table-container', '.table-container', 'table', '.table-responsive', '.data-tab', '#data-tab'].forEach(selector => {
                const elements = doc.querySelectorAll(selector);
                elements.forEach(el => {
                    el.style.display = 'none !important';
                    el.style.visibility = 'hidden !important';
                    el.style.opacity = '0 !important';
                    el.style.height = '0 !important';
                    el.style.width = '0 !important';
                    el.style.overflow = 'hidden !important';
                    el.classList.remove('open', 'active', 'visible', 'show');
                    console.log(`Hid element on initialization failure: ${selector}`);
                });
            });
            const style = doc.createElement('style');
            style.textContent = `
                #data-table, .data-table, #details, .details-container, .data-container,
                [data-role="details"], .details, [class*="data"], [class*="table"], [class*="details"],
                #data-table-container, .table-container, table, .table-responsive, .data-tab, #data-tab {
                    display: none !important;
                    visibility: hidden !important;
                    opacity: 0 !important;
                    height: 0 !important;
                    width: 0 !important;
                    overflow: hidden !important;
                }
            `;
            doc.head.appendChild(style);
            console.log('Injected global CSS to hide data containers on initialization failure');
            // Additional debugging for Productivity Dashboard
            if (context.includes('productivity')) {
                console.log(`Productivity Dashboard data container status (init failure):`, {
                    dataTable: !doc.querySelector('#data-table') || doc.querySelector('#data-table').style.display === 'none',
                    details: !doc.querySelector('#details') || doc.querySelector('#details').style.display === 'none',
                    dataContainer: !doc.querySelector('.data-container') || doc.querySelector('.data-container').style.display === 'none',
                    dataTab: !doc.querySelector('#data-tab') || doc.querySelector('#data-tab').style.display === 'none',
                    allTableElements: Array.from(doc.querySelectorAll('table, [class*="table"], .data-tab, #data-tab')).map(el => ({
                        tag: el.tagName,
                        id: el.id,
                        class: el.className,
                        display: el.style.display,
                        visibility: el.style.visibility
                    }))
                });
            }
        }
    });
}
"""
        self.page.runJavaScript(
            inject_script,
            lambda _: QTimer.singleShot(60000, self.check_charts_rendered),
        )

    def check_charts_rendered(self):
        js_check = """
(function() {
    const iframeConfigs = [
        { id: 'home-iframe', selectors: ['#line-chart svg', '#bar-chart svg', '#area-chart svg', '#scatter-chart svg'], path: '/', name: 'Home Dashboard' },
        { id: 'productivity-iframe', selectors: ['#line-chart svg', '#bar-chart svg', '#area-chart svg'], path: '/productivity', name: 'Productivity Dashboard' },
        { id: 'fte-iframe', selectors: ['#line-chart svg', '#bar-chart svg', '#area-chart svg'], path: '/fte', name: 'FTE Dashboard' },
        { id: 'sankey-iframe', selectors: ['#sankey-chart svg'], path: '/sankey', name: 'Sankey Dashboard' }
    ];

    let results = [];
    let hasErrors = window.customDashboard?.initializationError || false;

    if (window.location.pathname === '/all') {
        iframeConfigs.forEach(config => {
            const iframe = document.querySelector(`#${config.id}`) || document.querySelector(`iframe[src="${config.path}"]`);
            if (!iframe || !iframe.contentDocument) {
                console.error(`Iframe ${config.id} not found or inaccessible`);
                results.push({ id: config.id, name: config.name, allRendered: false, hasErrors: true });
                hasErrors = true;
                return;
            }
            const doc = iframe.contentDocument;
            const selectorResults = config.selectors.map(sel => {
                const el = doc.querySelector(sel);
                const status = el && el.children.length > 0 ? 'rendered' : 'not rendered';
                console.log(`Iframe ${config.id} selector ${sel} status: ${status}`);
                return el && el.children.length > 0;
            });
            console.log(`Iframe ${config.id} metric card count:`, doc.querySelectorAll('.metric-card p').length);
            console.log(`Iframe ${config.id} metric card contents:`, Array.from(doc.querySelectorAll('.metric-card p')).map(el => el.textContent));
            // Additional debugging for Productivity Dashboard
            if (config.path === '/productivity') {
                console.log(`Productivity Dashboard data container status:`, {
                    dataTable: !doc.querySelector('#data-table') || doc.querySelector('#data-table').style.display === 'none',
                    details: !doc.querySelector('#details') || doc.querySelector('#details').style.display === 'none',
                    dataContainer: !doc.querySelector('.data-container') || doc.querySelector('.data-container').style.display === 'none',
                    dataTab: !doc.querySelector('#data-tab') || doc.querySelector('#data-tab').style.display === 'none',
                    allTableElements: Array.from(doc.querySelectorAll('table, [class*="table"], .data-tab, #data-tab')).map(el => ({
                        tag: el.tagName,
                        id: el.id,
                        class: el.className,
                        display: el.style.display,
                        visibility: el.style.visibility
                    }))
                });
            }
            results.push({
                id: config.id,
                name: config.name,
                allRendered: selectorResults.every(Boolean),
                hasErrors: hasErrors
            });
        });
    } else {
        const path = window.location.pathname;
        const selectors = path === '/productivity' || path === '/fte' ?
            ['#line-chart svg', '#bar-chart svg', '#area-chart svg'] :
            path === '/sankey' ?
                ['#sankey-chart svg'] :
                ['#line-chart svg', '#bar-chart svg', '#area-chart svg', '#scatter-chart svg'];
        const selectorResults = selectors.map(sel => {
            const el = document.querySelector(sel);
            const status = el && el.children.length > 0 ? 'rendered' : 'not rendered';
            console.log(`Selector ${sel} status: ${status}`);
            return el && el.children.length > 0;
        });
        console.log('Metric card count:', document.querySelectorAll('.metric-card p').length);
        console.log('Metric card contents:', Array.from(document.querySelectorAll('.metric-card p')).map(el => el.textContent));
        // Additional debugging for Productivity Dashboard
        if (path === '/productivity') {
            console.log(`Productivity Dashboard data container status:`, {
                dataTable: !document.querySelector('#data-table') || document.querySelector('#data-table').style.display === 'none',
                details: !document.querySelector('#details') || document.querySelector('#details').style.display === 'none',
                dataContainer: !document.querySelector('.data-container') || document.querySelector('.data-container').style.display === 'none',
                dataTab: !document.querySelector('#data-tab') || document.querySelector('#data-tab').style.display === 'none',
                allTableElements: Array.from(document.querySelectorAll('table, [class*="table"], .data-tab, #data-tab')).map(el => ({
                    tag: el.tagName,
                    id: el.id,
                    class: el.className,
                    display: el.style.display,
                    visibility: el.style.visibility
                }))
            });
        }
        results.push({
            id: 'main',
            name: 'Main Dashboard',
            allRendered: selectorResults.every(Boolean),
            hasErrors: hasErrors
        });
    }

    window.onerror = function(msg, url, lineNo, columnNo, error) {
        window.customDashboard = window.customDashboard || {};
        window.customDashboard.initializationError = true;
        console.error(`Global error: ${msg}, URL: ${url}, Line: ${lineNo}, Column: ${columnNo}, Stack: ${error?.stack || 'N/A'}`);
    };

    return results;
})();
"""
        self.page.runJavaScript(js_check, self.handle_charts_check)

    def handle_charts_check(self, results):
        all_rendered = all(
            result["allRendered"] and not result["hasErrors"] for result in results
        )
        if all_rendered:
            print(f"Charts rendered for {self.urls[self.current][1]}")
            self.export_pdf(results)
        elif self.retry_count < self.max_retries:
            self.retry_count += 1
            print(
                f"Charts not yet rendered for {self.urls[self.current][1]}, retry {self.retry_count}/{self.max_retries}"
            )
            QTimer.singleShot(5000, self.check_charts_rendered)
        else:
            print(
                f"Max retries reached for {self.urls[self.current][1]}. Exporting page as-is."
            )
            self.export_pdf(results)

    def export_pdf(self, results=None):
        self.iframe_index = getattr(self, "iframe_index", 0)
        is_iframe_mode = self.urls[self.current][0].endswith("/all")
        iframe_configs = [
            {"id": "home-iframe", "path": "/", "name": "Home Dashboard"},
            {
                "id": "productivity-iframe",
                "path": "/productivity",
                "name": "Productivity Dashboard",
            },
            {"id": "fte-iframe", "path": "/fte", "name": "FTE Dashboard"},
            {"id": "sankey-iframe", "path": "/sankey", "name": "Sankey Dashboard"},
        ]

        if is_iframe_mode and self.iframe_index < len(iframe_configs):
            config = iframe_configs[self.iframe_index]
            filename = f"page_{self.current}_{self.iframe_index}.pdf"
            print(f"Exporting iframe {config['name']} to {filename}")

            js_set_layout = """
            (function() {
    // Hide all non-essential elements except charts, metrics, header, and navbar
    document.querySelectorAll('body > *:not(.chart-grid):not(.metrics-grid):not(header):not(.navbar)').forEach(el => {
        el.style.display = 'none !important';
        el.style.visibility = 'hidden !important';
        el.style.opacity = '0 !important';
        el.style.height = '0 !important';
        el.style.width = '0 !important';
        el.style.overflow = 'hidden !important';
        el.classList.remove('open', 'active', 'visible', 'show');
        console.log(`Hid non-essential element: ${el.tagName}${el.id ? '#' + el.id : ''}${el.className ? '.' + el.className : ''}`);
    });
    // Explicitly hide known data container selectors and any potential overrides
    ['#data-table', '.data-table', '#details', '.details-container', '.data-container', 
     '[data-role="details"]', '.details', '[class*="data"]', '[class*="table"]', '[class*="details"]', 
     '#data-table-container', '.table-container', 'table', '.table-responsive', '.data-tab', '#data-tab'].forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => {
            el.style.display = 'none !important';
            el.style.visibility = 'hidden !important';
            el.style.opacity = '0 !important';
            el.style.height = '0 !important';
            el.style.width = '0 !important';
            el.style.overflow = 'hidden !important';
            el.classList.remove('open', 'active', 'visible', 'show');
            console.log(`Hid element: ${selector}`);
        });
    });
    // Add a global CSS rule to ensure data containers and tables remain hidden
    const style = document.createElement('style');
    style.textContent = `
        #data-table, .data-table, #details, .details-container, .data-container,
        [data-role="details"], .details, [class*="data"], [class*="table"], [class*="details"],
        #data-table-container, .table-container, table, .table-responsive, .data-tab, #data-tab {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            height: 0 !important;
            width: 0 !important;
            overflow: hidden !important;
        }
    `;
    document.head.appendChild(style);
    console.log('Injected global CSS to hide data containers and tables');
    // Disable all event listeners to prevent dynamic showing
    document.querySelectorAll('*').forEach(el => {
        el.style.pointerEvents = 'none';
        el.onclick = null;
        el.onmouseover = null;
        el.onmouseout = null;
        el.onchange = null;
        el.onfocus = null;
        el.onkeydown = null;
        el.onkeyup = null;
    });
    // Apply layout adjustments
    document.body.style.margin = '0';
    document.body.style.padding = '0';
    document.body.style.width = '100%';
    document.body.style.height = '1080px';
    document.documentElement.style.width = '100%';
    document.documentElement.style.height = '1080px';
    document.body.style.overflow = 'hidden';
    ['header', '.navbar', '.metrics-grid', '.chart-grid', '.metric-card', '.card'].forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => {
            el.style.margin = '0';
            el.style.padding = '0';
            el.style.width = '100%';
            el.style.boxSizing = 'border-box';
        });
    });
    document.querySelectorAll('.card svg').forEach(svg => {
        svg.style.height = 'auto';
        svg.style.maxHeight = '800px';
        svg.style.width = '100%';
    });
    document.querySelectorAll('#sankey-chart svg').forEach(svg => {
        svg.style.height = 'auto';
        svg.style.maxHeight = '900px';
        svg.style.width = '100%';
    });
    document.querySelectorAll('.metric-card').forEach(card => {
        card.style.height = 'auto';
        card.style.minHeight = '100px';
    });
    document.querySelectorAll('.metrics-grid').forEach(grid => {
        grid.style.gridTemplateColumns = 'repeat(auto-fit, minmax(300px, 1fr))';
        grid.style.gap = '0';
    });
    document.querySelectorAll('.chart-grid').forEach(grid => {
        grid.style.gridTemplateColumns = 'repeat(auto-fit, minmax(600px, 1fr))';
        grid.style.gap = '0';
    });
    // Debug DOM state
    console.log('Data table hidden:', !document.querySelector('#data-table') || document.querySelector('#data-table').style.display === 'none');
    console.log('Details container hidden:', !document.querySelector('#details') || document.querySelector('#details').style.display === 'none');
    console.log('Data container hidden:', !document.querySelector('.data-container') || document.querySelector('.data-container').style.display === 'none');
    console.log('Data tab hidden:', !document.querySelector('#data-tab') || document.querySelector('#data-tab').style.display === 'none');
    console.log('Non-essential elements hidden:', Array.from(document.querySelectorAll('body > *:not(.chart-grid):not(.metrics-grid):not(header):not(.navbar)')).map(el => `${el.tagName}${el.id ? '#' + el.id : ''}${el.className ? '.' + el.className : ''}`));
    console.log('Table elements:', Array.from(document.querySelectorAll('table, [class*="table"], #data-tab, .data-tab')).map(el => ({
        tag: el.tagName,
        id: el.id,
        class: el.className,
        display: el.style.display,
        visibility: el.style.visibility
    })));
    console.log('DOM snapshot:', document.body.outerHTML.substring(0, 2000));
})();
            """ % {
                "id": config["id"],
                "path": config["path"],
            }

            def after_layout(_):
                # Increased delay to ensure JavaScript execution and rendering
                QTimer.singleShot(
                    3000, lambda: self.page.printToPdf(filename, self.page_layout)
                )

            self.page.runJavaScript(js_set_layout, after_layout)
            self.pdf_data.append(filename)
            self.iframe_index += 1
            QTimer.singleShot(5000, lambda: self.export_pdf(results))
        else:
            filename = f"page_{self.current}.pdf"
            print(f"Exporting to temporary file {filename}")
            js_set_layout = """
            (function() {
                // Hide all non-essential elements except charts, metrics, header, and navbar
                document.querySelectorAll('body > *:not(.chart-grid):not(.metrics-grid):not(header):not(.navbar)').forEach(el => {
                    el.style.display = 'none !important';
                    el.style.visibility = 'hidden !important';
                    el.classList.remove('open', 'active', 'visible');
                    console.log(`Hid non-essential element: ${el.tagName}${el.id ? '#' + el.id : ''}${el.className ? '.' + el.className : ''}`);
                });
                // Explicitly hide known data container selectors
                ['#data-table', '.data-table', '#details', '.details-container', '.data-container', '[data-role="details"]', '.details'].forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        el.style.display = 'none !important';
                        el.style.visibility = 'hidden !important';
                        el.classList.remove('open', 'active', 'visible');
                        console.log(`Hid element: ${selector}`);
                    });
                });
                // Disable all event listeners to prevent dynamic showing
                document.querySelectorAll('*').forEach(el => {
                    el.style.pointerEvents = 'none';
                    el.onclick = null;
                    el.onmouseover = null;
                    el.onmouseout = null;
                });
                // Apply layout adjustments
                document.body.style.margin = '0';
                document.body.style.padding = '0';
                document.body.style.width = '100%';
                document.body.style.height = '1080px';
                document.documentElement.style.width = '100%';
                document.documentElement.style.height = '1080px';
                document.body.style.overflow = 'hidden';
                ['header', '.navbar', '.metrics-grid', '.chart-grid', '.metric-card', '.card'].forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        el.style.margin = '0';
                        el.style.padding = '0';
                        el.style.width = '100%';
                        el.style.boxSizing = 'border-box';
                    });
                });
                document.querySelectorAll('.card svg').forEach(svg => {
                    svg.style.height = 'auto';
                    svg.style.maxHeight = '800px';
                    svg.style.width = '100%';
                });
                document.querySelectorAll('#sankey-chart svg').forEach(svg => {
                    svg.style.height = 'auto';
                    svg.style.maxHeight = '900px';
                    svg.style.width = '100%';
                });
                document.querySelectorAll('.metric-card').forEach(card => {
                    card.style.height = 'auto';
                    card.style.minHeight = '100px';
                });
                document.querySelectorAll('.metrics-grid').forEach(grid => {
                    grid.style.gridTemplateColumns = 'repeat(auto-fit, minmax(300px, 1fr))';
                    grid.style.gap = '0';
                });
                document.querySelectorAll('.chart-grid').forEach(grid => {
                    grid.style.gridTemplateColumns = 'repeat(auto-fit, minmax(600px, 1fr))';
                    grid.style.gap = '0';
                });
                // Debug DOM state
                console.log('Data table hidden:', !document.querySelector('#data-table') || document.querySelector('#data-table').style.display === 'none');
                console.log('Details container hidden:', !document.querySelector('#details') || document.querySelector('#details').style.display === 'none');
                console.log('Data container hidden:', !document.querySelector('.data-container') || document.querySelector('.data-container').style.display === 'none');
                console.log('Non-essential elements hidden:', Array.from(document.querySelectorAll('body > *:not(.chart-grid):not(.metrics-grid):not(header):not(.navbar)')).map(el => `${el.tagName}${el.id ? '#' + el.id : ''}${el.className ? '.' + el.className : ''}`));
                // Log DOM snapshot (limited to avoid overflow)
                console.log('DOM snapshot:', document.body.outerHTML.substring(0, 2000));
            })();
            """

            def after_layout(_):
                # Increased delay to ensure JavaScript execution and rendering
                QTimer.singleShot(
                    3000, lambda: self.page.printToPdf(filename, self.page_layout)
                )

            self.page.runJavaScript(js_set_layout, after_layout)
            self.pdf_data.append(filename)
            self.current += 1
            self.iframe_index = 0
            QTimer.singleShot(5000, self.load_next)

    def combine_pdf(self):
        merger = PdfMerger()
        for i, temp_file in enumerate(self.pdf_data):
            if temp_file and os.path.exists(temp_file):
                print(f"Adding {temp_file} to final PDF")
                merger.append(temp_file)
            else:
                print(f"Skipping page {i} due to load or render failure")

        if merger.pages:
            merger.write(self.output_file)
            print(f"Combined PDF saved as {self.output_file}")
        else:
            print("No pages were successfully rendered. PDF not created.")

        merger.close()
        self.page.triggerAction(QWebEnginePage.Stop)
        self.view.close()
        time.sleep(5)

        for temp_file in self.pdf_data:
            if temp_file and os.path.exists(temp_file):
                for attempt in range(5):
                    try:
                        os.remove(temp_file)
                        print(f"Deleted temporary file {temp_file}")
                        break
                    except Exception as e:
                        print(
                            f"Failed to delete temporary file {temp_file} (attempt {attempt + 1}/5): {e}"
                        )
                        time.sleep(3)
                    if attempt == 4:
                        print(
                            f"Max deletion attempts reached for {temp_file}, leaving file intact"
                        )


if __name__ == "__main__":
    urls = [
        ("http://127.0.0.1:5000/", "Home Dashboard"),
        ("http://127.0.0.1:5000/productivity", "Productivity Dashboard"),
        ("http://127.0.0.1:5000/fte", "FTE Dashboard"),
    ]
    exporter = PDFExporter(urls)
    exporter.start()
    sys.exit(exporter.app.exec_())
