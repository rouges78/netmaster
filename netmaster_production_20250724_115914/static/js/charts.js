/**
 * NetMaster Charts - Modulo per gestione grafici Chart.js
 * Gestisce tutti i grafici real-time e storici della dashboard
 */

class NetMasterCharts {
    constructor() {
        this.charts = {};
        this.chartConfigs = {};
        this.init();
    }
    
    init() {
        // Configurazione globale Chart.js
        Chart.defaults.font.family = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
        Chart.defaults.font.size = 12;
        Chart.defaults.color = '#64748b';
        Chart.defaults.borderColor = '#e2e8f0';
        Chart.defaults.backgroundColor = 'rgba(37, 99, 235, 0.1)';
        
        console.log('[NetMaster Charts] Modulo inizializzato');
    }
    
    // === CONFIGURAZIONI BASE ===
    
    getBaseLineConfig() {
        return {
            type: 'line',
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#2563eb',
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: true,
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.y.toFixed(1)}%`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            displayFormats: {
                                minute: 'HH:mm',
                                hour: 'HH:mm',
                                day: 'DD/MM'
                            }
                        },
                        grid: {
                            display: true,
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            maxTicksLimit: 8
                        }
                    },
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            display: true,
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                },
                elements: {
                    line: {
                        tension: 0.4,
                        borderWidth: 2
                    },
                    point: {
                        radius: 0,
                        hoverRadius: 6,
                        hitRadius: 10
                    }
                },
                animation: {
                    duration: 750,
                    easing: 'easeInOutQuart'
                }
            }
        };
    }
    
    // === CREAZIONE GRAFICI ===
    
    createCpuChart(canvasId) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        const config = this.getBaseLineConfig();
        
        config.data = {
            datasets: [{
                label: 'CPU %',
                data: [],
                borderColor: '#06b6d4',
                backgroundColor: 'rgba(6, 182, 212, 0.1)',
                fill: true
            }]
        };
        
        // Personalizzazioni specifiche per CPU
        config.options.plugins.tooltip.callbacks.label = function(context) {
            return `CPU: ${context.parsed.y.toFixed(1)}%`;
        };
        
        this.charts[canvasId] = new Chart(ctx, config);
        this.chartConfigs[canvasId] = 'cpu';
        
        return this.charts[canvasId];
    }
    
    createMemoryChart(canvasId) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        const config = this.getBaseLineConfig();
        
        config.data = {
            datasets: [{
                label: 'Memoria %',
                data: [],
                borderColor: '#f59e0b',
                backgroundColor: 'rgba(245, 158, 11, 0.1)',
                fill: true
            }]
        };
        
        // Personalizzazioni specifiche per Memoria
        config.options.plugins.tooltip.callbacks.label = function(context) {
            return `Memoria: ${context.parsed.y.toFixed(1)}%`;
        };
        
        this.charts[canvasId] = new Chart(ctx, config);
        this.chartConfigs[canvasId] = 'memory';
        
        return this.charts[canvasId];
    }
    
    createHistoryChart(canvasId) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        const config = this.getBaseLineConfig();
        
        config.data = {
            datasets: [
                {
                    label: 'CPU %',
                    data: [],
                    borderColor: '#06b6d4',
                    backgroundColor: 'rgba(6, 182, 212, 0.1)',
                    fill: false,
                    yAxisID: 'y'
                },
                {
                    label: 'Memoria %',
                    data: [],
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    fill: false,
                    yAxisID: 'y'
                },
                {
                    label: 'Disco %',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: false,
                    yAxisID: 'y'
                }
            ]
        };
        
        // Personalizzazioni per grafico storico
        config.options.plugins.tooltip.callbacks.label = function(context) {
            return `${context.dataset.label}: ${context.parsed.y.toFixed(1)}%`;
        };
        
        this.charts[canvasId] = new Chart(ctx, config);
        this.chartConfigs[canvasId] = 'history';
        
        return this.charts[canvasId];
    }
    
    createDoughnutChart(canvasId, title) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        const config = {
            type: 'doughnut',
            data: {
                labels: ['Utilizzato', 'Libero'],
                datasets: [{
                    data: [0, 100],
                    backgroundColor: [
                        '#2563eb',
                        '#e2e8f0'
                    ],
                    borderWidth: 0,
                    cutout: '70%'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.label}: ${context.parsed}%`;
                            }
                        }
                    }
                },
                animation: {
                    animateRotate: true,
                    duration: 1000
                }
            }
        };
        
        this.charts[canvasId] = new Chart(ctx, config);
        return this.charts[canvasId];
    }
    
    // === AGGIORNAMENTO DATI ===
    
    updateChart(chartId, data) {
        const chart = this.charts[chartId];
        if (!chart) {
            console.warn(`[Charts] Grafico ${chartId} non trovato`);
            return;
        }
        
        const chartType = this.chartConfigs[chartId];
        
        switch (chartType) {
            case 'cpu':
                this.updateLineChart(chart, data, 'cpu');
                break;
            case 'memory':
                this.updateLineChart(chart, data, 'memory');
                break;
            case 'history':
                this.updateHistoryChart(chart, data);
                break;
            default:
                console.warn(`[Charts] Tipo grafico ${chartType} non supportato`);
        }
    }
    
    updateLineChart(chart, data, metric) {
        // Converte i dati nel formato Chart.js
        const chartData = data.map(point => ({
            x: new Date(point.timestamp),
            y: point[metric]
        }));
        
        chart.data.datasets[0].data = chartData;
        chart.update('none'); // Aggiornamento senza animazione per real-time
    }
    
    updateHistoryChart(chart, data) {
        // Aggiorna tutti e tre i dataset (CPU, Memoria, Disco)
        const metrics = ['cpu', 'memory', 'disk'];
        
        metrics.forEach((metric, index) => {
            const chartData = data.map(point => ({
                x: new Date(point.timestamp),
                y: point[metric + '_percent'] || point[metric] || 0
            }));
            
            chart.data.datasets[index].data = chartData;
        });
        
        chart.update();
    }
    
    updateDoughnutChart(chartId, percentage) {
        const chart = this.charts[chartId];
        if (!chart) return;
        
        chart.data.datasets[0].data = [percentage, 100 - percentage];
        
        // Cambia colore in base alla percentuale
        if (percentage > 90) {
            chart.data.datasets[0].backgroundColor[0] = '#ef4444';
        } else if (percentage > 75) {
            chart.data.datasets[0].backgroundColor[0] = '#f59e0b';
        } else {
            chart.data.datasets[0].backgroundColor[0] = '#2563eb';
        }
        
        chart.update();
    }
    
    // === GESTIONE TIMESPAN ===
    
    updateTimespan(chartId, timespan) {
        const chart = this.charts[chartId];
        if (!chart) return;
        
        // Aggiorna la configurazione dell'asse X in base al timespan
        let displayFormat, unit;
        
        switch (timespan) {
            case '1h':
                displayFormat = 'HH:mm';
                unit = 'minute';
                chart.options.scales.x.ticks.maxTicksLimit = 12;
                break;
            case '6h':
                displayFormat = 'HH:mm';
                unit = 'hour';
                chart.options.scales.x.ticks.maxTicksLimit = 8;
                break;
            case '24h':
                displayFormat = 'HH:mm';
                unit = 'hour';
                chart.options.scales.x.ticks.maxTicksLimit = 12;
                break;
            default:
                displayFormat = 'HH:mm';
                unit = 'hour';
                chart.options.scales.x.ticks.maxTicksLimit = 8;
        }
        
        chart.options.scales.x.time.displayFormats[unit] = displayFormat;
        chart.options.scales.x.time.unit = unit;
        chart.update();
    }
    
    // === UTILITÀ ===
    
    destroyChart(chartId) {
        if (this.charts[chartId]) {
            this.charts[chartId].destroy();
            delete this.charts[chartId];
            delete this.chartConfigs[chartId];
        }
    }
    
    destroyAllCharts() {
        Object.keys(this.charts).forEach(chartId => {
            this.destroyChart(chartId);
        });
    }
    
    resizeCharts() {
        Object.values(this.charts).forEach(chart => {
            chart.resize();
        });
    }
    
    // === TEMI E STILI ===
    
    setDarkTheme() {
        Chart.defaults.color = '#94a3b8';
        Chart.defaults.borderColor = '#334155';
        
        Object.values(this.charts).forEach(chart => {
            chart.options.scales.x.grid.color = 'rgba(255, 255, 255, 0.1)';
            chart.options.scales.y.grid.color = 'rgba(255, 255, 255, 0.1)';
            chart.update();
        });
    }
    
    setLightTheme() {
        Chart.defaults.color = '#64748b';
        Chart.defaults.borderColor = '#e2e8f0';
        
        Object.values(this.charts).forEach(chart => {
            chart.options.scales.x.grid.color = 'rgba(0, 0, 0, 0.05)';
            chart.options.scales.y.grid.color = 'rgba(0, 0, 0, 0.05)';
            chart.update();
        });
    }
    
    // === EXPORT ===
    
    exportChart(chartId, filename) {
        const chart = this.charts[chartId];
        if (!chart) return;
        
        const url = chart.toBase64Image();
        const link = document.createElement('a');
        link.download = filename || `chart-${chartId}.png`;
        link.href = url;
        link.click();
    }
    
    // === METODI PUBBLICI PER LA DASHBOARD ===
    
    initializeCharts() {
        // Inizializza tutti i grafici della dashboard
        this.createCpuChart('cpuChart');
        this.createMemoryChart('memoryChart');
        this.createHistoryChart('historyChart');
        
        console.log('[Charts] Grafici inizializzati');
    }
    
    updateRealTimeCharts(data) {
        // Aggiorna i grafici real-time con nuovi dati
        this.updateChart('cpuChart', data);
        this.updateChart('memoryChart', data);
    }
    
    updateHistoryChartData(data) {
        // Aggiorna il grafico storico
        this.updateChart('historyChart', data);
    }
    
    setupChartControls() {
        // Configura i controlli per cambiare timespan
        document.querySelectorAll('.chart-controls button').forEach(button => {
            button.addEventListener('click', (e) => {
                const timespan = e.target.dataset.timespan;
                const chartContainer = e.target.closest('.chart-container');
                const canvas = chartContainer.querySelector('canvas');
                
                if (canvas && timespan) {
                    // Aggiorna stato attivo dei bottoni
                    chartContainer.querySelectorAll('.chart-controls button').forEach(btn => {
                        btn.classList.remove('active');
                    });
                    e.target.classList.add('active');
                    
                    // Aggiorna timespan del grafico
                    this.updateTimespan(canvas.id, timespan);
                    
                    // Ricarica dati per il nuovo timespan
                    if (window.dashboard) {
                        window.dashboard.loadChartData(canvas.id, timespan);
                    }
                }
            });
        });
    }
}

// Crea istanza globale dei grafici
window.NetMasterCharts = new NetMasterCharts();

// Inizializza i grafici quando il DOM è pronto
document.addEventListener('DOMContentLoaded', () => {
    // Aspetta che la dashboard sia inizializzata
    setTimeout(() => {
        window.NetMasterCharts.initializeCharts();
        window.NetMasterCharts.setupChartControls();
    }, 1000);
});

// Gestisce il resize della finestra
window.addEventListener('resize', () => {
    window.NetMasterCharts.resizeCharts();
});
