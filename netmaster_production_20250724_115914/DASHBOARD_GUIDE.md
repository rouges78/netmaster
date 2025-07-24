# 🌐 NetMaster Dashboard - Guida Utente

*Versione: 1.0.0 | Data: 24 Luglio 2025*

## 📋 Panoramica

La **NetMaster Dashboard** è un'interfaccia web moderna e responsive per il monitoraggio in tempo reale dei sistemi in rete locale. Sostituisce l'interfaccia desktop con una soluzione web-based accessibile da qualsiasi browser.

## 🚀 Accesso alla Dashboard

### URL di Accesso
```
http://127.0.0.1:5000
```

### Credenziali di Accesso
- **Username**: `admin`
- **Password**: `password`

### Avvio del Server
```bash
# Naviga nella directory del progetto
cd c:\Users\davide\Desktop\progetto-server

# Avvia il server di test (per sviluppo)
python server_test.py

# Oppure avvia il server principale (produzione)
python server.py
```

## 🎯 Funzionalità Principali

### 1. 📊 **Sezione Panoramica**
- **Statistiche Aggregate**: Visualizza metriche globali del sistema
  - Numero totale di agent monitorati
  - CPU media di tutti i sistemi
  - Memoria media utilizzata
  - Numero di avvisi attivi

- **Grafici Real-time**: 
  - Grafico CPU con aggiornamento automatico
  - Grafico Memoria con dati storici
  - Timespan configurabili (1h, 6h, 24h)

### 2. 🖥️ **Gestione Agent**
- **Lista Agent**: Tabella con tutti i sistemi monitorati
- **Informazioni per Agent**:
  - Hostname e indirizzo IP
  - Stato (Online/Warning/Offline)
  - CPU, Memoria, Disco (percentuali)
  - Piattaforma e architettura
  - Ultimo aggiornamento

- **Filtri e Ricerca**:
  - Filtra per stato (Tutti/Online/Warning/Offline)
  - Ricerca per hostname o IP
  - Ordinamento per colonne

### 3. 📈 **Storico Dati**
- **Grafici Storici**: Visualizzazione dati nel tempo
- **Filtri Temporali**: Seleziona periodo di interesse
- **Export Dati**: Esporta dati in formato CSV/JSON
- **Analisi Trend**: Identifica pattern e anomalie

### 4. 🚨 **Sistema Avvisi**
- **Notifiche Real-time**: Avvisi automatici per soglie superate
- **Severità Colorate**:
  - 🟢 **Info**: Informazioni generali
  - 🟡 **Warning**: Attenzione richiesta
  - 🔴 **Critical**: Intervento immediato
  - ⚫ **Error**: Errori di sistema

- **Gestione Avvisi**:
  - Visualizza dettagli avviso
  - Dismissal manuale
  - Cronologia avvisi

### 5. ⚙️ **Configurazioni**
- **Soglie di Monitoraggio**:
  - CPU: Soglia di allerta (default: 75%)
  - Memoria: Soglia critica (default: 85%)
  - Disco: Soglia spazio (default: 90%)

- **Notifiche Email**:
  - Configurazione server SMTP
  - Destinatari notifiche
  - Template personalizzati

## 🛠️ Architettura Tecnica

### Frontend
- **HTML5**: Struttura semantica moderna
- **CSS3**: Design responsive e animazioni
- **JavaScript ES6+**: Logica modulare e interattiva
- **Chart.js**: Grafici interattivi e real-time

### Backend API
- **Flask**: Framework web Python
- **SQLite**: Database locale per dati storici
- **RESTful API**: Endpoint standardizzati
- **Autenticazione Basic**: Sicurezza integrata

### Moduli JavaScript

#### 1. `api.js` - Comunicazione API
```javascript
// Esempio di utilizzo
const stats = await NetMasterAPI.getStats();
const agents = await NetMasterAPI.getAgents();
```

#### 2. `charts.js` - Gestione Grafici
```javascript
// Esempio di utilizzo
NetMasterCharts.createCpuChart('cpuChart');
NetMasterCharts.updateChart('cpuChart', realTimeData);
```

#### 3. `dashboard.js` - Logica Principale
```javascript
// Esempio di utilizzo
Dashboard.init();
Dashboard.loadSection('overview');
```

## 📡 API Endpoints

### Statistiche Sistema
```http
GET /api/stats
Authorization: Basic YWRtaW46cGFzc3dvcmQ=

Response:
{
  "total_agents": 3,
  "avg_cpu": 45.2,
  "avg_memory": 67.8,
  "avg_disk": 23.4,
  "active_alerts": 2
}
```

### Dati Real-time
```http
GET /api/realtime?timespan=6h
Authorization: Basic YWRtaW46cGFzc3dvcmQ=

Response:
[
  {
    "timestamp": 1690200000000,
    "cpu": 45.2,
    "memory": 67.8,
    "disk": 23.4
  }
]
```

### Lista Agent
```http
GET /api/agents
Authorization: Basic YWRtaW46cGFzc3dvcmQ=

Response:
[
  {
    "id": 1,
    "hostname": "PC-UFFICIO-01",
    "ip_address": "192.168.1.100",
    "cpu_percent": 45.2,
    "memory_percent": 67.8,
    "disk_percent": 23.4,
    "status": "online"
  }
]
```

### Avvisi Sistema
```http
GET /api/alerts
Authorization: Basic YWRtaW46cGFzc3dvcmQ=

Response:
[
  {
    "id": "1",
    "type": "cpu",
    "severity": "warning",
    "title": "CPU Elevata",
    "message": "PC-UFFICIO-02: CPU al 78.5%",
    "timestamp": 1690200000,
    "active": true
  }
]
```

## 🔧 Personalizzazione

### Temi e Colori
Modifica `css/dashboard.css` per personalizzare:
```css
:root {
  --primary-color: #2563eb;
  --secondary-color: #64748b;
  --success-color: #10b981;
  --warning-color: #f59e0b;
  --error-color: #ef4444;
}
```

### Configurazione Grafici
Modifica `js/charts.js` per personalizzare:
```javascript
// Intervallo di aggiornamento (millisecondi)
const UPDATE_INTERVAL = 30000; // 30 secondi

// Colori grafici
const CHART_COLORS = {
  cpu: '#06b6d4',
  memory: '#f59e0b',
  disk: '#10b981'
};
```

## 🐛 Troubleshooting

### Problemi Comuni

#### 1. Dashboard non si carica
- **Verifica**: Server attivo su porta 5000
- **Soluzione**: `python server_test.py`

#### 2. Errore 404 su file CSS/JS
- **Causa**: Routing file statici non configurato
- **Soluzione**: Verificare endpoint `/css/` e `/js/` nel server

#### 3. Errore 401 Unauthorized
- **Causa**: Credenziali non corrette
- **Soluzione**: Username `admin`, Password `password`

#### 4. Grafici non si aggiornano
- **Causa**: Problemi di connessione API
- **Soluzione**: Controllare console browser (F12)

### Log di Debug
```bash
# Visualizza log del server
tail -f logs/server.log

# Debug JavaScript nel browser
# Apri DevTools (F12) > Console
```

## 🔒 Sicurezza

### Autenticazione
- Autenticazione HTTP Basic integrata
- Credenziali configurabili tramite variabili d'ambiente
- Rate limiting su tutte le API

### HTTPS (Produzione)
```bash
# Avvia con HTTPS (certificati auto-firmati)
python server.py  # HTTPS automatico se certificati disponibili
```

### Validazione Input
- Sanitizzazione automatica di tutti gli input
- Validazione JSON rigorosa
- Protezione contro attacchi XSS e injection

## 📱 Compatibilità

### Browser Supportati
- ✅ **Chrome** 90+
- ✅ **Firefox** 88+
- ✅ **Safari** 14+
- ✅ **Edge** 90+

### Dispositivi
- ✅ **Desktop**: Esperienza completa
- ✅ **Tablet**: Layout responsive
- ✅ **Mobile**: Interfaccia ottimizzata

## 🚀 Prossimi Sviluppi

### Funzionalità Pianificate
- [ ] **WebSocket**: Aggiornamenti real-time senza polling
- [ ] **Notifiche Push**: Avvisi browser nativi
- [ ] **Dashboard Personalizzabili**: Widget drag-and-drop
- [ ] **Reportistica Avanzata**: PDF automatici
- [ ] **Multi-tenancy**: Gestione più organizzazioni
- [ ] **Mobile App**: Applicazione nativa iOS/Android

### Miglioramenti UX
- [ ] **Dark Mode**: Tema scuro automatico
- [ ] **Internazionalizzazione**: Supporto multi-lingua
- [ ] **Accessibilità**: Conformità WCAG 2.1
- [ ] **Performance**: Lazy loading e caching

## 📞 Supporto

Per assistenza tecnica o segnalazione bug:
- **Documentazione**: Consulta questo file
- **Log**: Controlla `logs/server.log`
- **Debug**: Usa DevTools browser (F12)

---

**NetMaster Dashboard v1.0.0**  
*Sistema di Monitoraggio Rete Locale*  
*Sviluppato con ❤️ per il monitoraggio efficiente*
