/**
 * FINESE2 Dashboard - Chart Rendering Engine
 * Uses Plotly.js for interactive visualizations
 */

class ChartEngine {
    constructor() {
        this.defaultLayout = {
            paper_bgcolor: '#1C2128',
            plot_bgcolor: '#1C2128',
            font: { family: 'Inter, sans-serif', color: '#E6EDF3', size: 12 },
            margin: { l: 60, r: 30, t: 40, b: 50 },
            xaxis: {
                gridcolor: '#30363D', zerolinecolor: '#30363D',
                tickfont: { color: '#8B949E' }
            },
            yaxis: {
                gridcolor: '#30363D', zerolinecolor: '#30363D',
                tickfont: { color: '#8B949E' }
            },
            legend: { bgcolor: 'rgba(28,33,40,0.8)', font: { color: '#E6EDF3' } },
            hoverlabel: { bgcolor: '#1C2128', font: { color: '#E6EDF3' }, bordercolor: '#30363D' }
        };
        this.colors = ['#00D4AA', '#6C63FF', '#FF6B6B', '#FFD93D', '#6BCB77', '#4D96FF', '#FF9F45', '#C9B1FF'];
    }

    getLayout(title = '', extra = {}) {
        return {
            ...this.defaultLayout,
            title: { text: title, font: { size: 16, color: '#E6EDF3' } },
            ...extra
        };
    }

    getConfig() {
        return {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['lasso2d', 'select2d'],
            displaylogo: false
        };
    }

    // ===== CHART TYPES =====

    barChart(containerId, data, title = '', xLabel = '', yLabel = '') {
        const trace = {
            x: data.map(d => d.x || d.label),
            y: data.map(d => d.y || d.value),
            type: 'bar',
            marker: {
                color: data.map((_, i) => this.colors[i % this.colors.length]),
                line: { width: 0 }
            },
            text: data.map(d => d.y || d.value),
            textposition: 'auto',
            textfont: { color: '#E6EDF3', size: 11 }
        };
        const layout = this.getLayout(title, {
            xaxis: { ...this.defaultLayout.xaxis, title: xLabel },
            yaxis: { ...this.defaultLayout.yaxis, title: yLabel }
        });
        Plotly.newPlot(containerId, [trace], layout, this.getConfig());
    }

    lineChart(containerId, xData, yData, title = '', xLabel = '', yLabel = '') {
        const trace = {
            x: xData, y: yData, type: 'scatter', mode: 'lines+markers',
            line: { color: this.colors[0], width: 3 },
            marker: { size: 6, color: this.colors[0] }
        };
        const layout = this.getLayout(title, {
            xaxis: { ...this.defaultLayout.xaxis, title: xLabel },
            yaxis: { ...this.defaultLayout.yaxis, title: yLabel }
        });
        Plotly.newPlot(containerId, [trace], layout, this.getConfig());
    }

    scatterPlot(containerId, xData, yData, title = '', xLabel = '', yLabel = '', colors = null) {
        const trace = {
            x: xData, y: yData, mode: 'markers', type: 'scatter',
            marker: {
                size: 8, color: colors || this.colors[1],
                opacity: 0.7, line: { width: 1, color: '#E6EDF3' }
            }
        };
        const layout = this.getLayout(title, {
            xaxis: { ...this.defaultLayout.xaxis, title: xLabel },
            yaxis: { ...this.defaultLayout.yaxis, title: yLabel }
        });
        Plotly.newPlot(containerId, [trace], layout, this.getConfig());
    }

    histogram(containerId, data, title = '', xLabel = '', nbins = 30) {
        const trace = {
            x: data, type: 'histogram', nbinsx: nbins,
            marker: { color: this.colors[0], line: { color: '#30363D', width: 1 } }
        };
        const layout = this.getLayout(title, {
            xaxis: { ...this.defaultLayout.xaxis, title: xLabel },
            yaxis: { ...this.defaultLayout.yaxis, title: 'Count' }
        });
        Plotly.newPlot(containerId, [trace], layout, this.getConfig());
    }

    boxPlot(containerId, data, title = '', labels = null) {
        const traces = [];
        if (Array.isArray(data[0])) {
            data.forEach((d, i) => {
                traces.push({
                    y: d, type: 'box', name: labels ? labels[i] : `Group ${i+1}`,
                    marker: { color: this.colors[i % this.colors.length] },
                    boxpoints: 'outliers'
                });
            });
        } else {
            traces.push({
                y: data, type: 'box', name: title,
                marker: { color: this.colors[0] }, boxpoints: 'outliers'
            });
        }
        Plotly.newPlot(containerId, traces, this.getLayout(title), this.getConfig());
    }

    pieChart(containerId, labels, values, title = '') {
        const trace = {
            labels: labels, values: values, type: 'pie',
            hole: 0.4, textinfo: 'percent+label',
            marker: { colors: this.colors, line: { color: '#1C2128', width: 2 } },
            textfont: { color: '#E6EDF3', size: 12 }
        };
        Plotly.newPlot(containerId, [trace], this.getLayout(title), this.getConfig());
    }

    heatmap(containerId, z, xLabels, yLabels, title = '') {
        const trace = {
            z: z, x: xLabels, y: yLabels, type: 'heatmap',
            colorscale: [[0, '#161B22'], [0.5, '#00D4AA'], [1, '#6C63FF']],
            showscale: true, colorbar: { tickfont: { color: '#8B949E' } },
            text: z.map(row => row.map(v => v.toFixed(2))),
            texttemplate: '%{text}', hoverongaps: false
        };
        Plotly.newPlot(containerId, [trace], this.getLayout(title), this.getConfig());
    }

    correlationHeatmap(containerId, corrMatrix, title = 'Correlation Heatmap') {
        const columns = Object.keys(corrMatrix);
        const z = columns.map(col => columns.map(c2 => corrMatrix[col][c2] || 0));
        const trace = {
            z: z, x: columns, y: columns, type: 'heatmap',
            colorscale: [[0, '#F85149'], [0.5, '#1C2128'], [1, '#00D4AA']],
            zmid: 0, showscale: true,
            text: z.map(row => row.map(v => v.toFixed(2))),
            texttemplate: '%{text}', hoverongaps: false,
            colorbar: { tickfont: { color: '#8B949E' } }
        };
        const layout = this.getLayout(title, {
            xaxis: { ...this.defaultLayout.xaxis, tickangle: -45 },
            yaxis: { ...this.defaultLayout.yaxis, automargin: true }
        });
        Plotly.newPlot(containerId, [trace], layout, this.getConfig());
    }

    featureImportance(containerId, features, importances, title = 'Feature Importance') {
        const sorted = features.map((f, i) => ({ name: f, value: importances[i] }))
            .sort((a, b) => b.value - a.value).slice(0, 20);
        const trace = {
            y: sorted.map(d => d.name), x: sorted.map(d => d.value),
            type: 'bar', orientation: 'h',
            marker: { color: this.colors[0] }
        };
        const layout = this.getLayout(title, {
            yaxis: { ...this.defaultLayout.yaxis, automargin: true },
            xaxis: { ...this.defaultLayout.xaxis, title: 'Importance' },
            margin: { l: 150, r: 30, t: 40, b: 50 }
        });
        Plotly.newPlot(containerId, [trace], layout, this.getConfig());
    }

    modelComparison(containerId, modelNames, metrics, title = 'Model Comparison') {
        const traces = Object.keys(metrics[0] || {}).map((metric, i) => ({
            x: modelNames,
            y: metrics.map(m => m[metric] || 0),
            name: metric, type: 'bar',
            marker: { color: this.colors[i % this.colors.length] }
        }));
        const layout = this.getLayout(title, {
            barmode: 'group',
            xaxis: { ...this.defaultLayout.xaxis, tickangle: -30 },
            yaxis: { ...this.defaultLayout.yaxis, title: 'Score' }
        });
        Plotly.newPlot(containerId, traces, layout, this.getConfig());
    }

    gaugeChart(containerId, value, title = '', min = 0, max = 100) {
        const trace = {
            type: 'indicator', mode: 'gauge+number',
            value: value, title: { text: title, font: { color: '#E6EDF3' } },
            gauge: {
                axis: { range: [min, max], tickcolor: '#8B949E', tickfont: { color: '#8B949E' } },
                bar: { color: '#00D4AA' },
                bgcolor: '#1C2128',
                steps: [
                    { range: [min, max * 0.3], color: '#F8514920' },
                    { range: [max * 0.3, max * 0.7], color: '#D2992220' },
                    { range: [max * 0.7, max], color: '#3FB95020' }
                ],
                threshold: { line: { color: '#6C63FF', width: 4 }, thickness: 0.75, value: value }
            }
        };
        const layout = { ...this.getLayout(''), paper_bgcolor: '#1C2128', height: 250 };
        Plotly.newPlot(containerId, [trace], layout, this.getConfig());
    }

    // ===== UTILITY =====
    renderPlotlyJSON(containerId, plotlyJSON) {
        if (plotlyJSON && plotlyJSON.data) {
            const layout = { ...this.defaultLayout, ...(plotlyJSON.layout || {}) };
            Plotly.newPlot(containerId, plotlyJSON.data, layout, this.getConfig());
        }
    }

    destroy(containerId) {
        Plotly.purge(containerId);
    }
}

const charts = new ChartEngine();
