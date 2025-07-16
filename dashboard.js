// dashboard.js

const themes = ['light-theme', 'dark-theme', 'corporate-theme', 'neutral-theme'];
let currentTheme = localStorage.getItem('theme') || 'light-theme';
document.body.className = currentTheme;

const chartConfig = {
    defaultWidth: 450,
    defaultHeight: 300,
    margin: { top: 20, right: 2, bottom: 20, left: 2 },
    animationDuration: 6000,
    mobileBreakpoint: 1366,
    resolutions: {
        '1366': { height: 220, fontScale: 0.9 },
        '1920': { height: 300, fontScale: 1 },
        '2560': { height: 340, fontScale: 1.1 },
        '3440': { height: 380, fontScale: 1.2 },
        '3840': { height: 420, fontScale: 1.3 }
    }
};

const getCSSVariable = (variable) =>
    getComputedStyle(document.documentElement).getPropertyValue(variable).trim();

const getResponsiveDimensions = (containerId) => {
    const container = document.querySelector(containerId);
    const screenWidth = window.innerWidth;
    let width = container ? Math.max(container.clientWidth - 40, chartConfig.defaultWidth) : chartConfig.defaultWidth;

    // Fix: Correctly use chartConfig.defaultHeight instead of container.defaultHeight
    let height = containerId === '#sankey-chart' ? Math.min(window.innerHeight * 0.8, 600) : chartConfig.defaultHeight;
    let fontScale = 1;

    for (let res in chartConfig.resolutions) {
        if (screenWidth <= parseInt(res)) {
            if (containerId !== '#sankey-chart') {
                height = chartConfig.resolutions[res].height;
            }
            fontScale = chartConfig.resolutions[res].fontScale;
            break;
        }
    }

    return { width, height, fontScale };
};

const fetchData = async () => {
    try {
        const path = window.location.pathname;
        const endpoint = path === '/productivity' ? '/api/productivity_data' :
            path === '/fte' ? '/api/fte_data' :
                path === '/sankey' ? '/api/sankey_data' :
                    '/api/data';

        const response = await fetch(endpoint, { cache: 'no-store' });
        if (!response.ok) throw new Error(`Network response was not ok: ${response.status}`);

        const data = await response.json();
        console.log('Fetched data:', data);

        if (path !== '/sankey' && data.metrics?.current_metrics) {
            const metrics = data.metrics.current_metrics;
            const updateMetric = (id, value, trend, percentChange) => {
                const el = document.getElementById(id);
                if (el) el.innerHTML = `
                    ${value}
                    <span class="${trend === '↑' ? 'trend-up' : 'trend-down'}">
                        ${trend} (${percentChange?.toFixed(2)}%)
                    </span>`;
            };

            if (path === '/productivity') {
                updateMetric('metric-tasks-completed', metrics.tasks_completed, metrics.trends.tasks_completed_trend, metrics.trends.tasks_completed_percent_change);
                updateMetric('metric-avg-completion-time', metrics.avg_completion_time, metrics.trends.avg_completion_time_trend, metrics.trends.avg_completion_time_percent_change);
                updateMetric('metric-efficiency-rate', `${metrics.efficiency_rate}%`, metrics.trends.efficiency_rate_trend, metrics.trends.efficiency_rate_percent_change);
            } else if (path === '/fte') {
                updateMetric('metric-total-fte', metrics.total_fte, metrics.trends.total_fte_trend, metrics.trends.total_fte_percent_change);
                updateMetric('metric-utilization', `${metrics.utilization}%`, metrics.trends.utilization_trend, metrics.trends.utilization_percent_change);
                updateMetric('metric-overtime-hours', metrics.overtime_hours, metrics.trends.overtime_hours_trend, metrics.trends.overtime_hours_percent_change);
            } else {
                updateMetric('metric-count-id', metrics.count_id, metrics.trends.count_id_trend, metrics.trends.count_id_percent_change);
                updateMetric('metric-count-gf', metrics.count_gf, metrics.trends.count_gf_trend, metrics.trends.count_gf_percent_change);
                updateMetric('metric-count-gfc', metrics.count_gfc, metrics.trends.count_gfc_trend, metrics.trends.count_gfc_percent_change);
            }
        }

        return data;
    } catch (error) {
        console.error('Error fetching data:', error);
        // Improvement: Display error on UI
        ['#line-chart', '#bar-chart', '#area-chart', '#scatter-chart', '#sankey-chart'].forEach(selector => {
            const container = document.querySelector(selector);
            if (container) {
                container.innerHTML = `<div class="error">Failed to load data: ${error.message}</div>`;
            }
        });
        return {
            lineData: [],
            barData: [],
            areaData: [],
            scatterData: [],
            nodes: [],
            links: [],
            metrics: {
                current_metrics: {
                    count_id: 0, count_gf: 0, count_gfc: 0,
                    tasks_completed: 0, avg_completion_time: 0, efficiency_rate: 0,
                    total_fte: 0, utilization: 0, overtime_hours: 0,
                    trends: {
                        count_id_trend: '↔', count_id_percent_change: 0,
                        count_gf_trend: '↔', count_gf_percent_change: 0,
                        count_gfc_trend: '↔', count_gfc_percent_change: 0,
                        tasks_completed_trend: '↔', tasks_completed_percent_change: 0,
                        avg_completion_time_trend: '↔', avg_completion_time_percent_change: 0,
                        efficiency_rate_trend: '↔', efficiency_rate_percent_change: 0,
                        total_fte_trend: '↔', total_fte_percent_change: 0,
                        utilization_trend: '↔', utilization_percent_change: 0,
                        overtime_hours_trend: '↔', overtime_hours_percent_change: 0
                    }
                }
            }
        };
    }
};

// Theme and UI Controls
function cycleTheme() {
    const index = (themes.indexOf(currentTheme) + 1) % themes.length;
    currentTheme = themes[index];
    document.body.className = currentTheme;
    localStorage.setItem('theme', currentTheme);
    refreshCharts();
}

const closeDetails = () => {
    const details = document.getElementById('details');
    if (details) details.classList.remove('open');
};

const switchTab = (id) => {
    document.querySelectorAll('.tab, .tab-content').forEach(el => el.classList.remove('active'));
    const tab = document.querySelector(`[onclick="switchTab('${id}')"]`);
    const content = document.getElementById(id);
    if (tab) tab.classList.add('active');
    if (content) content.classList.add('active');
};

// dashboard.js (appended logic)

function toggleFocusMode() {
    document.body.classList.toggle('focus-mode');
    setTimeout(() => {
        window.dispatchEvent(new Event('resize'));
        drawCharts();
    }, 200);
}

function applyDynamicGridLayout() {
    const grid = document.querySelector('.chart-grid');
    if (!grid) return;
    grid.classList.add('dynamic-layout');
    grid.classList.remove('grid-3', 'grid-4');
    const chartCount = grid.querySelectorAll('.card').length;
    if (chartCount === 4) {
        grid.classList.add('grid-4');
    } else if (chartCount === 3) {
        grid.classList.add('grid-3');
    }
}

// // Call after charts rendered
// const originalDrawCharts = drawCharts;
// drawCharts = async () => {
//     await originalDrawCharts();
//     applyDynamicGridLayout();
// };

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

                    // Fix: Simplify styles by removing color-mix to ensure compatibility with html2canvas
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
                            resolve();
                        }
                    }, 500);

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

const exportToExcel = () => {
    try {
        const rows = document.querySelectorAll('#data-table-content tr');
        if (rows.length <= 1) throw new Error('No data to export');
        const csv = [...rows].map(row =>
            [...row.children].map(cell => `"${cell.textContent.replace(/"/g, '""')}"`).join(',')
        ).join('\n');
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'dashboard_data.csv';
        link.click();
        URL.revokeObjectURL(link.href);
    } catch (error) {
        console.error('Error exporting to CSV:', error);
        alert('Failed to export to CSV. Please ensure the table has data and try again.');
    }
};


const createChartBase = (svg, width, height, x, y, fontScale) => {
    const { margin } = chartConfig;
    svg.append('g')
        .attr('class', 'grid')
        .attr('transform', `translate(0, ${height - margin.bottom})`)
        .call(d3.axisBottom(x).tickSize(-height + margin.top + margin.bottom).tickFormat(''))
        .selectAll('line')
        .attr('stroke', getCSSVariable('--grid'))
        .attr('stroke-opacity', 0.2)
        .attr('stroke-dasharray', '2,2');
    svg.append('g')
        .attr('class', 'grid')
        .attr('transform', `translate(${margin.left}, 0)`)
        .call(d3.axisLeft(y).tickSize(-width + margin.left + margin.right).tickFormat(''))
        .selectAll('line')
        .attr('stroke', getCSSVariable('--grid'))
        .attr('stroke-opacity', 0.2)
        .attr('stroke-dasharray', '2,2');
    svg.append('g')
        .attr('class', 'x-axis')
        .attr('transform', `translate(0, ${height - margin.bottom})`)
        .call(d3.axisBottom(x)
            .ticks(Math.min(10, x.domain().length))
            .tickFormat((d, i) => i % (Math.ceil(x.domain().length / 6)) === 0 ? d : '')
            .tickPadding(6))
        .selectAll('text')
        .attr('fill', getCSSVariable('--fg'))
        .style('font-size', `${10 * fontScale}px`)
        .attr('transform', window.innerWidth <= chartConfig.mobileBreakpoint ? 'rotate(-45)' : 'rotate(0)')
        .style('text-anchor', window.innerWidth <= chartConfig.mobileBreakpoint ? 'end' : 'middle')
        .selectAll('line, path')
        .attr('stroke', getCSSVariable('--fg'))
        .attr('stroke-width', 0.8)
        .attr('stroke-opacity', 0.7);
    svg.append('g')
        .attr('class', 'y-axis')
        .attr('transform', `translate(${margin.left}, 0)`)
        .call(d3.axisLeft(y).ticks(5).tickFormat(d => d.toFixed(0)))
        .selectAll('text')
        .attr('fill', getCSSVariable('--fg'))
        .style('font-size', `${10 * fontScale}px`)
        .selectAll('line, path')
        .attr('stroke', getCSSVariable('--fg'))
        .attr('stroke-width', 0.8)
        .attr('stroke-opacity', 0.7);
};

const createGradient = (svg, id, colorStart, colorEnd) => {
    const defs = svg.append('defs');
    const gradient = defs.append('linearGradient')
        .attr('id', id)
        .attr('x1', '0%')
        .attr('y1', '0%')
        .attr('x2', '0%')
        .attr('y2', '100%');
    gradient.append('stop')
        .attr('offset', '0%')
        .style('stop-color', colorStart)
        .style('stop-opacity', 0.6);
    gradient.append('stop')
        .attr('offset', '100%')
        .style('stop-color', colorEnd)
        .style('stop-opacity', 0.2);
    return `url(#${id})`;
};

const createEffects = (svg) => {
    const defs = svg.append('defs');
    const shadow = defs.append('filter').attr('id', 'drop-shadow').attr('height', '130%');
    shadow.append('feDropShadow')
        .attr('dx', 1)
        .attr('dy', 1)
        .attr('stdDeviation', 3)
        .attr('flood-opacity', 0.4);
    const glow = defs.append('filter').attr('id', 'glow');
    glow.append('feGaussianBlur').attr('stdDeviation', '3').attr('result', 'coloredBlur');
    const feMerge = glow.append('feMerge');
    feMerge.append('feMergeNode').attr('in', 'coloredBlur');
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic');
};

const createLegend = (svg, width, color, text, fontScale) => {
    const legend = svg.append('g')
        .attr('class', 'legend')
        .attr('transform', `translate(${width - chartConfig.margin.right - 100}, ${chartConfig.margin.top - 40})`)
        .attr('opacity', 0);
    legend.append('rect')
        .attr('width', 12)
        .attr('height', 12)
        .attr('fill', color)
        .attr('filter', 'url(#glow)');
    legend.append('text')
        .attr('x', 30)
        .attr('y', 10)
        .attr('fill', getCSSVariable('--fg'))
        .style('font-size', `${12 * fontScale}px`)
        .text(text);
    legend.transition()
        .duration(800)
        .delay(chartConfig.animationDuration / 2)
        .attr('opacity', 1);
    return legend;
};

const createScatterLegend = (svg, width, colors, fontScale) => {
    const legend = svg.append('g')
        .attr('class', 'legend')
        .attr('transform', `translate(${width - chartConfig.margin.right - 220}, ${chartConfig.margin.top - 40})`)
        .attr('opacity', 0);
    const items = [
        { text: 'Total TF', color: colors[0] },
        { text: 'OCM Overall', color: colors[1] }
    ];
    const legendItems = legend.selectAll('.legend-item')
        .data(items)
        .enter()
        .append('g')
        .attr('class', 'legend-item')
        .attr('transform', (d, i) => `translate(${i * 140}, 0)`)
        .style('cursor', 'pointer');
    legendItems.append('rect')
        .attr('width', 12)
        .attr('height', 12)
        .attr('fill', d => d.color)
        .attr('filter', 'url(#glow)');
    legendItems.append('text')
        .attr('x', 30)
        .attr('y', 10)
        .attr('fill', getCSSVariable('--fg'))
        .style('font-size', `${12 * fontScale}px`)
        .text(d => d.text);

    legend.transition()
        .duration(800)
        .delay(chartConfig.animationDuration / 2)
        .attr('opacity', 1);
    return { tfLegend: legendItems.filter((d, i) => i === 0), ocmLegend: legendItems.filter((d, i) => i === 1) };
};

// Improvement: Add timeout to prevent permanent rendering lock
let isRendering = false;
let renderingTimeout = null;

const drawCharts = async () => {
    if (isRendering) {
        console.log('[DrawCharts] Rendering in progress, skipping');
        return;
    }
    isRendering = true;
    renderingTimeout = setTimeout(() => {
        isRendering = false; // Reset after 10 seconds to prevent permanent lock
        console.warn('[DrawCharts] Rendering took too long, resetting isRendering flag');
    }, 10000);

    console.log(`[DrawCharts] Starting chart rendering for path: ${window.location.pathname}`);
    try {
        const data = await fetchData();
        const primaryColorStart = getCSSVariable('--chart-gradient-start');
        const primaryColorEnd = getCSSVariable('--chart-gradient-end');

        const chartConfigs = {
            '/': [
                { id: '#line-chart', data: data.lineData, title: 'ID Count Trend', color: primaryColorStart, type: 'line' },
                { id: '#bar-chart', data: data.barData, title: 'GF Count by Month', color: primaryColorStart, type: 'bar' },
                { id: '#area-chart', data: data.areaData, title: 'GFC Count Trend', color: primaryColorStart, type: 'lollipop' },
                { id: '#scatter-chart', data: data.scatterData, title: 'ID Distribution', colors: ['#ff5555', '#5555ff'], type: 'scatter' }
            ],
            '/productivity': [
                { id: '#line-chart', data: data.lineData, title: 'Tasks Completed Trend', color: primaryColorStart, type: 'line' },
                { id: '#bar-chart', data: data.barData, title: 'Avg Completion Time by Month', color: primaryColorStart, type: 'bar' },
                { id: '#area-chart', data: data.areaData, title: 'Efficiency Rate Trend', color: primaryColorStart, type: 'lollipop' }
            ],
            '/fte': [
                { id: '#line-chart', data: data.lineData, title: 'Total FTE Trend', color: primaryColorStart, type: 'line' },
                { id: '#bar-chart', data: data.barData, title: 'Utilization by Month', color: primaryColorStart, type: 'bar' },
                { id: '#area-chart', data: data.areaData, title: 'Overtime Hours Trend', color: primaryColorStart, type: 'lollipop' }
            ],
            '/sankey': [
                { id: '#sankey-chart', data: data, title: 'Client Flow Sankey Diagram', color: primaryColorStart, type: 'sankey' }
            ]
        };

        const charts = chartConfigs[window.location.pathname] || chartConfigs['/'];

        console.log(`[DrawCharts] Chart configurations:`, charts);

        ['#line-chart', '#bar-chart', '#area-chart', '#scatter-chart', '#sankey-chart'].forEach(selector => {
            const container = document.querySelector(selector);
            if (container) {
                container.innerHTML = '';
            }
        });

        for (const chart of charts) {
            console.log(`[DrawCharts] Rendering chart: ${chart.title} at ${chart.id}`);
            try {
                const container = document.querySelector(chart.id);
                if (!container) {
                    console.warn(`Chart container ${chart.id} not found`);
                    continue;
                }

                switch (chart.type) {
                    case 'line':
                        drawLineChart(chart.id, chart.data, chart.title, chart.color, primaryColorEnd);
                        break;
                    case 'bar':
                        const percentChange = window.location.pathname === '/productivity' ?
                            data.metrics.current_metrics.trends.avg_completion_time_percent_change :
                            window.location.pathname === '/fte' ?
                                data.metrics.current_metrics.trends.utilization_percent_change :
                                data.metrics.current_metrics.trends.count_gf_percent_change;
                        drawBarChart(chart.id, chart.data, chart.title, chart.color, primaryColorEnd, percentChange);
                        break;
                    case 'lollipop':
                        drawLollipopChart(chart.id, chart.data, chart.title, chart.color, primaryColorEnd);
                        break;
                    case 'scatter':
                        drawScatterChart(chart.id, chart.data, chart.title, chart.colors[0], chart.colors[1]);
                        break;
                    case 'sankey':
                        drawSankeyChart(chart.id, chart.data, chart.title, chart.color);
                        break;
                    default:
                        console.warn(`Unknown chart type: ${chart.type}`);
                }
            } catch (error) {
                console.error(`Error rendering chart ${chart.title}:`, error);
                const container = document.querySelector(chart.id);
                if (container) {
                    container.innerHTML = `<div class="error">Error loading chart: ${error.message}</div>`;
                }
            }
        }
    } finally {
        isRendering = false;
        clearTimeout(renderingTimeout);
    }
};

const areChartContainersReady = () => {
    const path = window.location.pathname;
    const selectors = path === '/productivity' || path === '/fte' ?
        ['#line-chart', '#bar-chart', '#area-chart'] :
        path === '/sankey' ?
            ['#sankey-chart'] :
            ['#line-chart', '#bar-chart', '#area-chart', '#scatter-chart'];
    return selectors.every(id => document.querySelector(id));
};

const refreshCharts = async () => {
    if (isRendering) return;
    ['#line-chart', '#bar-chart', '#area-chart', '#scatter-chart', '#sankey-chart'].forEach(selector => {
        const container = document.querySelector(selector);
        if (container) container.innerHTML = '';
    });
    drawCharts();
};

const drawLineChart = (container, data, title, color, colorEnd) => {
    if (!data?.length) {
        d3.select(container).append('text')
            .attr('x', '50%')
            .attr('y', '50%')
            .attr('text-anchor', 'middle')
            .attr('fill', getCSSVariable('--fg'))
            .text('No data available');
        return;
    }
    const { width, height, fontScale } = getResponsiveDimensions(container);
    const svg = d3.select(container).append('svg')
        .attr('viewBox', `0 0 ${width} ${height}`)
        .style('font-size', `${12 * fontScale}px`);
    const { margin } = chartConfig;
    const x = d3.scalePoint().domain(data.map(d => d.label)).range([margin.left, width - margin.right]);
    const y = d3.scaleLinear().domain([0, d3.max(data, d => d.value) * 1.2]).nice().range([height - margin.bottom, margin.top]);

    createChartBase(svg, width, height, x, y, fontScale);
    createEffects(svg);
    const gradientId = `lineGradient-${Math.random().toString(36).substr(2, 9)}`;
    const fill = createGradient(svg, gradientId, color, colorEnd);

    const area = d3.area().x(d => x(d.label)).y0(height - margin.bottom).y1(d => y(d.value)).curve(d3.curveMonotoneX);
    svg.append('path').datum(data).attr('fill', fill).attr('d', area).attr('opacity', 0)
        .transition().duration(chartConfig.animationDuration).ease(d3.easeElastic).attr('opacity', 0.8);

    const line = d3.line().x(d => x(d.label)).y(d => y(d.value)).curve(d3.curveMonotoneX);
    svg.append('path').datum(data).attr('stroke', color).attr('stroke-width', 3).attr('fill', 'none').attr('d', line)
        .attr('stroke-dasharray', function () { return this.getTotalLength(); })
        .attr('stroke-dashoffset', function () { return this.getTotalLength(); })
        .transition().duration(chartConfig.animationDuration).ease(d3.easeElastic)
        .attr('stroke-dashoffset', 0);

    svg.selectAll('circle').data(data).enter().append('circle')
        .attr('cx', d => x(d.label)).attr('cy', d => y(d.value)).attr('r', 0).attr('fill', color)
        .attr('stroke', '#fff').attr('stroke-width', 2).style('cursor', 'pointer')
        .attr('filter', 'url(#glow)')
        .on('mouseover', (event, d) => {
            const tooltipWidth = d3.select('.tooltip').node()?.offsetWidth || 200;
            const xPos = Math.min(event.pageX + 10, window.innerWidth - tooltipWidth - 20);
            d3.select('.tooltip').style('display', 'block')
                .html(`<b>${d.label}</b><br>Value: ${d.value?.toFixed(1) || 'N/A'}<br>Trend: ${d.value > (data[data.indexOf(d) - 1]?.value || 0) ? '↑' : '↓'}`)
                .style('left', `${xPos}px`).style('top', `${Math.max(event.pageY - 40, 20)}px`)
                .transition().duration(200).ease(d3.easeElastic).style('opacity', 0.9);
        })
        .on('mouseout', () => d3.select('.tooltip').transition().duration(300).ease(d3.easeElastic).style('opacity', 0)
            .on('end', () => d3.select('.tooltip').style('display', 'none')))
        .transition().duration(chartConfig.animationDuration / 2).delay((d, i) => i * 300).ease(d3.easeElastic).attr('r', 6);

    svg.selectAll('.data-label').data(data).enter().append('text')
        .attr('class', 'data-label')
        .attr('x', d => x(d.label))
        .attr('y', d => y(d.value) - 10)
        .attr('fill', getCSSVariable('--fg'))
        .attr('text-anchor', 'middle')
        .style('font-size', `${10 * fontScale}px`)
        .style('opacity', 0)
        .text(d => d.value.toFixed(0))
        .transition().duration(chartConfig.animationDuration / 2).delay((d, i) => i * 300).ease(d3.easeElastic).style('opacity', 1);

    createLegend(svg, width, color, 'ID Count', fontScale);

    svg.on('click', () => showDetails(data, 'line', `Trend of ${title} over time.`));
};

const drawBarChart = (container, data, title, color, colorEnd, percentChange) => {
    if (!data?.length) {
        d3.select(container).append('text')
            .attr('x', '50%')
            .attr('y', '50%')
            .attr('text-anchor', 'middle')
            .attr('fill', getCSSVariable('--fg'))
            .text('No data available');
        return;
    }
    const { width, height, fontScale } = getResponsiveDimensions(container);
    const svg = d3.select(container).append('svg')
        .attr('viewBox', `0 0 ${width} ${height}`)
        .style('font-size', `${12 * fontScale}px`);
    const { margin } = chartConfig;
    const x = d3.scaleBand().domain(data.map(d => d.label)).range([margin.left, width - margin.right]).padding(0.25);
    const y = d3.scaleLinear().domain([0, d3.max(data, d => d.value) * 1.2]).nice().range([height - margin.bottom, margin.top]);

    createChartBase(svg, width, height, x, y, fontScale);
    createEffects(svg);
    const gradientId = `barGradient-${Math.random().toString(36).substr(2, 9)}`;
    const fill = createGradient(svg, gradientId, color, colorEnd);

    svg.selectAll('rect').data(data).enter().append('rect')
        .attr('x', d => x(d.label)).attr('y', d => y(0)).attr('width', x.bandwidth()).attr('height', 0)
        .attr('fill', fill).attr('rx', 6).attr('ry', 6).style('cursor', 'pointer')
        .attr('filter', 'url(#glow)')
        .on('mouseover', (event, d) => {
            const tooltipWidth = d3.select('.tooltip').node()?.offsetWidth || 200;
            const xPos = Math.min(event.pageX + 10, window.innerWidth - tooltipWidth - 20);
            const changeText = d === data[0] ? `<br>% Change: ${percentChange?.toFixed(2) || 'N/A'}%` : '';
            d3.select('.tooltip').style('display', 'block')
                .html(`<b>${d.label}</b><br>Value: ${d.value?.toFixed(1) || 'N/A'}${changeText}<br>Trend: ${d.value > (data[data.indexOf(d) - 1]?.value || 0) ? '↑' : '↓'}`)
                .style('left', `${xPos}px`).style('top', `${Math.max(event.pageY - 40, 20)}px`)
                .transition().duration(200).ease(d3.easeElastic).style('opacity', 0.9);
        })
        .on('mouseout', () => d3.select('.tooltip').transition().duration(300).ease(d3.easeElastic).style('opacity', 0)
            .on('end', () => d3.select('.tooltip').style('display', 'none')))
        .transition().duration(chartConfig.animationDuration).delay((d, i) => i * 300).ease(d3.easeElastic)
        .attr('y', d => y(d.value)).attr('height', d => height - margin.bottom - y(d.value));

    svg.selectAll('.data-label').data(data).enter().append('text')
        .attr('class', 'data-label')
        .attr('x', d => x(d.label) + x.bandwidth() / 2)
        .attr('y', d => y(d.value) - 5)
        .attr('fill', getCSSVariable('--fg'))
        .attr('text-anchor', 'middle')
        .style('font-size', `${10 * fontScale}px`)
        .style('opacity', 0)
        .text(d => d.value.toFixed(0))
        .transition().duration(chartConfig.animationDuration / 2).delay((d, i) => i * 300).ease(d3.easeElastic).style('opacity', 1);

    createLegend(svg, width, color, 'GF Count', fontScale);

    svg.on('click', () => showDetails(data, 'bar', `Distribution of ${title} over time. Current month % change: ${percentChange?.toFixed(2) || 'N/A'}%`));
};

const drawLollipopChart = (container, data, title, color, colorEnd) => {
    if (!data?.length) {
        d3.select(container).append('text')
            .attr('x', '50%')
            .attr('y', '50%')
            .attr('text-anchor', 'middle')
            .attr('fill', getCSSVariable('--fg'))
            .text('No data available');
        return;
    }
    const { width, height, fontScale } = getResponsiveDimensions(container);
    const svg = d3.select(container).append('svg')
        .attr('viewBox', `0 0 ${width} ${height}`)
        .style('font-size', `${12 * fontScale}px`);

    const { margin } = chartConfig;
    const x = d3.scalePoint()
        .domain(data.map(d => d.label))
        .range([margin.left + 1, width - margin.right - 1])
        .padding(0.5);
    const y = d3.scaleLinear().domain([0, d3.max(data, d => d.value) * 1.2]).nice()
        .range([height - margin.bottom, margin.top]);

    createChartBase(svg, width, height, x, y, fontScale);
    createEffects(svg);

    svg.selectAll('line.stem')
        .data(data).enter()
        .append('line')
        .attr('class', 'stem')
        .attr('x1', d => x(d.label))
        .attr('x2', d => x(d.label))
        .attr('y1', y(0))
        .attr('y2', y(0))
        .attr('stroke', color)
        .attr('stroke-width', 2)
        .transition()
        .duration(chartConfig.animationDuration)
        .ease(d3.easeBounce)
        .attr('y2', d => y(d.value));

    svg.selectAll('circle.head')
        .data(data).enter()
        .append('circle')
        .attr('class', 'head')
        .attr('cx', d => x(d.label))
        .attr('cy', y(0))
        .attr('r', 0)
        .attr('fill', color)
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .attr('filter', 'url(#glow)')
        .style('cursor', 'pointer')
        .transition()
        .duration(chartConfig.animationDuration)
        .delay((d, i) => i * 100)
        .ease(d3.easeElastic)
        .attr('cy', d => y(d.value))
        .attr('r', 6);

    svg.selectAll('.data-label')
        .data(data).enter()
        .append('text')
        .attr('class', 'data-label')
        .attr('x', d => x(d.label))
        .attr('y', d => y(d.value) - 10)
        .attr('fill', getCSSVariable('--fg'))
        .attr('text-anchor', 'middle')
        .style('font-size', `${10 * fontScale}px`)
        .style('opacity', 0)
        .text(d => d.value.toFixed(0))
        .transition()
        .duration(chartConfig.animationDuration / 2)
        .delay((d, i) => i * 300)
        .ease(d3.easeElastic)
        .style('opacity', 1);

    svg.selectAll('circle.head')
        .on('mouseover', (event, d) => {
            const tooltipWidth = d3.select('.tooltip').node()?.offsetWidth || 200;
            const xPos = Math.min(event.pageX + 10, window.innerWidth - tooltipWidth - 20);
            d3.select('.tooltip').style('display', 'block')
                .html(`<b>${d.label}</b><br>Value: ${d.value?.toFixed(1) || 'N/A'}`)
                .style('left', `${xPos}px`)
                .style('top', `${Math.max(event.pageY - 40, 20)}px`)
                .transition()
                .duration(200)
                .ease(d3.easeElastic)
                .style('opacity', 0.9);
        })
        .on('mouseout', () => d3.select('.tooltip').transition().duration(300).ease(d3.easeElastic).style('opacity', 0)
            .on('end', () => d3.select('.tooltip').style('display', 'none')));

    createLegend(svg, width, color, 'GFC Count', fontScale);

    svg.on('click', () => showDetails(data, 'grouped-bar', `GFC Count Trend over time`));
};

const drawScatterChart = (container, data, title, colorTF, colorOCM) => {
    if (!data?.length) {
        d3.select(container).append('text')
            .attr('x', '50%')
            .attr('y', '50%')
            .attr('text-anchor', 'middle')
            .attr('fill', getCSSVariable('--fg'))
            .text('No data available');
        return;
    }
    const { width, height, fontScale } = getResponsiveDimensions(container);
    const svg = d3.select(container).append('svg')
        .attr('viewBox', `0 0 ${width} ${height}`)
        .style('font-size', `${12 * fontScale}px`);
    const { margin } = chartConfig;
    const x = d3.scalePoint().domain(data.map(d => d.label)).range([margin.left, width - margin.right]);
    const yTF = d3.scaleLinear().domain([0, d3.max(data, d => d.total_tf || 0) * 1.2]).nice().range([height - margin.bottom, margin.top]);
    const yOCM = d3.scaleLinear().domain([0, d3.max(data, d => d.ocm_overall || 0) * 1.2]).nice().range([height - margin.bottom, margin.top]);

    createChartBase(svg, width, height, x, yTF, fontScale);
    svg.append('g')
        .attr('class', 'y-axis')
        .attr('transform', `translate(${width - margin.right}, 0)`)
        .call(d3.axisRight(yOCM).ticks(5).tickFormat(d => d.toFixed(0)))
        .selectAll('text')
        .attr('fill', colorOCM)
        .style('font-size', `${10 * fontScale}px`)
        .selectAll('line, path')
        .attr('stroke', colorOCM)
        .attr('stroke-width', 0.8)
        .attr('stroke-opacity', 0.7);

    createEffects(svg);

    const lineTF = d3.line().x(d => x(d.label)).y(d => yTF(d.total_tf || 0)).curve(d3.curveMonotoneX);
    const lineOCM = d3.line().x(d => x(d.label)).y(d => yOCM(d.ocm_overall || 0)).curve(d3.curveMonotoneX);

    const tfLine = svg.append('path')
        .datum(data)
        .attr('class', 'tf-line')
        .attr('stroke', colorTF)
        .attr('stroke-width', 3)
        .attr('fill', 'none')
        .attr('d', lineTF)
        .attr('stroke-dasharray', function () { return this.getTotalLength(); })
        .attr('stroke-dashoffset', function () { return this.getTotalLength(); })
        .transition()
        .duration(chartConfig.animationDuration)
        .ease(d3.easeElastic)
        .attr('stroke-dashoffset', 0);

    const ocmLine = svg.append('path')
        .datum(data)
        .attr('class', 'ocm-line')
        .attr('stroke', colorOCM)
        .attr('stroke-width', 3)
        .attr('fill', 'none')
        .attr('d', lineOCM)
        .attr('stroke-dasharray', function () { return this.getTotalLength(); })
        .attr('stroke-dashoffset', function () { return this.getTotalLength(); })
        .transition()
        .duration(chartConfig.animationDuration)
        .ease(d3.easeElastic)
        .attr('stroke-dashoffset', 0);

    const tfDots = svg.selectAll('.dot-tf')
        .data(data)
        .enter()
        .append('circle')
        .attr('class', 'dot-tf')
        .attr('cx', d => x(d.label))
        .attr('cy', d => yTF(d.total_tf || 0))
        .attr('r', 0)
        .attr('fill', colorTF)
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .style('cursor', 'pointer')
        .attr('filter', 'url(#glow)')
        .on('mouseover', (event, d) => {
            const tooltipWidth = d3.select('.tooltip').node()?.offsetWidth || 200;
            const xPos = Math.min(event.pageX + 10, window.innerWidth - tooltipWidth - 20);
            d3.select('.tooltip').style('display', 'block')
                .html(`<b>${d.label}</b><br>Total TF: ${d.total_tf?.toFixed(1) || 'N/A'}`)
                .style('left', `${xPos}px`)
                .style('top', `${Math.max(event.pageY - 40, 20)}px`)
                .transition()
                .duration(200)
                .ease(d3.easeElastic)
                .style('opacity', 0.9);
        })
        .on('mouseout', () => d3.select('.tooltip').transition().duration(300).ease(d3.easeElastic).style('opacity', 0)
            .on('end', () => d3.select('.tooltip').style('display', 'none')))
        .transition()
        .duration(chartConfig.animationDuration / 2)
        .delay((d, i) => i * 300)
        .ease(d3.easeElastic)
        .attr('r', 5);

    const ocmDots = svg.selectAll('.dot-ocm')
        .data(data)
        .enter()
        .append('circle')
        .attr('class', 'dot-ocm')
        .attr('cx', d => x(d.label))
        .attr('cy', d => yOCM(d.ocm_overall || 0))
        .attr('r', 0)
        .attr('fill', colorOCM)
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .style('cursor', 'pointer')
        .attr('filter', 'url(#glow)')
        .on('mouseover', (event, d) => {
            const tooltipWidth = d3.select('.tooltip').node()?.offsetWidth || 200;
            const xPos = Math.min(event.pageX + 10, window.innerWidth - tooltipWidth - 20);
            d3.select('.tooltip').style('display', 'block')
                .html(`<b>${d.label}</b><br>OCM Overall: ${d.ocm_overall?.toFixed(1) || 'N/A'}`)
                .style('left', `${xPos}px`)
                .style('top', `${Math.max(event.pageY - 40, 20)}px`)
                .transition()
                .duration(200)
                .ease(d3.easeElastic)
                .style('opacity', 0.9);
        })
        .on('mouseout', () => d3.select('.tooltip').transition().duration(300).ease(d3.easeElastic).style('opacity', 0)
            .on('end', () => d3.select('.tooltip').style('display', 'none')))
        .transition()
        .duration(chartConfig.animationDuration / 2)
        .delay((d, i) => i * 300)
        .ease(d3.easeElastic)
        .attr('r', 5);

    let tfVisible = true, ocmVisible = true;
    const { tfLegend, ocmLegend } = createScatterLegend(svg, width, [colorTF, colorOCM], fontScale);

    tfLegend.on('click', () => {
        tfVisible = !tfVisible;
        tfLine.attr('opacity', tfVisible ? 1 : 0);
        tfDots.attr('opacity', tfVisible ? 1 : 0);
        tfLegend.select('rect').attr('opacity', tfVisible ? 1 : 0.3);
    });

    ocmLegend.on('click', () => {
        ocmVisible = !ocmVisible;
        ocmLine.attr('opacity', ocmVisible ? 1 : 0);
        ocmDots.attr('opacity', ocmVisible ? 1 : 0);
        ocmLegend.select('rect').attr('opacity', ocmVisible ? 1 : 0.3);
    });

    svg.on('click', () => showDetails(data, 'scatter', `Distribution of ${title} over time.`));
};

// const drawSankeyChart = (containerId, data, title, color) => {
//     const container = document.querySelector(containerId);
//     if (!container || !data?.nodes?.length || !data?.links?.length) {
//         d3.select(containerId).append('text')
//             .attr('x', '50%')
//             .attr('y', '50%')
//             .attr('text-anchor', 'middle')
//             .style('fill', getCSSVariable('--fg'))
//             .style('font-size', '12px') // Reduced error message font size
//             .text('No data available');
//         return;
//     }

//     const tableBody = document.querySelector('#data-table-content');
//     if (tableBody) {
//         tableBody.innerHTML = data.links.map(link => `
//             <tr>
//                 <td>${data.nodes[link.source]?.name || 'N/A'}</td>
//                 <td>${data.nodes[link.target]?.name || 'N/A'}</td>
//                 <td>${link.value}</td>
//                 <td>${link.increase || 'N/A'}</td>
//             </tr>
//         `).join('');
//     }

//     if (!document.getElementById('cosmic-pulse-style')) {
//         const style = document.createElement('style');
//         style.id = 'cosmic-pulse-style';
//         style.textContent = `
//             @keyframes pulse {
//                 0%, 100% { filter: drop-shadow(0 0 4px rgba(255,255,255,0.15)); }
//                 50% { filter: drop-shadow(0 0 10px rgba(255,255,255,0.45)); }
//             }
//         `;
//         document.head.appendChild(style);
//     }

//     const { width, height, fontScale } = getResponsiveDimensions(containerId);
//     const isDarkTheme = getComputedStyle(document.documentElement).getPropertyValue('--theme') === 'dark'; // Check theme state
//     const backgroundColor = isDarkTheme ? getCSSVariable('--bg-dark') : getCSSVariable('--bg-light');

//     const svg = d3.select(containerId).append('svg')
//         .attr('viewBox', `0 0 ${width} ${height}`)
//         .attr('preserveAspectRatio', 'xMidYMid meet')
//         .style('width', '100%')
//         .style('height', '100%')
//         .style('font-family', 'Poppins, sans-serif')
//         .style('background', backgroundColor);

//     const margin = { top: 20, right: 20, bottom: 80, left: 20 };

//     const sankey = d3.sankey()
//         .nodeWidth(80) // Reduced from 150 to make cards smaller
//         .nodePadding(20) // Reduced from 40 to decrease vertical spacing
//         .extent([[margin.left, margin.top], [width - margin.right, height - margin.bottom]])
//         .nodeAlign(d3.sankeyCenter);

//     const sankeyData = sankey({
//         nodes: data.nodes.map((d, i) => ({ ...d, id: i })),
//         links: data.links.map(d => ({ ...d }))
//     });

//     const colorScale = d3.scaleOrdinal()
//         .domain(data.nodes.map((_, i) => i))
//         .range(['#f472b6', '#d946ef', '#c026d3', '#a21caf', '#86198f', '#4c1d95']); // Pink to purple gradient

//     const defs = svg.append('defs');
//     const gradientId = `gradient-${Math.random().toString(36).substr(2, 9)}`;
//     const gradient = defs.append('linearGradient')
//         .attr('id', gradientId)
//         .attr('x1', '0%').attr('y1', '0%')
//         .attr('x2', '100%').attr('y2', '0%');
//     gradient.append('stop').attr('offset', '0%').style('stop-color', getCSSVariable('--chart-gradient-start')).style('stop-opacity', 0.8);
//     gradient.append('stop').attr('offset', '100%').style('stop-color', getCSSVariable('--chart-gradient-end')).style('stop-opacity', 0.5);

//     const tooltip = d3.select('.tooltip');

//     const linkGroup = svg.append('g').attr('class', 'links');
//     const links = linkGroup.selectAll('path')
//         .data(sankeyData.links.filter(d => d.value > 0))
//         .enter().append('path')
//         .attr('d', d3.sankeyLinkHorizontal())
//         .attr('stroke', `url(#${gradientId})`)
//         .attr('fill', 'none')
//         .attr('filter', 'url(#glow)')
//         .style('stroke-opacity', 0)
//         .style('stroke-width', 0)
//         .on('mouseover', (event, d) => {
//             const tooltipWidth = tooltip.node()?.offsetWidth || 200;
//             const xPos = Math.min(event.pageX + 12, window.innerWidth - tooltipWidth - 20);
//             tooltip.style('display', 'block')
//                 .html(`<b>${d.source.name} → ${d.target.name}</b><br>Count: ${d.value}<br>Increase: ${d.increase || 'N/A'}`)
//                 .style('left', `${xPos}px`)
//                 .style('top', `${Math.max(event.pageY - 28, 20)}px`)
//                 .transition().duration(200).style('opacity', 0.95);
//         })
//         .on('mouseout', () => {
//             tooltip.transition().duration(300).style('opacity', 0)
//                 .on('end', () => tooltip.style('display', 'none'));
//         });

//     links.transition()
//         .delay((d, i) => i * 50)
//         .duration(1000)
//         .ease(d3.easeCubicInOut)
//         .style('stroke-opacity', d => Math.min(0.7, d.value / 100))
//         .style('stroke-width', d => Math.max(3, Math.min(d.width, 10)));

//     const isLowPerformance = window.innerWidth < 1366 || navigator.hardwareConcurrency < 4;
//     const maxParticlesPerLink = isLowPerformance ? 1 : 2;

//     links.each(function(d) {
//         const path = d3.select(this).node();
//         const length = path.getTotalLength();
//         const particleCount = Math.min(maxParticlesPerLink, Math.floor(d.value / 50));

//         for (let i = 0; i < particleCount; i++) {
//             const particle = svg.append('circle')
//                 .attr('r', 2)
//                 .attr('fill', '#ffffff')
//                 .attr('opacity', 0.5)
//                 .attr('filter', 'url(#glow)');

//             function animate() {
//                 particle.transition()
//                     .duration(2000 + Math.random() * 500)
//                     .delay(i * 400)
//                     .ease(d3.easeLinear)
//                     .attrTween('transform', () => t => {
//                         const point = path.getPointAtLength(t * length);
//                         return `translate(${point.x},${point.y})`;
//                     })
//                     .attrTween('opacity', () => t => (1 - t))
//                     .on('end', animate);
//             }

//             animate();
//         }
//     });

//     const node = svg.append('g').attr('class', 'nodes')
//         .selectAll('g')
//         .data(sankeyData.nodes)
//         .enter().append('g')
//         .attr('transform', d => `translate(${d.x0},${d.y0})`);

//     node.append('rect')
//         .attr('height', d => Math.max(30, d.y1 - d.y0))
//         .attr('width', sankey.nodeWidth())
//         .attr('rx', 8)
//         .attr('ry', 8)
//         .attr('fill', (d, i) => colorScale(i))
//         .attr('filter', 'url(#glow)')
//         .style('opacity', 0)
//         .style('transform', 'scale(0.9) translateY(-5px)')
//         .style('animation', 'pulse 3s infinite')
//         .transition()
//         .delay((d, i) => i * 80)
//         .duration(800)
//         .ease(d3.easeBackOut)
//         .style('opacity', 1)
//         .style('transform', 'scale(1) translateY(0)');

//     node.each(function(d) {
//         const g = d3.select(this);
//         g.append('text')
//             .attr('x', sankey.nodeWidth() / 2)
//             .attr('y', 15 * fontScale)
//             .attr('dy', '0.35em')
//             .attr('text-anchor', 'middle')
//             .style('fill', '#fff')
//             .style('font-size', `${10 * fontScale}px`)
//             .style('font-weight', '600')
//             .text(d.name)
//             .style('opacity', 0)
//             .transition().duration(500).delay(200).style('opacity', 1);

//         g.append('text')
//             .attr('x', sankey.nodeWidth() / 2)
//             .attr('y', 25 * fontScale)
//             .attr('dy', '0.35em')
//             .attr('text-anchor', 'middle')
//             .style('fill', '#fff')
//             .style('font-size', `${12 * fontScale}px`)
//             .style('font-weight', 'bold')
//             .text(d.value || 'N/A')
//             .style('opacity', 0)
//             .transition().duration(500).delay(300).style('opacity', 1);

//         if (d.increase) {
//             g.append('text')
//                 .attr('x', sankey.nodeWidth() / 2)
//                 .attr('y', 35 * fontScale)
//                 .attr('dy', '0.35em')
//                 .attr('text-anchor', 'middle')
//                 .style('fill', '#fff')
//                 .style('font-size', `${10 * fontScale}px`)
//                 .style('font-style', 'italic')
//                 .text(d.increase)
//                 .style('opacity', 0)
//                 .transition().duration(500).delay(400).style('opacity', 1);
//         }
//     });

//     const metrics = data.metrics || [];
//     const metricGroup = svg.append('g').attr('class', 'metrics')
//         .attr('transform', `translate(0, ${height - margin.bottom + 20})`);
//     metrics.forEach((metric, i) => {
//         const xPos = (width / (metrics.length + 1)) * (i + 1);
//         metricGroup.append('rect')
//             .attr('x', xPos - 50)
//             .attr('y', 0)
//             .attr('width', 100)
//             .attr('height', 50)
//             .attr('rx', 6)
//             .attr('ry', 6)
//             .attr('fill', '#fff')
//             .attr('opacity', 0.9)
//             .attr('filter', 'url(#glow)');
//         metricGroup.append('text')
//             .attr('x', xPos)
//             .attr('y', 15)
//             .attr('dy', '0.35em')
//             .attr('text-anchor', 'middle')
//             .style('fill', getCSSVariable('--fg'))
//             .style('font-size', `${10 * fontScale}px`)
//             .text(metric.label);
//         metricGroup.append('text')
//             .attr('x', xPos)
//             .attr('y', 30)
//             .attr('dy', '0.35em')
//             .attr('text-anchor', 'middle')
//             .style('fill', getCSSVariable('--fg'))
//             .style('font-size', `${12 * fontScale}px`)
//             .style('font-weight', 'bold')
//             .text(metric.value);
//     });

//     svg.append('text')
//         .attr('x', width / 2)
//         .attr('y', margin.top / 2)
//         .attr('text-anchor', 'middle')
//         .style('fill', getCSSVariable('--fg'))
//         .style('font-size', `${14 * fontScale}px`)
//         .style('font-weight', '600')
//         .text(title)
//         .style('opacity', 0)
//         .transition().duration(800).style('opacity', 1);

//     svg.on('click', () => {
//         showDetails(
//             sankeyData.links.map(d => ({ label: `${d.source.name} → ${d.target.name}`, value: d.value, increase: d.increase })),
//             'sankey',
//             `Flow from ${title}`
//         );
//     });
// };


// const drawSankeyChart = (containerId, data, title, color) => {
//     const container = document.querySelector(containerId);
//     if (!container || !data?.nodes?.length || !data?.links?.length) {
//         d3.select(containerId).append('text')
//             .attr('x', '50%')
//             .attr('y', '50%')
//             .attr('text-anchor', 'middle')
//             .style('fill', getCSSVariable('--fg'))
//             .style('font-size', '12px') // Reduced error message font size
//             .text('No data available');
//         return;
//     }

//     const tableBody = document.querySelector('#data-table-content');
//     if (tableBody) {
//         tableBody.innerHTML = data.links.map(link => `
//             <tr>
//                 <td>${data.nodes[link.source]?.name || 'N/A'}</td>
//                 <td>${data.nodes[link.target]?.name || 'N/A'}</td>
//                 <td>${link.value}</td>
//                 <td>${link.increase || 'N/A'}</td>
//             </tr>
//         `).join('');
//     }

//     if (!document.getElementById('cosmic-pulse-style')) {
//         const style = document.createElement('style');
//         style.id = 'cosmic-pulse-style';
//         style.textContent = `
//             @keyframes pulse {
//                 0%, 100% { filter: drop-shadow(0 0 4px rgba(255,255,255,0.15)); }
//                 50% { filter: drop-shadow(0 0 10px rgba(255,255,255,0.45)); }
//             }
//         `;
//         document.head.appendChild(style);
//     }

//     const { width, height, fontScale } = getResponsiveDimensions(containerId);
//     const isDarkTheme = getComputedStyle(document.documentElement).getPropertyValue('--theme') === 'dark'; // Check theme state
//     const backgroundColor = isDarkTheme ? getCSSVariable('--bg-dark') : getCSSVariable('--bg-light');

//     const svg = d3.select(containerId).append('svg')
//         .attr('viewBox', `0 0 ${width} ${height}`)
//         .attr('preserveAspectRatio', 'xMidYMid meet')
//         .style('width', '100%')
//         .style('height', '100%')
//         .style('font-family', 'Poppins, sans-serif')
//         .style('background', backgroundColor);

//     const margin = { top: 20, right: 20, bottom: 80, left: 20 };

//     const sankey = d3.sankey()
//         .nodeWidth(80) // Consistent width for all tiles
//         .nodePadding(20) // Consistent padding for uniform spacing
//         .extent([[margin.left, margin.top], [width - margin.right, height - margin.bottom]])
//         .nodeAlign(d3.sankeyCenter);

//     const sankeyData = sankey({
//         nodes: data.nodes.map((d, i) => ({ ...d, id: i })),
//         links: data.links.map(d => ({ ...d }))
//     });

//     // New shade of blue for tiles, compatible with dark and light themes
//     const colorScale = d3.scaleOrdinal()
//         .domain(data.nodes.map((_, i) => i))
//         .range(['#1E40AF', '#3B82F6', '#60A5FA', '#93C5FD', '#BFDBFE', '#DBEAFE']); // New blue shades

//     const defs = svg.append('defs');
//     const gradientId = `gradient-${Math.random().toString(36).substr(2, 9)}`;
//     const gradient = defs.append('linearGradient')
//         .attr('id', gradientId)
//         .attr('x1', '0%').attr('y1', '0%')
//         .attr('x2', '100%').attr('y2', '0%');
//     gradient.append('stop').attr('offset', '0%').style('stop-color', getCSSVariable('--chart-gradient-start')).style('stop-opacity', 0.8);
//     gradient.append('stop').attr('offset', '100%').style('stop-color', getCSSVariable('--chart-gradient-end')).style('stop-opacity', 0.5);

//     const tooltip = d3.select('.tooltip');

//     const linkGroup = svg.append('g').attr('class', 'links');
//     const links = linkGroup.selectAll('path')
//         .data(sankeyData.links.filter(d => d.value > 0))
//         .enter().append('path')
//         .attr('d', d3.sankeyLinkHorizontal())
//         .attr('stroke', `url(#${gradientId})`)
//         .attr('fill', 'none')
//         .attr('filter', 'url(#glow)')
//         .style('stroke-opacity', 0)
//         .style('stroke-width', 0)
//         .on('mouseover', (event, d) => {
//             const tooltipWidth = tooltip.node()?.offsetWidth || 200;
//             const xPos = Math.min(event.pageX + 12, window.innerWidth - tooltipWidth - 20);
//             tooltip.style('display', 'block')
//                 .html(`<b>${d.source.name} → ${d.target.name}</b><br>Count: ${d.value}<br>Increase: ${d.increase || 'N/A'}`)
//                 .style('left', `${xPos}px`)
//                 .style('top', `${Math.max(event.pageY - 28, 20)}px`)
//                 .transition().duration(200).style('opacity', 0.95);
//         })
//         .on('mouseout', () => {
//             tooltip.transition().duration(300).style('opacity', 0)
//                 .on('end', () => tooltip.style('display', 'none'));
//         });

//     links.transition()
//         .delay((d, i) => i * 50)
//         .duration(1000)
//         .ease(d3.easeCubicInOut)
//         .style('stroke-opacity', d => Math.min(0.7, d.value / 100))
//         .style('stroke-width', d => Math.max(3, Math.min(d.width, 10)));

//     const isLowPerformance = window.innerWidth < 1366 || navigator.hardwareConcurrency < 4;
//     const maxParticlesPerLink = isLowPerformance ? 1 : 2;

//     links.each(function(d) {
//         const path = d3.select(this).node();
//         const length = path.getTotalLength();
//         const particleCount = Math.min(maxParticlesPerLink, Math.floor(d.value / 50));

//         for (let i = 0; i < particleCount; i++) {
//             const particle = svg.append('circle')
//                 .attr('r', 2)
//                 .attr('fill', '#ffffff')
//                 .attr('opacity', 0.5)
//                 .attr('filter', 'url(#glow)');

//             function animate() {
//                 particle.transition()
//                     .duration(2000 + Math.random() * 500)
//                     .delay(i * 400)
//                     .ease(d3.easeLinear)
//                     .attrTween('transform', () => t => {
//                         const point = path.getPointAtLength(t * length);
//                         return `translate(${point.x},${point.y})`;
//                     })
//                     .attrTween('opacity', () => t => (1 - t))
//                     .on('end', animate);
//             }

//             animate();
//         }
//     });

//     const node = svg.append('g').attr('class', 'nodes')
//         .selectAll('g')
//         .data(sankeyData.nodes)
//         .enter().append('g')
//         .attr('transform', d => `translate(${d.x0},${d.y0})`);

//     node.append('rect')
//         .attr('height', d => Math.max(30, d.y1 - d.y0)) // Consistent minimum height
//         .attr('width', sankey.nodeWidth()) // Consistent width
//         .attr('rx', 8) // Uniform corner radius
//         .attr('ry', 8) // Uniform corner radius
//         .attr('fill', (d, i) => colorScale(i))
//         .attr('filter', 'url(#glow)')
//         .style('opacity', 0)
//         .style('transform', 'scale(0.9) translateY(-5px)')
//         .style('animation', 'pulse 3s infinite')
//         .transition()
//         .delay((d, i) => i * 80)
//         .duration(800)
//         .ease(d3.easeBackOut)
//         .style('opacity', 1)
//         .style('transform', 'scale(1) translateY(0)');

//     node.each(function(d) {
//         const g = d3.select(this);
//         g.append('text')
//             .attr('x', sankey.nodeWidth() / 2)
//             .attr('y', 15 * fontScale)
//             .attr('dy', '0.35em')
//             .attr('text-anchor', 'middle')
//             .style('fill', '#fff')
//             .style('font-size', `${10 * fontScale}px`)
//             .style('font-weight', '600')
//             .text(d.name)
//             .style('opacity', 0)
//             .transition().duration(500).delay(200).style('opacity', 1);

//         g.append('text')
//             .attr('x', sankey.nodeWidth() / 2)
//             .attr('y', 25 * fontScale)
//             .attr('dy', '0.35em')
//             .attr('text-anchor', 'middle')
//             .style('fill', '#fff')
//             .style('font-size', `${12 * fontScale}px`)
//             .style('font-weight', 'bold')
//             .text(d.value || 'N/A')
//             .style('opacity', 0)
//             .transition().duration(500).delay(300).style('opacity', 1);

//         if (d.increase) {
//             g.append('text')
//                 .attr('x', sankey.nodeWidth() / 2)
//                 .attr('y', 35 * fontScale)
//                 .attr('dy', '0.35em')
//                 .attr('text-anchor', 'middle')
//                 .style('fill', '#fff')
//                 .style('font-size', `${10 * fontScale}px`)
//                 .style('font-style', 'italic')
//                 .text(d.increase)
//                 .style('opacity', 0)
//                 .transition().duration(500).delay(400).style('opacity', 1);
//         }
//     });

//     const metrics = data.metrics || [];
//     const metricGroup = svg.append('g').attr('class', 'metrics')
//         .attr('transform', `translate(0, ${height - margin.bottom + 20})`);
//     metrics.forEach((metric, i) => {
//         const xPos = (width / (metrics.length + 1)) * (i + 1);
//         metricGroup.append('rect')
//             .attr('x', xPos - 50)
//             .attr('y', 0)
//             .attr('width', 100)
//             .attr('height', 50)
//             .attr('rx', 6)
//             .attr('ry', 6)
//             .attr('fill', '#fff')
//             .attr('opacity', 0.9)
//             .attr('filter', 'url(#glow)');
//         metricGroup.append('text')
//             .attr('x', xPos)
//             .attr('y', 15)
//             .attr('dy', '0.35em')
//             .attr('text-anchor', 'middle')
//             .style('fill', getCSSVariable('--fg'))
//             .style('font-size', `${10 * fontScale}px`)
//             .text(metric.label);
//         metricGroup.append('text')
//             .attr('x', xPos)
//             .attr('y', 30)
//             .attr('dy', '0.35em')
//             .attr('text-anchor', 'middle')
//             .style('fill', getCSSVariable('--fg'))
//             .style('font-size', `${12 * fontScale}px`)
//             .style('font-weight', 'bold')
//             .text(metric.value);
//     });

//     svg.append('text')
//         .attr('x', width / 2)
//         .attr('y', margin.top / 2)
//         .attr('text-anchor', 'middle')
//         .style('fill', getCSSVariable('--fg'))
//         .style('font-size', `${14 * fontScale}px`)
//         .style('font-weight', '600')
//         .text(title)
//         .style('opacity', 0)
//         .transition().duration(800).style('opacity', 1);

//     svg.on('click', () => {
//         showDetails(
//             sankeyData.links.map(d => ({ label: `${d.source.name} → ${d.target.name}`, value: d.value, increase: d.increase })),
//             'sankey',
//             `Flow from ${title}`
//         );
//     });
// };
const drawSankeyChart = (containerId, data, title, color) => {
    const container = document.querySelector(containerId);
    if (!container || !data?.nodes?.length || !data?.links?.length) {
        d3.select(containerId).append('text')
            .attr('x', '50%')
            .attr('y', '50%')
            .attr('text-anchor', 'middle')
            .style('fill', getCSSVariable('--fg'))
            .style('font-size', '12px')
            .text('No data available');
        return;
    }

    const tableBody = document.querySelector('#data-table-content');
    if (tableBody) {
        tableBody.innerHTML = data.links.map(link => `
            <tr>
                <td>${data.nodes[link.source]?.name || 'N/A'}</td>
                <td>${data.nodes[link.target]?.name || 'N/A'}</td>
                <td>${link.value}</td>
                <td>${link.increase || 'N/A'}</td>
            </tr>
        `).join('');
    }

    if (!document.getElementById('cosmic-pulse-style')) {
        const style = document.createElement('style');
        style.id = 'cosmic-pulse-style';
        style.textContent = `
            @keyframes pulse {
                0%, 100% { filter: drop-shadow(0 0 3px rgba(255,255,255,0.1)); }
                50% { filter: drop-shadow(0 0 6px rgba(255,255,255,0.3)); }
            }
        `;
        document.head.appendChild(style);
    }

    const { width, height, fontScale } = getResponsiveDimensions(containerId);
    const isDarkTheme = getComputedStyle(document.documentElement).getPropertyValue('--theme') === 'dark';
    const backgroundColor = isDarkTheme ? getCSSVariable('--bg-dark') : getCSSVariable('--bg-light');

    const svg = d3.select(containerId).append('svg')
        .attr('viewBox', `0 0 ${width} ${height}`)
        .attr('preserveAspectRatio', 'xMidYMid meet')
        .style('width', '100%')
        .style('height', '100%')
        .style('font-family', 'Poppins, sans-serif')
        .style('background', backgroundColor);

    const margin = { top: 20, right: 20, bottom: 100, left: 20 }; // Increased bottom margin for metrics

    const sankey = d3.sankey()
        .nodeWidth(65) // Slightly increased for better visibility
        .nodePadding(30) // Increased for better spacing
        .extent([[margin.left, margin.top], [width - margin.right, height - margin.bottom]])
        .nodeAlign(d3.sankeyLeft);

    const sankeyData = sankey({
        nodes: data.nodes.map((d, i) => ({ ...d, id: i })),
        links: data.links.map(d => ({ ...d }))
    });

    // New polished color palette
    const colorScale = d3.scaleOrdinal()
        .domain(data.nodes.map((_, i) => i))
        .range(['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD', '#D4A5A5']);

    const defs = svg.append('defs');
    const gradientId = `gradient-${Math.random().toString(36).substr(2, 9)}`;
    const gradient = defs.append('linearGradient')
        .attr('id', gradientId)
        .attr('x1', '0%').attr('y1', '0%')
        .attr('x2', '100%').attr('y2', '0%');
    gradient.append('stop').attr('offset', '0%').style('stop-color', getCSSVariable('--chart-gradient-start', '#45B7D1')).style('stop-opacity', 0.9);
    gradient.append('stop').attr('offset', '100%').style('stop-color', getCSSVariable('--chart-gradient-end', '#96CEB4')).style('stop-opacity', 0.6);

    const tooltip = d3.select('.tooltip');

    const linkGroup = svg.append('g').attr('class', 'links');
    const links = linkGroup.selectAll('path')
        .data(sankeyData.links.filter(d => d.value > 0))
        .enter().append('path')
        .attr('d', d3.sankeyLinkHorizontal())
        .attr('stroke', `url(#${gradientId})`)
        .attr('fill', 'none')
        .attr('filter', 'url(#glow)')
        .style('stroke-opacity', 0)
        .style('stroke-width', 0)
        .on('mouseover', (event, d) => {
            const tooltipWidth = tooltip.node()?.offsetWidth || 200;
            const xPos = Math.min(event.pageX + 12, window.innerWidth - tooltipWidth - 20);
            tooltip.style('display', 'block')
                .html(`<b>${d.source.name} → ${d.target.name}</b><br>Count: ${d.value}<br>Increase: ${d.increase || 'N/A'}`)
                .style('left', `${xPos}px`)
                .style('top', `${Math.max(event.pageY - 28, 20)}px`)
                .transition().duration(200).style('opacity', 0.95);
        })
        .on('mouseout', () => {
            tooltip.transition().duration(300).style('opacity', 0)
                .on('end', () => tooltip.style('display', 'none'));
        });

    links.transition()
        .delay((d, i) => i * 50)
        .duration(1000)
        .ease(d3.easeCubicInOut)
        .style('stroke-opacity', d => Math.min(0.8, d.value / 80)) // Adjusted opacity scale
        .style('stroke-width', d => Math.max(4, Math.min(d.width, 12)));

    const isLowPerformance = window.innerWidth < 1366 || navigator.hardwareConcurrency < 4;
    const maxParticlesPerLink = isLowPerformance ? 1 : 2;

    links.each(function (d) {
        const path = d3.select(this).node();
        const length = path.getTotalLength();
        const particleCount = Math.min(maxParticlesPerLink, Math.floor(d.value / 40));

        for (let i = 0; i < particleCount; i++) {
            const particle = svg.append('circle')
                .attr('r', 2.5) // Slightly larger particles
                .attr('fill', '#ffffff')
                .attr('opacity', 0.6)
                .attr('filter', 'url(#glow)');

            function animate() {
                particle.transition()
                    .duration(1800 + Math.random() * 400)
                    .delay(i * 350)
                    .ease(d3.easeLinear)
                    .attrTween('transform', () => {
                        let lastPoint = { x: 0, y: 0 };
                        return t => {
                            const point = path.getPointAtLength(t * length);
                            if (t === 0) lastPoint = point;
                            return `translate(${point.x},${point.y})`;
                        };
                    })
                    .attrTween('opacity', () => t => (1 - t) * 0.4 + 0.6)
                    .on('end', animate);
            }

            animate();
        }
    });

    const node = svg.append('g').attr('class', 'nodes')
        .selectAll('g')
        .data(sankeyData.nodes)
        .enter().append('g')
        .attr('transform', d => `translate(${d.x0},${d.y0})`);

    node.append('rect')
        .attr('height', d => Math.max(40, d.y1 - d.y0)) // Slightly increased minimum height
        .attr('width', sankey.nodeWidth())
        .attr('rx', 10) // Increased corner radius for polish
        .attr('ry', 10)
        .attr('fill', (d, i) => colorScale(i)) // Apply color to nodes
        .attr('filter', 'url(#glow)')
        .style('opacity', 0)
        .style('transform', 'scale(0.9) translateY(-5px)')
        .style('animation', 'pulse 2.5s infinite')
        .transition()
        .delay((d, i) => i * 70)
        .duration(700)
        .ease(d3.easeBackOut)
        .style('opacity', 1)
        .style('transform', 'scale(1) translateY(0)');

    node.each(function (d) {
        const g = d3.select(this);
        g.append('text')
            .attr('x', sankey.nodeWidth() / 2)
            .attr('y', 18 * fontScale)
            .attr('dy', '0.35em')
            .attr('text-anchor', 'middle')
            .style('fill', '#fff')
            .style('font-size', `${11 * fontScale}px`) // Slightly increased font size
            .style('font-weight', '600')
            .text(d.name.length > 12 ? d.name.substring(0, 12) + '...' : d.name)
            .style('opacity', 0)
            .transition().duration(500).delay(200).style('opacity', 1);

        g.append('text')
            .attr('x', sankey.nodeWidth() / 2)
            .attr('y', 28 * fontScale)
            .attr('dy', '0.35em')
            .attr('text-anchor', 'middle')
            .style('fill', '#fff')
            .style('font-size', `${13 * fontScale}px`) // Slightly increased font size
            .style('font-weight', 'bold')
            .text(d.value || 'N/A')
            .style('opacity', 0)
            .transition().duration(500).delay(300).style('opacity', 1);

        if (d.increase) {
            g.append('text')
                .attr('x', sankey.nodeWidth() / 2)
                .attr('y', 38 * fontScale)
                .attr('dy', '0.35em')
                .attr('text-anchor', 'middle')
                .style('fill', '#fff')
                .style('font-size', `${11 * fontScale}px`)
                .style('font-style', 'italic')
                .text(d.increase)
                .style('opacity', 0)
                .transition().duration(500).delay(400).style('opacity', 1);
        }
    });

    const metrics = data.metrics || [{ label: 'Current Status', value: 'N/A' }, { label: 'Total Projects', value: 'N/A' }, { label: 'Saving', value: 'N/A' }];
    const metricGroup = svg.append('g').attr('class', 'metrics')
        .attr('transform', `translate(0, ${height - margin.bottom + 30})`); // Adjusted for better positioning
    metrics.forEach((metric, i) => {
        const xPos = (width / (metrics.length + 1)) * (i + 1);
        metricGroup.append('rect')
            .attr('x', xPos - 60) // Increased width
            .attr('y', 0)
            .attr('width', 120)
            .attr('height', 60)
            .attr('rx', 8)
            .attr('ry', 8)
            .attr('fill', '#fff')
            .attr('opacity', 0.95)
            .attr('filter', 'url(#glow)');
        metricGroup.append('text')
            .attr('x', xPos)
            .attr('y', 20)
            .attr('dy', '0.35em')
            .attr('text-anchor', 'middle')
            .style('fill', getCSSVariable('--fg'))
            .style('font-size', `${11 * fontScale}px`)
            .text(metric.label);
        metricGroup.append('text')
            .attr('x', xPos)
            .attr('y', 40)
            .attr('dy', '0.35em')
            .attr('text-anchor', 'middle')
            .style('fill', getCSSVariable('--fg'))
            .style('font-size', `${13 * fontScale}px`)
            .style('font-weight', 'bold')
            .text(metric.value);
    });

    svg.append('text')
        .attr('x', width / 2)
        .attr('y', margin.top / 2)
        .attr('text-anchor', 'middle')
        .style('fill', getCSSVariable('--fg'))
        .style('font-size', `${15 * fontScale}px`) // Slightly increased title size
        .style('font-weight', '600')
        .text(title)
        .style('opacity', 0)
        .transition().duration(800).style('opacity', 1);

    svg.on('click', () => {
        showDetails(
            sankeyData.links.map(d => ({ label: `${d.source.name} → ${d.target.name}`, value: d.value, increase: d.increase })),
            'sankey',
            `Flow from ${title}`
        );
    });
};

const showCommentForm = (chartId = 'all-charts') => {
    const formContainer = document.querySelector('.comment-form-container');
    if (!formContainer) return;
    formContainer.classList.add('open');
    const chartInput = formContainer.querySelector('#chart-select');
    const hiddenChartInput = formContainer.querySelector('#comment-chart-id');
    if (chartInput && hiddenChartInput) {
        chartInput.value = chartId;
        hiddenChartInput.value = chartId;
    }
};

const closeCommentForm = () => {
    const formContainer = document.querySelector('.comment-form-container');
    if (formContainer) formContainer.classList.remove('open');
    const form = formContainer.querySelector('.comment-form');
    if (form) form.reset();
};

const submitComment = async (event) => {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const chartId = formData.get('chart_id');
    const commentData = {
        chart_id: chartId,
        page: window.location.pathname,
        text: formData.get('comments'),
        user: formData.get('username') || 'Anonymous',
        reason: formData.get('reason'),
        exclusion: formData.get('exclusion'),
        why: formData.get('why'),
        quick_fix: formData.get('quick_fix'),
        to_do: formData.get('to_do')
    };

    try {
        const response = await fetch('/api/annotations', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(commentData)
        });
        if (!response.ok) throw new Error(`Failed to submit comment: ${response.status}`);
        const result = await response.json();
        alert('Comment added successfully!');
        closeCommentForm();
        fetchComments(chartId === 'all-charts' ? 'all-charts' : chartId);
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

const showDetails = (data, type, summary) => {
    if (!data?.length) {
        alert('No data available to display.');
        return;
    }

    const chartId = type === 'line' ? 'line-chart' :
        type === 'bar' ? 'bar-chart' :
        type === 'lollipop' ? 'area-chart' :
        type === 'scatter' ? 'scatter-chart' :
        type === 'sankey' ? 'sankey-chart' : 'all-charts';

    const container = document.getElementById('details');
    if (container) {
        container.classList.add('open');
        const overview = document.getElementById('overview-text');
        if (overview) overview.textContent = summary;
        const tableBody = document.querySelector('#data-table-content tbody');
        if (tableBody) {
            tableBody.innerHTML = data.map(d => `
                <tr>
                    <td>${d.label || 'N/A'}</td>
                    <td>${type === 'scatter' ?
                        `TF: ${d.total_tf?.toFixed(2) || 'N/A'}, OCM: ${d.ocm_overall?.toFixed(2) || 'N/A'}` :
                        type === 'grouped-bar' ?
                            `Baseline: ${d.baseline?.toFixed(2) || 'N/A'}, Growth: ${d.growth?.toFixed(2) || 'N/A'}` :
                            `${(d.value ?? 'N/A').toFixed(2)}`}</td>
                </tr>
            `).join('');
        }
        switchTab('comments');
        setTimeout(() => {
            fetchComments(chartId);
        }, 100);
    }
};

const fetchComments = async (chartId, container = document.querySelector('#comments-content')) => {
    try {
        const response = await fetch(`/api/annotations?page=${window.location.pathname}&chart_id=${chartId}`, {
            cache: 'no-store'
        });
        if (!response.ok) throw new Error(`Failed to fetch comments: ${response.status}`);
        let comments = await response.json();
        if (container) {
            if (chartId === 'all-charts') {
                const allChartIds = ['line-chart', 'bar-chart', 'area-chart', 'scatter-chart', 'sankey-chart'];
                const allComments = [];
                for (const id of allChartIds) {
                    const resp = await fetch(`/api/annotations?page=${window.location.pathname}&chart_id=${id}`, {
                        cache: 'no-store'
                    });
                    if (resp.ok) {
                        const chartComments = await resp.json();
                        allComments.push(...chartComments);
                    }
                }
                const allChartsResp = await fetch(`/api/annotations?page=${window.location.pathname}&chart_id=all-charts`, {
                    cache: 'no-store'
                });
                if (allChartsResp.ok) {
                    const allChartsComments = await allChartsResp.json();
                    allComments.push(...allChartsComments);
                }
                comments = allComments;
            } else {
                const allChartsResp = await fetch(`/api/annotations?page=${window.location.pathname}&chart_id=all-charts`, {
                    cache: 'no-store'
                });
                if (allChartsResp.ok) {
                    const allChartsComments = await allChartsResp.json();
                    comments = [...comments, ...allChartsComments];
                }
            }
            if (comments.length > 0) {
                comments.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
                const table = `
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: ${getCSSVariable('--card-border')};">
                                <th style="padding: 8px; text-align: left;">User</th>
                                <th style="padding: 8px; text-align: left;">Chart</th>
                                <th style="padding: 8px; text-align: left;">Comment</th>
                                <th style="padding: 8px; text-align: left;">Reason</th>
                                <th style="padding: 8px; text-align: left;">Exclusion</th>
                                <th style="padding: 8px; text-align: left;">Why</th>
                                <th style="padding: 8px; text-align: left;">Quick Fix</th>
                                <th style="padding: 8px; text-align: left;">To Do</th>
                                <th style="padding: 8px; text-align: left;">Date</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${comments.map(comment => `
                                <tr style="border-bottom: 1px solid ${getCSSVariable('--card-border')};">
                                    <td style="padding: 8px;">${comment.user || 'Anonymous'}</td>
                                    <td style="padding: 8px;">${comment.chart_id.replace('-chart', '').toUpperCase()}</td>
                                    <td style="padding: 8px;">${comment.text}</td>
                                    <td style="padding: 8px;">${comment.reason || ''}</td>
                                    <td style="padding: 8px;">${comment.exclusion || ''}</td>
                                    <td style="padding: 8px;">${comment.why || ''}</td>
                                    <td style="padding: 8px;">${comment.quick_fix || ''}</td>
                                    <td style="padding: 8px;">${comment.to_do || ''}</td>
                                    <td style="padding: 8px;">${new Date(comment.created_at).toLocaleString()}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
                container.innerHTML = table;
                return new Promise(resolve => requestAnimationFrame(() => resolve(true)));
            } else {
                container.innerHTML = `<p style="color: ${getCSSVariable('--fg')};">No comments available for ${chartId.replace('-chart', '').toUpperCase()}.</p>`;
                return true;
            }
        }
    } catch (error) {
        console.error('Error fetching comments:', error);
        if (container) {
            container.innerHTML = `<p style="color: ${getCSSVariable('--fg')};">Error loading comments for ${chartId.replace('-chart', '').toUpperCase()}: ${error.message}</p>`;
        }
        return false;
    }
};

// Update "Add Comments" button handler to wait for comments table to render
document.addEventListener('DOMContentLoaded', () => {
    const addCommentsButton = document.querySelector('.header-actions button:nth-child(3)'); // Targets the "Add Comments" button
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
                    // Poll DOM to ensure table is rendered with proper scoping
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
                alert('Failed to load comments. Please try again later. Error: ' + error.message);
            }
        });
    }

    createTooltip();
    initializeCharts();
});

// SocketIO for real-time comment updates
const socket = io('/annotations');
socket.on('connect', () => {
    console.log('Connected to SocketIO');
});
socket.on('new_comment', (comment) => {
    if (comment.page === window.location.pathname) {
        fetchComments(comment.chart_id);
    }
});

// Event Handling
const debounce = (func, wait) => {
    let timeout;
    return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
};

const createTooltip = () => {
    let tooltip = d3.select('.tooltip');
    if (!tooltip.node()) {
        tooltip = d3.select('body')
            .append('div')
            .attr('class', 'tooltip')
            .style('position', 'absolute')
            .style('opacity', 0)
            .style('display', 'none')
            .style('pointer-events', 'none')
            .style('z-index', 9999)
            .style('background', getCSSVariable('--card'))
            .style('color', getCSSVariable('--fg'))
            .style('padding', '0.5rem')
            .style('font-size', getCSSVariable('--font-size-base'))
            .style('border-radius', '4px')
            .style('box-shadow', '0 2px 8px rgba(0, 0, 0, 0.15)')
            .style('border', `1px solid ${getCSSVariable('--card-border')}`);
    }
    return tooltip;
};

const initializeCharts = async (retryCount = 0, maxRetries = 5) => {
    console.log(`Initializing charts (attempt ${retryCount + 1})`);

    if (typeof d3 === 'undefined') {
        console.error('D3.js not loaded');
        if (retryCount < maxRetries) {
            setTimeout(() => initializeCharts(retryCount + 1, maxRetries), 500);
            return;
        } else {
            console.error('Failed to load D3.js after retries');
            return;
        }
    }

    const containers = [
        '#line-chart',
        '#bar-chart',
        '#area-chart',
        window.location.pathname === '/' ? '#scatter-chart' : null
    ].filter(id => id && document.querySelector(id));

    if (containers.length === 0) {
        console.error('Chart containers not found');
        if (retryCount < maxRetries) {
            setTimeout(() => initializeCharts(retryCount + 1, maxRetries), 500);
            return;
        }
    }

    createTooltip();
    await drawCharts();
    if (containers.length > 0) retryCount = 0;
};

// Improvement: Add resize event listener with debouncing
const debouncedDrawCharts = debounce(drawCharts, 150);

document.addEventListener('DOMContentLoaded', initializeCharts);
window.addEventListener('resize', debouncedDrawCharts);
window.addEventListener('beforeunload', () => {
    window.removeEventListener('resize', debouncedDrawCharts);
});