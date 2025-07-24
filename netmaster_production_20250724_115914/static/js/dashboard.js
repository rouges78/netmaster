/**
 * NetMaster Dashboard - JavaScript principale
 * Gestisce la logica della dashboard, navigazione e aggiornamenti real-time
 */

class NetMasterDashboard {
    constructor() {
        this.refreshInterval = 10000; // 10 secondi di default
        this.refreshTimer = null;
        this.isConnected = false;
        this.currentSection = 'overview';
        this.charts = {};
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupNavigation();
        this.setupRefreshControls();
        this.startAutoRefresh();
        this.loadInitialData();
        
        console.log('[NetMaster] Dashboard inizializzata');
    }
    
    setupEventListeners() {
        // Refresh manuale
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.refreshData();
        });
        
        // Cambio intervallo refresh
        document.getElementById('refreshInterval').addEventListener('change', (e) => {
            this.refreshInterval = parseInt(e.target.value);
            this.restartAutoRefresh();
        });
        
        // Ricerca agent
        document.getElementById('agentSearch').addEventListener('input', (e) => {
            this.filterAgents(e.target.value);
        });
        
        // Export dati
        document.getElementById('exportBtn').addEventListener('click', () => {
            this.exportData();
        });
        
        // Form soglie
        document.getElementById('thresholdForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveThresholds();
        });
        
        // Form email
        document.getElementById('emailForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveEmailConfig();
        });
        
        // Caricamento storico
        document.getElementById('loadHistoryBtn').addEventListener('click', () => {
            this.loadHistoryData();
        });
    }
    
    setupNavigation() {
        const navItems = document.querySelectorAll('.nav-item');
        
        navItems.forEach(item => {
            item.addEventListener('click', () => {
                const section = item.dataset.section;
                this.switchSection(section);
                
                // Aggiorna stato attivo
                navItems.forEach(nav => nav.classList.remove('active'));
                item.classList.add('active');
            });
        });
    }
    
    switchSection(sectionName) {
        // Nascondi tutte le sezioni
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });
        
        // Mostra la sezione selezionata
        document.getElementById(sectionName).classList.add('active');
        this.currentSection = sectionName;
        
        // Carica dati specifici per la sezione
        this.loadSectionData(sectionName);
    }
    
    setupRefreshControls() {
        // Imposta data/ora corrente per i controlli storico
        const now = new Date();
        const endDate = now.toISOString().slice(0, 16);
        const startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString().slice(0, 16);
        
        document.getElementById('endDate').value = endDate;
        document.getElementById('startDate').value = startDate;
    }
    
    async loadInitialData() {
        this.showLoading(true);
        
        try {
            await Promise.all([
                this.loadOverviewData(),
                this.loadAgentsData(),
                this.loadThresholds(),
                this.loadEmailConfig()
            ]);
            
            this.updateConnectionStatus(true);
            this.showToast('Dashboard caricata con successo', 'success');
        } catch (error) {
            console.error('[NetMaster] Errore caricamento iniziale:', error);
            this.updateConnectionStatus(false);
            this.showToast('Errore nel caricamento dei dati', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    async loadSectionData(section) {
        switch (section) {
            case 'overview':
                await this.loadOverviewData();
                break;
            case 'agents':
                await this.loadAgentsData();
                break;
            case 'history':
                await this.loadHistoryData();
                break;
            case 'alerts':
                await this.loadAlertsData();
                break;
            case 'settings':
                await this.loadSettingsData();
                break;
        }
    }
    
    async loadOverviewData() {
        try {
            // Carica statistiche generali
            const stats = await NetMasterAPI.getStats();
            this.updateStatsCards(stats);
            
            // Carica dati real-time per i grafici
            const realtimeData = await NetMasterAPI.getRealTimeData();
            this.updateCharts(realtimeData);
            
            // Carica lista agent
            const agents = await NetMasterAPI.getAgents();
            this.updateAgentsTable(agents);
            
        } catch (error) {
            console.error('[NetMaster] Errore caricamento overview:', error);
            throw error;
        }
    }
    
    async loadAgentsData() {
        try {
            const agents = await NetMasterAPI.getAgents();
            this.updateAgentsGrid(agents);
        } catch (error) {
            console.error('[NetMaster] Errore caricamento agent:', error);
        }
    }
    
    async loadHistoryData() {
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        
        if (!startDate || !endDate) {
            this.showToast('Seleziona un intervallo di date valido', 'warning');
            return;
        }
        
        try {
            const historyData = await NetMasterAPI.getHistory(startDate, endDate);
            this.updateHistoryChart(historyData);
        } catch (error) {
            console.error('[NetMaster] Errore caricamento storico:', error);
            this.showToast('Errore nel caricamento dello storico', 'error');
        }
    }
    
    async loadAlertsData() {
        try {
            // Carica avvisi attivi
            const alerts = await NetMasterAPI.getAlerts();
            this.updateAlertsList(alerts);
            
            // Aggiorna badge contatore
            document.getElementById('alertCount').textContent = alerts.filter(a => a.active).length;
        } catch (error) {
            console.error('[NetMaster] Errore caricamento avvisi:', error);
        }
    }
    
    async loadSettingsData() {
        try {
            await this.loadThresholds();
            await this.loadEmailConfig();
        } catch (error) {
            console.error('[NetMaster] Errore caricamento impostazioni:', error);
        }
    }
    
    async loadThresholds() {
        try {
            const thresholds = await NetMasterAPI.getThresholds();
            
            document.getElementById('cpuThreshold').value = thresholds.cpu || 80;
            document.getElementById('memoryThreshold').value = thresholds.memory || 85;
            document.getElementById('diskThreshold').value = thresholds.disk || 90;
        } catch (error) {
            console.error('[NetMaster] Errore caricamento soglie:', error);
        }
    }
    
    async loadEmailConfig() {
        try {
            const config = await NetMasterAPI.getEmailConfig();
            
            if (config) {
                document.getElementById('smtpServer').value = config.smtp_server || '';
                document.getElementById('smtpPort').value = config.smtp_port || 587;
                document.getElementById('senderEmail').value = config.sender_email || '';
                document.getElementById('recipientEmail').value = config.recipient_email || '';
            }
        } catch (error) {
            console.error('[NetMaster] Errore caricamento config email:', error);
        }
    }
    
    updateStatsCards(stats) {
        document.getElementById('totalAgents').textContent = stats.total_agents || 0;
        document.getElementById('avgCpu').textContent = `${Math.round(stats.avg_cpu || 0)}%`;
        document.getElementById('avgMemory').textContent = `${Math.round(stats.avg_memory || 0)}%`;
        document.getElementById('avgDisk').textContent = `${Math.round(stats.avg_disk || 0)}%`;
        
        // Aggiorna progress bar
        this.updateProgressBar('cpuProgress', stats.avg_cpu || 0);
        this.updateProgressBar('memoryProgress', stats.avg_memory || 0);
        this.updateProgressBar('diskProgress', stats.avg_disk || 0);
        
        // Aggiorna badge contatore agent
        document.getElementById('agentCount').textContent = stats.total_agents || 0;
    }
    
    updateProgressBar(elementId, percentage) {
        const progressBar = document.getElementById(elementId);
        progressBar.style.width = `${Math.min(percentage, 100)}%`;
        
        // Cambia colore in base alla percentuale
        if (percentage > 90) {
            progressBar.style.background = 'var(--danger-color)';
        } else if (percentage > 75) {
            progressBar.style.background = 'var(--warning-color)';
        } else {
            progressBar.style.background = 'var(--primary-color)';
        }
    }
    
    updateAgentsTable(agents) {
        const tbody = document.getElementById('agentsTableBody');
        tbody.innerHTML = '';
        
        agents.forEach(agent => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>${agent.hostname}</strong></td>
                <td>${agent.ip_address}</td>
                <td>
                    <span class="stat-value ${this.getStatusClass(agent.cpu_percent, 80)}">${agent.cpu_percent}%</span>
                </td>
                <td>
                    <span class="stat-value ${this.getStatusClass(agent.memory_percent, 85)}">${agent.memory_percent}%</span>
                </td>
                <td>
                    <span class="stat-value ${this.getStatusClass(agent.disk_percent, 90)}">${agent.disk_percent}%</span>
                </td>
                <td>${this.formatTimestamp(agent.last_update)}</td>
                <td>
                    <span class="status-badge ${agent.status}">${this.getStatusText(agent.status)}</span>
                </td>
            `;
            tbody.appendChild(row);
        });
    }
    
    updateAgentsGrid(agents) {
        const grid = document.getElementById('agentsGrid');
        grid.innerHTML = '';
        
        agents.forEach(agent => {
            const card = document.createElement('div');
            card.className = 'agent-card';
            card.innerHTML = `
                <div class="agent-header">
                    <h3>${agent.hostname}</h3>
                    <span class="status-badge ${agent.status}">${this.getStatusText(agent.status)}</span>
                </div>
                <div class="agent-info">
                    <p><strong>IP:</strong> ${agent.ip_address}</p>
                    <p><strong>Platform:</strong> ${agent.platform || 'N/A'}</p>
                    <p><strong>Uptime:</strong> ${this.formatUptime(agent.uptime)}</p>
                </div>
                <div class="agent-metrics">
                    <div class="metric">
                        <span class="metric-label">CPU</span>
                        <span class="metric-value ${this.getStatusClass(agent.cpu_percent, 80)}">${agent.cpu_percent}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">RAM</span>
                        <span class="metric-value ${this.getStatusClass(agent.memory_percent, 85)}">${agent.memory_percent}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Disco</span>
                        <span class="metric-value ${this.getStatusClass(agent.disk_percent, 90)}">${agent.disk_percent}%</span>
                    </div>
                </div>
            `;
            grid.appendChild(card);
        });
    }
    
    updateAlertsList(alerts) {
        const list = document.getElementById('alertsList');
        list.innerHTML = '';
        
        if (alerts.length === 0) {
            list.innerHTML = '<p class="no-alerts">Nessun avviso attivo</p>';
            return;
        }
        
        alerts.forEach(alert => {
            const alertElement = document.createElement('div');
            alertElement.className = `alert-item ${alert.severity}`;
            alertElement.innerHTML = `
                <div class="alert-icon">
                    <i class="fas fa-${this.getAlertIcon(alert.type)}"></i>
                </div>
                <div class="alert-content">
                    <h4>${alert.title}</h4>
                    <p>${alert.message}</p>
                    <small>${this.formatTimestamp(alert.timestamp)}</small>
                </div>
                <div class="alert-actions">
                    <button class="btn btn-sm" onclick="dashboard.dismissAlert('${alert.id}')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
            list.appendChild(alertElement);
        });
    }
    
    async saveThresholds() {
        const thresholds = {
            cpu: parseInt(document.getElementById('cpuThreshold').value),
            memory: parseInt(document.getElementById('memoryThreshold').value),
            disk: parseInt(document.getElementById('diskThreshold').value)
        };
        
        try {
            await NetMasterAPI.saveThresholds(thresholds);
            this.showToast('Soglie salvate con successo', 'success');
        } catch (error) {
            console.error('[NetMaster] Errore salvataggio soglie:', error);
            this.showToast('Errore nel salvataggio delle soglie', 'error');
        }
    }
    
    async saveEmailConfig() {
        const config = {
            smtp_server: document.getElementById('smtpServer').value,
            smtp_port: parseInt(document.getElementById('smtpPort').value),
            sender_email: document.getElementById('senderEmail').value,
            sender_password: document.getElementById('emailPassword').value,
            recipient_email: document.getElementById('recipientEmail').value
        };
        
        try {
            await NetMasterAPI.saveEmailConfig(config);
            this.showToast('Configurazione email salvata', 'success');
            
            // Pulisci il campo password per sicurezza
            document.getElementById('emailPassword').value = '';
        } catch (error) {
            console.error('[NetMaster] Errore salvataggio config email:', error);
            this.showToast('Errore nel salvataggio della configurazione', 'error');
        }
    }
    
    filterAgents(searchTerm) {
        const rows = document.querySelectorAll('#agentsTableBody tr');
        
        rows.forEach(row => {
            const hostname = row.cells[0].textContent.toLowerCase();
            const ip = row.cells[1].textContent.toLowerCase();
            
            if (hostname.includes(searchTerm.toLowerCase()) || ip.includes(searchTerm.toLowerCase())) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }
    
    exportData() {
        // Implementa export CSV dei dati correnti
        const data = this.getCurrentTableData();
        const csv = this.convertToCSV(data);
        this.downloadCSV(csv, 'netmaster-data.csv');
        
        this.showToast('Dati esportati con successo', 'success');
    }
    
    getCurrentTableData() {
        const rows = document.querySelectorAll('#agentsTableBody tr');
        const data = [];
        
        rows.forEach(row => {
            if (row.style.display !== 'none') {
                data.push({
                    hostname: row.cells[0].textContent,
                    ip: row.cells[1].textContent,
                    cpu: row.cells[2].textContent,
                    memory: row.cells[3].textContent,
                    disk: row.cells[4].textContent,
                    lastUpdate: row.cells[5].textContent,
                    status: row.cells[6].textContent
                });
            }
        });
        
        return data;
    }
    
    convertToCSV(data) {
        if (data.length === 0) return '';
        
        const headers = Object.keys(data[0]);
        const csvContent = [
            headers.join(','),
            ...data.map(row => headers.map(header => `"${row[header]}"`).join(','))
        ].join('\n');
        
        return csvContent;
    }
    
    downloadCSV(csv, filename) {
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);
    }
    
    startAutoRefresh() {
        this.refreshTimer = setInterval(() => {
            if (this.currentSection === 'overview') {
                this.refreshData();
            }
        }, this.refreshInterval);
    }
    
    restartAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
        this.startAutoRefresh();
    }
    
    async refreshData() {
        try {
            await this.loadSectionData(this.currentSection);
            this.updateLastUpdateTime();
            this.updateConnectionStatus(true);
        } catch (error) {
            console.error('[NetMaster] Errore refresh:', error);
            this.updateConnectionStatus(false);
        }
    }
    
    updateConnectionStatus(connected) {
        this.isConnected = connected;
        const statusElement = document.getElementById('connectionStatus');
        const statusIcon = document.getElementById('statusIcon');
        const statusText = document.getElementById('statusText');
        
        if (connected) {
            statusElement.className = 'connection-status connected';
            statusText.textContent = 'Connesso';
        } else {
            statusElement.className = 'connection-status disconnected';
            statusText.textContent = 'Disconnesso';
        }
    }
    
    updateLastUpdateTime() {
        const now = new Date();
        document.getElementById('lastUpdate').textContent = now.toLocaleTimeString('it-IT');
    }
    
    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (show) {
            overlay.classList.add('active');
        } else {
            overlay.classList.remove('active');
        }
    }
    
    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <i class="fas fa-${this.getToastIcon(type)}"></i>
                <span>${message}</span>
            </div>
        `;
        
        container.appendChild(toast);
        
        // Mostra il toast
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Rimuovi il toast dopo 5 secondi
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => container.removeChild(toast), 300);
        }, 5000);
    }
    
    // Utility functions
    getStatusClass(value, threshold) {
        if (value > threshold) return 'danger';
        if (value > threshold * 0.8) return 'warning';
        return 'success';
    }
    
    getStatusText(status) {
        const statusMap = {
            'online': 'Online',
            'offline': 'Offline',
            'warning': 'Avviso'
        };
        return statusMap[status] || 'Sconosciuto';
    }
    
    getAlertIcon(type) {
        const iconMap = {
            'cpu': 'microchip',
            'memory': 'memory',
            'disk': 'hdd',
            'network': 'network-wired',
            'system': 'exclamation-triangle'
        };
        return iconMap[type] || 'info-circle';
    }
    
    getToastIcon(type) {
        const iconMap = {
            'success': 'check-circle',
            'error': 'times-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return iconMap[type] || 'info-circle';
    }
    
    formatTimestamp(timestamp) {
        if (!timestamp) return 'N/A';
        const date = new Date(timestamp * 1000);
        return date.toLocaleString('it-IT');
    }
    
    formatUptime(seconds) {
        if (!seconds) return 'N/A';
        
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        
        if (days > 0) return `${days}g ${hours}h`;
        if (hours > 0) return `${hours}h ${minutes}m`;
        return `${minutes}m`;
    }
}

// Inizializza la dashboard quando il DOM è pronto
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new NetMasterDashboard();
});
