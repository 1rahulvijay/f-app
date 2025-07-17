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
(function() {
    window.customDashboard = window.customDashboard || {};

    function loadDependencies(doc, callback) {
        if (typeof doc.defaultView.io === 'undefined' && !doc.defaultView.navigator.webdriver) {
            var socketScript = doc.createElement('script');
            socketScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.5/socket.io.min.js';
            socketScript.onload = function() {
                console.log('Socket.IO injected successfully');
                loadD3(doc, callback);
            };
            socketScript.onerror = function() {
                console.error('Failed to load Socket.IO');
                loadD3(doc, callback);
            };
            doc.head.appendChild(socketScript);
        } else {
            loadD3(doc, callback);
        }
    }

    function loadD3(doc, callback) {
        if (typeof doc.defaultView.d3 === 'undefined') {
            var d3Script = doc.createElement('script');
            d3Script.src = 'https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js';
            d3Script.onload = function() {
                console.log('D3.js injected successfully');
                loadSankey(doc, callback);
            };
            d3Script.onerror = function() {
                console.error('Failed to load D3.js');
                callback(false);
            };
            doc.head.appendChild(d3Script);
        } else {
            loadSankey(doc, callback);
        }
    }

    function loadSankey(doc, callback) {
        if (typeof doc.defaultView.d3?.sankey === 'undefined' && doc.location.pathname === '/sankey') {
            var sankeyScript = doc.createElement('script');
            sankeyScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/d3-sankey/0.12.3/d3-sankey.min.js';
            sankeyScript.onload = function() {
                console.log('d3-sankey injected successfully');
                loadDashboard(doc, callback);
            };
            sankeyScript.onerror = function() {
                console.error('Failed to load d3-sankey');
                callback(false);
            };
            doc.head.appendChild(sankeyScript);
        } else {
            loadDashboard(doc, callback);
        }
    }

    function loadDashboard(doc, callback) {
        if (!doc.querySelector('script[src="/static/js/dashboard.js"]')) {
            var dashScript = doc.createElement('script');
            dashScript.src = '/static/js/dashboard.js';
            dashScript.onload = function() {
                console.log('dashboard.js loaded');
                callback(true);
            };
            dashScript.onerror = function() {
                console.error('Failed to load dashboard.js');
                callback(false);
            };
            doc.head.appendChild(dashScript);
        } else {
            callback(true);
        }
    }

    const iframeConfigs = [
        { id: 'home-iframe', path: '/' },
        { id: 'productivity-iframe', path: '/productivity' },
        { id: 'fte-iframe', path: '/fte' },
        { id: 'sankey-iframe', path: '/sankey' }
    ];

    iframeConfigs.forEach(config => {
        const iframe = document.querySelector(`#${config.id}`) || document.querySelector(`iframe[src="${config.path}"]`);
        if (!iframe || !iframe.contentDocument) {
            console.error(`Iframe ${config.id} not found or inaccessible`);
            window.customDashboard.initializationError = true;
            return;
        }
        const doc = iframe.contentDocument;
        loadDependencies(doc, function(success) {
            if (success && typeof doc.defaultView.initializeCharts === 'function') {
                console.log(`Calling initializeCharts for iframe ${config.id}`);
                doc.defaultView.originalInitializeCharts = doc.defaultView.initializeCharts;
                doc.defaultView.initializeCharts = function() {
                    fetch('/api/data')
                        .then(response => response.json())
                        .then(data => {
                            console.log(`[DrawCharts] Fetched data for ${config.id}:`, JSON.stringify(data));
                            const metricCards = doc.querySelectorAll('.metric-card p');
                            if (metricCards.length >= 2) {
                                metricCards[0].textContent = data.idCount !== undefined && data.idTrend !== undefined 
                                    ? `${data.idCount} (${data.idTrend}%)`
                                    : 'ID Count: N/A';
                                metricCards[1].textContent = data.gfCount !== undefined && data.gfTrend !== undefined 
                                    ? `${data.gfCount} (${data.gfTrend}%)`
                                    : 'GF Count: N/A';
                            } else {
                                console.warn(`[DrawCharts] Metric card elements not found in ${config.id}`);
                            }
                            doc.defaultView.originalInitializeCharts();
                        })
                        .catch(error => {
                            console.error(`[DrawCharts] Error fetching data for ${config.id}:`, error);
                            const metricCards = doc.querySelectorAll('.metric-card p');
                            if (metricCards.length >= 2) {
                                metricCards[0].textContent = 'ID Count: Error';
                                metricCards[1].textContent = 'GF Count: Error';
                            }
                            doc.defaultView.originalInitializeCharts();
                        });
                };
                doc.defaultView.initializeCharts();
            } else {
                console.warn(`initializeCharts not defined or dependencies failed in ${config.id}`);
                window.customDashboard.initializationError = true;
            }
        });
    });
})();
"""
        self.page.runJavaScript(
            inject_script,
            lambda _: QTimer.singleShot(60000, self.check_charts_rendered)
        )

    def check_charts_rendered(self):
        js_check = """
(function() {
    const iframeConfigs = [
        { id: 'home-iframe', selectors: ['#line-chart svg', '#bar-chart svg', '#area-chart svg', '#scatter-chart svg'], path: '/' },
        { id: 'productivity-iframe', selectors: ['#line-chart svg', '#bar-chart svg', '#area-chart svg'], path: '/productivity' },
        { id: 'fte-iframe', selectors: ['#line-chart svg', '#bar-chart svg', '#area-chart svg'], path: '/fte' },
        { id: 'sankey-iframe', selectors: ['#sankey-chart svg'], path: '/sankey' }
    ];
    const results = [];
    let hasErrors = window.customDashboard?.initializationError || false;

    iframeConfigs.forEach(config => {
        const iframe = document.querySelector(`#${config.id}`) || document.querySelector(`iframe[src="${config.path}"]`);
        if (!iframe || !iframe.contentDocument) {
            console.error(`Iframe ${config.id} not found or inaccessible`);
            results.push({ id: config.id, allRendered: false, hasErrors: true });
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
        results.push({
            id: config.id,
            allRendered: selectorResults.every(Boolean),
            hasErrors: hasErrors
        });
    });

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
        all_rendered = all(result['allRendered'] and not result['hasErrors'] for result in results)
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

    def export_pdf(self, iframe_results):
        self.iframe_index = getattr(self, 'iframe_index', 0)
        iframe_configs = [
            {'id': 'home-iframe', 'path': '/', 'name': 'Home Dashboard'},
            {'id': 'productivity-iframe', 'path': '/productivity', 'name': 'Productivity Dashboard'},
            {'id': 'fte-iframe', 'path': '/fte', 'name': 'FTE Dashboard'},
            {'id': 'sankey-iframe', 'path': '/sankey', 'name': 'Sankey Dashboard'}
        ]

        if self.iframe_index >= len(iframe_configs):
            self.iframe_index = 0
            self.current += 1
            QTimer.singleShot(2000, self.load_next)
            return

        config = iframe_configs[self.iframe_index]
        filename = f"page_{self.current}_{self.iframe_index}.pdf"
        print(f"Exporting iframe {config['name']} to {filename}")

        js_set_layout = """
        (function() {
            const iframe = document.querySelector('#%(id)s') || document.querySelector('iframe[src="%(path)s"]');
            if (!iframe || !iframe.contentDocument) {
                console.error('Iframe %(id)s not found or inaccessible');
                return;
            }
            const doc = iframe.contentDocument;
            doc.body.style.margin = '0';
            doc.body.style.padding = '0';
            doc.body.style.width = '100%%';
            doc.body.style.height = '1080px';
            doc.documentElement.style.width = '100%%';
            doc.documentElement.style.height = '1080px';
            doc.body.style.overflow = 'hidden';
            ['header', '.navbar', '.metrics-grid', '.chart-grid', '.metric-card', '.card'].forEach(selector => {
                const elements = doc.querySelectorAll(selector);
                elements.forEach(el => {
                    el.style.margin = '0';
                    el.style.padding = '0';
                    el.style.width = '100%%';
                    el.style.boxSizing = 'border-box';
                });
            });
            doc.querySelectorAll('.card svg').forEach(svg => {
                svg.style.height = 'auto';
                svg.style.maxHeight = '800px';
                svg.style.width = '100%%';
            });
            doc.querySelectorAll('#sankey-chart svg').forEach(svg => {
                svg.style.height = 'auto';
                svg.style.maxHeight = '900px';
                svg.style.width = '100%%';
            });
            doc.querySelectorAll('.metric-card').forEach(card => {
                card.style.height = 'auto';
                card.style.minHeight = '100px';
            });
            doc.querySelectorAll('.metrics-grid').forEach(grid => {
                grid.style.gridTemplateColumns = 'repeat(auto-fit, minmax(300px, 1fr))';
                grid.style.gap = '0';
            });
            doc.querySelectorAll('.chart-grid').forEach(grid => {
                grid.style.gridTemplateColumns = 'repeat(auto-fit, minmax(600px, 1fr))';
                grid.style.gap = '0';
            });
            document.querySelectorAll('iframe').forEach(f => f.style.display = 'none');
            iframe.style.display = 'block';
            iframe.style.width = '1920px';
            iframe.style.height = '1080px';
            iframe.style.position = 'absolute';
            iframe.style.top = '0';
            iframe.style.left = '0';
        })();
        """ % {'id': config['id'], 'path': config['path']}

        self.page.runJavaScript(
            js_set_layout, lambda _: self.page.printToPdf(filename, self.page_layout)
        )
        self.pdf_data.append(filename)
        self.iframe_index += 1
        QTimer.singleShot(2000, lambda: self.export_pdf(iframe_results))

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
        ("http://127.0.0.1:5000/all", "All Dashboards"),
    ]
    exporter = PDFExporter(urls)
    exporter.start()
    sys.exit(exporter.app.exec_())
