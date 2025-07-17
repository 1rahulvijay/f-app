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

    function loadDependencies(callback) {
        if (typeof io === 'undefined' && !window.navigator.webdriver) {
            var socketScript = document.createElement('script');
            socketScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.5/socket.io.min.js';
            socketScript.onload = function() {
                console.log('Socket.IO injected successfully');
                loadD3(callback);
            };
            socketScript.onerror = function() {
                console.error('Failed to load Socket.IO');
                loadD3(callback);
            };
            document.head.appendChild(socketScript);
        } else {
            loadD3(callback);
        }
    }

    function loadD3(callback) {
        if (typeof d3 === 'undefined') {
            var d3Script = document.createElement('script');
            d3Script.src = 'https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js';
            d3Script.onload = function() {
                console.log('D3.js injected successfully');
                loadSankey(callback);
            };
            d3Script.onerror = function() {
                console.error('Failed to load D3.js');
                callback(false);
            };
            document.head.appendChild(d3Script);
        } else {
            loadSankey(callback);
        }
    }

    function loadSankey(callback) {
        if (typeof d3.sankey === 'undefined' && window.location.pathname === '/sankey') {
            var sankeyScript = document.createElement('script');
            sankeyScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/d3-sankey/0.12.3/d3-sankey.min.js';
            sankeyScript.onload = function() {
                console.log('d3-sankey injected successfully');
                loadDashboard(callback);
            };
            sankeyScript.onerror = function() {
                console.error('Failed to load d3-sankey');
                callback(false);
            };
            document.head.appendChild(sankeyScript);
        } else {
            loadDashboard(callback);
        }
    }

    function loadDashboard(callback) {
        if (!document.querySelector('script[src="/static/js/dashboard.js"]')) {
            var dashScript = document.createElement('script');
            dashScript.src = '/static/js/dashboard.js';
            dashScript.onload = function() {
                console.log('dashboard.js loaded');
                callback(true);
            };
            dashScript.onerror = function() {
                console.error('Failed to load dashboard.js');
                callback(false);
            };
            document.head.appendChild(dashScript);
        } else {
            callback(true);
        }
    }

    loadDependencies(function(success) {
        if (success && typeof window.initializeCharts === 'function') {
            console.log('Calling initializeCharts');
            window.originalInitializeCharts = window.initializeCharts;
            window.initializeCharts = function() {
                fetch('/api/data')
                    .then(response => response.json())
                    .then(data => {
                        console.log('[DrawCharts] Fetched data:', JSON.stringify(data));
                        const metricCards = document.querySelectorAll('.metric-card p');
                        if (metricCards.length >= 2) {
                            metricCards[0].textContent = data.idCount !== undefined && data.idTrend !== undefined 
                                ? `${data.idCount} (${data.idTrend}%)`
                                : 'ID Count: N/A';
                            metricCards[1].textContent = data.gfCount !== undefined && data.gfTrend !== undefined 
                                ? `${data.gfCount} (${data.gfTrend}%)`
                                : 'GF Count: N/A';
                        } else {
                            console.warn('[DrawCharts] Metric card elements not found');
                        }
                        window.originalInitializeCharts();
                    })
                    .catch(error => {
                        console.error('[DrawCharts] Error fetching data:', error);
                        const metricCards = document.querySelectorAll('.metric-card p');
                        if (metricCards.length >= 2) {
                            metricCards[0].textContent = 'ID Count: Error';
                            metricCards[1].textContent = 'GF Count: Error';
                        }
                        window.originalInitializeCharts();
                    });
            };
            window.initializeCharts();
        } else {
            console.warn('initializeCharts not defined or dependencies failed');
            window.customDashboard.initializationError = true;
        }
    });
})();
"""
        self.page.runJavaScript(
            inject_script,
            lambda _: QTimer.singleShot(40000, self.check_charts_rendered)
        )

    def check_charts_rendered(self):
        js_check = """
(function() {
    const path = window.location.pathname;
    const selectors = path === '/productivity' || path === '/fte' ?
        ['#line-chart svg', '#bar-chart svg', '#area-chart svg'] :
        path === '/sankey' ?
            ['#sankey-chart svg'] :
            ['#line-chart svg', '#bar-chart svg', '#area-chart svg', '#scatter-chart svg'];
    const results = selectors.map(sel => {
        const el = document.querySelector(sel);
        const status = el && el.children.length > 0 ? 'rendered' : 'not rendered';
        console.log(`Selector ${sel} status: ${status}`);
        return el && el.children.length > 0;
    });
    const hasErrors = window.customDashboard?.initializationError || false;
    window.onerror = function(msg, url, lineNo, columnNo, error) {
        window.customDashboard = window.customDashboard || {};
        window.customDashboard.initializationError = true;
        console.error(`Global error: ${msg}, URL: ${url}, Line: ${lineNo}, Column: ${columnNo}, Stack: ${error?.stack || 'N/A'}`);
    };
    console.log('Metric card count:', document.querySelectorAll('.metric-card p').length);
    console.log('Metric card contents:', Array.from(document.querySelectorAll('.metric-card p')).map(el => el.textContent));
    return {
        allRendered: results.every(Boolean),
        hasErrors: hasErrors
    };
})();
"""
        self.page.runJavaScript(js_check, self.handle_charts_check)

    def handle_charts_check(self, result):
        all_rendered = result['allRendered'] and not result['hasErrors']
        if all_rendered:
            print(f"Charts rendered for {self.urls[self.current][1]}")
            self.export_pdf()
        elif self.retry_count < self.max_retries:
            self.retry_count += 1
            print(
                f"Charts not yet rendered for {self.urls[self.current][1]}, retry {self.retry_count}/{self.max_retries}"
            )
            QTimer.singleShot(3000, self.check_charts_rendered)
        else:
            print(
                f"Max retries reached for {self.urls[self.current][1]}. Exporting page as-is."
            )
            self.export_pdf()

    def export_pdf(self):
        filename = f"page_{self.current}.pdf"
        print(f"Exporting to temporary file {filename}")
        js_set_layout = """
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
    """
        self.page.runJavaScript(
            js_set_layout, lambda _: self.page.printToPdf(filename, self.page_layout)
        )
        self.pdf_data.append(filename)
        self.current += 1
        QTimer.singleShot(2000, self.load_next)

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
        ("http://127.0.0.1:5000/sankey", "Sankey Dashboard"),
    ]
    exporter = PDFExporter(urls)
    exporter.start()
    sys.exit(exporter.app.exec_())
