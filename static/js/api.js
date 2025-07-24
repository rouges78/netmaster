/**
 * NetMaster API - Modulo per comunicazione con il server
 * Gestisce tutte le chiamate API REST al backend Flask
 */

class NetMasterAPI {
    constructor() {
        this.baseUrl = window.location.origin;
        this.credentials = null;
        this.init();
    }
    
    init() {
        // Prova a recuperare credenziali salvate
        this.loadCredentials();
        console.log('[NetMaster API] Modulo inizializzato');
    }
    
    loadCredentials() {
        // Per ora usa credenziali di default - in produzione implementare login
        this.credentials = {
            username: 'admin',
            password: 'password' // In produzione sarà gestito tramite form di login
        };
    }
    
    getAuthHeaders() {
        if (!this.credentials) {
            throw new Error('Credenziali non configurate');
        }
        
        const encoded = btoa(`${this.credentials.username}:${this.credentials.password}`);
        return {
            'Authorization': `Basic ${encoded}`,
            'Content-Type': 'application/json'
        };
    }
    
    async makeRequest(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: this.getAuthHeaders(),
            ...options
        };
        
        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error('Autenticazione fallita');
                } else if (response.status === 429) {
                    throw new Error('Troppe richieste - riprova più tardi');
                } else {
                    throw new Error(`Errore HTTP ${response.status}: ${response.statusText}`);
                }
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            console.error(`[NetMaster API] Errore richiesta ${endpoint}:`, error);
            throw error;
        }
    }
    
    // === ENDPOINT ESISTENTI ===
    
    async getHistory(startDate = null, endDate = null) {
        let endpoint = '/api/history';
        const params = new URLSearchParams();
        
        if (startDate) params.append('start', startDate);
        if (endDate) params.append('end', endDate);
        
        if (params.toString()) {
            endpoint += `?${params.toString()}`;
        }
        
        return await this.makeRequest(endpoint, { method: 'GET' });
    }
    
    async getThresholds() {
        return await this.makeRequest('/api/thresholds', { method: 'GET' });
    }
    
    async saveThresholds(thresholds) {
        return await this.makeRequest('/api/thresholds', {
            method: 'POST',
            body: JSON.stringify(thresholds)
        });
    }
    
    async getEmailConfig() {
        return await this.makeRequest('/api/notifications/config', { method: 'GET' });
    }
    
    async saveEmailConfig(config) {
        return await this.makeRequest('/api/notifications/config', {
            method: 'POST',
            body: JSON.stringify(config)
        });
    }
    
    // === NUOVI ENDPOINT PER DASHBOARD ===
    
    async getStats() {
        return await this.makeRequest('/api/stats', { method: 'GET' });
    }
    
    async getRealTimeData(timespan = '6h') {
        return await this.makeRequest(`/api/realtime?timespan=${timespan}`, { method: 'GET' });
    }
    
    async getAgents() {
        return await this.makeRequest('/api/agents', { method: 'GET' });
    }
    
    async getAgent(agentId) {
        return await this.makeRequest(`/api/agents/${agentId}`, { method: 'GET' });
    }
    
    async getAlerts() {
        return await this.makeRequest('/api/alerts', { method: 'GET' });
    }
    
    async dismissAlert(alertId) {
        return await this.makeRequest(`/api/alerts/${alertId}/dismiss`, { method: 'POST' });
    }
    
    async getSystemHealth() {
        return await this.makeRequest('/api/health', { method: 'GET' });
    }
    
    // === METODI DI UTILITÀ ===
    
    async testConnection() {
        try {
            await this.makeRequest('/api/health', { method: 'GET' });
            return true;
        } catch (error) {
            return false;
        }
    }
    
    // Mock data per sviluppo (da rimuovere quando gli endpoint saranno implementati)
    async getMockStats() {
        return new Promise(resolve => {
            setTimeout(() => {
                resolve({
                    total_agents: 5,
                    avg_cpu: 45.2,
                    avg_memory: 67.8,
                    avg_disk: 23.4,
                    active_alerts: 2
                });
            }, 500);
        });
    }
    
    async getMockRealTimeData() {
        return new Promise(resolve => {
            setTimeout(() => {
                const now = Date.now();
                const data = [];
                
                // Genera dati mock per le ultime 6 ore
                for (let i = 0; i < 72; i++) {
                    const timestamp = now - (i * 5 * 60 * 1000); // Ogni 5 minuti
                    data.unshift({
                        timestamp: timestamp,
                        cpu: 30 + Math.random() * 40,
                        memory: 50 + Math.random() * 30,
                        disk: 20 + Math.random() * 20
                    });
                }
                
                resolve(data);
            }, 300);
        });
    }
    
    async getMockAgents() {
        return new Promise(resolve => {
            setTimeout(() => {
                resolve([
                    {
                        id: 1,
                        hostname: 'PC-UFFICIO-01',
                        ip_address: '192.168.1.100',
                        cpu_percent: 45.2,
                        memory_percent: 67.8,
                        disk_percent: 23.4,
                        processes: 156,
                        uptime: 86400,
                        platform: 'Windows 11',
                        architecture: 'x64',
                        last_update: Date.now() / 1000 - 30,
                        status: 'online'
                    },
                    {
                        id: 2,
                        hostname: 'PC-UFFICIO-02',
                        ip_address: '192.168.1.101',
                        cpu_percent: 78.5,
                        memory_percent: 89.2,
                        disk_percent: 45.7,
                        processes: 203,
                        uptime: 172800,
                        platform: 'Windows 10',
                        architecture: 'x64',
                        last_update: Date.now() / 1000 - 45,
                        status: 'warning'
                    },
                    {
                        id: 3,
                        hostname: 'SERVER-01',
                        ip_address: '192.168.1.10',
                        cpu_percent: 23.1,
                        memory_percent: 45.6,
                        disk_percent: 67.8,
                        processes: 89,
                        uptime: 2592000,
                        platform: 'Ubuntu 22.04',
                        architecture: 'x64',
                        last_update: Date.now() / 1000 - 15,
                        status: 'online'
                    },
                    {
                        id: 4,
                        hostname: 'PC-RECEPTION',
                        ip_address: '192.168.1.102',
                        cpu_percent: 12.3,
                        memory_percent: 34.5,
                        disk_percent: 12.1,
                        processes: 67,
                        uptime: 43200,
                        platform: 'Windows 11',
                        architecture: 'x64',
                        last_update: Date.now() / 1000 - 120,
                        status: 'offline'
                    },
                    {
                        id: 5,
                        hostname: 'PC-ADMIN',
                        ip_address: '192.168.1.103',
                        cpu_percent: 56.7,
                        memory_percent: 72.3,
                        disk_percent: 34.5,
                        processes: 134,
                        uptime: 129600,
                        platform: 'Windows 11',
                        architecture: 'x64',
                        last_update: Date.now() / 1000 - 60,
                        status: 'online'
                    }
                ]);
            }, 400);
        });
    }
    
    async getMockAlerts() {
        return new Promise(resolve => {
            setTimeout(() => {
                resolve([
                    {
                        id: '1',
                        type: 'cpu',
                        severity: 'warning',
                        title: 'CPU Elevata',
                        message: 'PC-UFFICIO-02: CPU al 78.5% (soglia: 75%)',
                        timestamp: Date.now() / 1000 - 300,
                        active: true,
                        agent_hostname: 'PC-UFFICIO-02'
                    },
                    {
                        id: '2',
                        type: 'memory',
                        severity: 'critical',
                        title: 'Memoria Critica',
                        message: 'PC-UFFICIO-02: Memoria al 89.2% (soglia: 85%)',
                        timestamp: Date.now() / 1000 - 180,
                        active: true,
                        agent_hostname: 'PC-UFFICIO-02'
                    },
                    {
                        id: '3',
                        type: 'system',
                        severity: 'error',
                        title: 'Agent Offline',
                        message: 'PC-RECEPTION non risponde da 2 minuti',
                        timestamp: Date.now() / 1000 - 120,
                        active: true,
                        agent_hostname: 'PC-RECEPTION'
                    }
                ]);
            }, 200);
        });
    }
    
    // Metodi che usano mock data durante lo sviluppo
    async getStatsWithFallback() {
        try {
            return await this.getStats();
        } catch (error) {
            console.warn('[NetMaster API] Usando dati mock per stats:', error.message);
            return await this.getMockStats();
        }
    }
    
    async getRealTimeDataWithFallback(timespan = '6h') {
        try {
            return await this.getRealTimeData(timespan);
        } catch (error) {
            console.warn('[NetMaster API] Usando dati mock per real-time:', error.message);
            return await this.getMockRealTimeData();
        }
    }
    
    async getAgentsWithFallback() {
        try {
            return await this.getAgents();
        } catch (error) {
            console.warn('[NetMaster API] Usando dati mock per agents:', error.message);
            return await this.getMockAgents();
        }
    }
    
    async getAlertsWithFallback() {
        try {
            return await this.getAlerts();
        } catch (error) {
            console.warn('[NetMaster API] Usando dati mock per alerts:', error.message);
            return await this.getMockAlerts();
        }
    }
}

// Crea istanza globale dell'API
window.NetMasterAPI = new NetMasterAPI();

// Alias per compatibilità con dashboard.js
window.NetMasterAPI.getStats = window.NetMasterAPI.getStatsWithFallback;
window.NetMasterAPI.getRealTimeData = window.NetMasterAPI.getRealTimeDataWithFallback;
window.NetMasterAPI.getAgents = window.NetMasterAPI.getAgentsWithFallback;
window.NetMasterAPI.getAlerts = window.NetMasterAPI.getAlertsWithFallback;

// Aggiungi alias per tutte le funzioni mancanti
window.NetMasterAPI.getThresholds = window.NetMasterAPI.getThresholds || function() {
    return Promise.resolve({ cpu: 75, memory: 85, disk: 90 });
};

window.NetMasterAPI.getEmailConfig = window.NetMasterAPI.getEmailConfig || function() {
    return Promise.resolve({
        enabled: true,
        smtp_server: 'smtp.gmail.com',
        smtp_port: 587,
        username: 'test@example.com'
    });
};

window.NetMasterAPI.saveThresholds = window.NetMasterAPI.saveThresholds || function(thresholds) {
    return Promise.resolve({ message: 'Soglie salvate con successo' });
};

window.NetMasterAPI.saveEmailConfig = window.NetMasterAPI.saveEmailConfig || function(config) {
    return Promise.resolve({ message: 'Configurazione email salvata' });
};

console.log('[NetMaster API] Tutti gli alias configurati correttamente');
