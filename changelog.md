# Changelog

Tutte le modifiche rilevanti a questo progetto saranno documentate in questo file.

Il formato si basa su [Keep a Changelog](https://keepachangelog.com/it-IT/1.0.0/).

## [2.0.0] - In Sviluppo

### Aggiunto

- **Refactoring Modulare**: Introdotto il modulo `database.py` per astrarre completamente la gestione del database SQLite, separando la logica di accesso ai dati da quella di business.
- **Test di Convalida**: Aggiunti test funzionali per verificare la corretta comunicazione tra server e agent dopo il refactoring.

### Modificato

- **Architettura Server**: `server.py` è stato completamente rifattorizzato per utilizzare esclusivamente il modulo `database.py`, migliorando la leggibilità e la manutenibilità.
- **Architettura Agent**: `agent.py` è stato migliorato per inviare credenziali di autenticazione e gestire in modo più robusto gli errori di connessione e autenticazione.
- **Standardizzazione API**: Tutti gli endpoint del server ora utilizzano il prefisso `/api` per coerenza (es. `/report` è diventato `/api/report`).
- **Configurazione**: Il file `config.json` è stato aggiornato per includere la password in chiaro, necessaria all'agent, e il server è stato modificato per non rimuoverla più dopo l'hashing.

### Risolto

- **Stabilità del Sistema**: Risolti numerosi bug legati a file corrotti, configurazioni errate (porta, URL) e conflitti di gestione della configurazione tra server e agent.
- **Connessione Agent-Server**: Risolti i problemi che impedivano all'agent di connettersi e inviare dati al server.

## [1.0.0] - 2025-07-03

### Aggiunto

- **Struttura Iniziale**: Creazione della struttura base del progetto con `server.py`, `agent.py`, e `monitor_gui.py`.
- **Script di Avvio**: Implementati script batch (`.bat`) per avvio, test e debug.
- **Configurazione**: Gestione della configurazione tramite `config.json`.
- **Database**: Implementato sistema di archiviazione dati con SQLite.
- **API Endpoints**: Aggiunti endpoint per la ricezione di dati, lo storico e la configurazione.
- **Sistema di Notifiche**: Aggiunto sistema di notifiche email basato su soglie.
- **Logging Avanzato**: Implementato sistema di logging con rotazione dei file.

### Modificato

- **Sicurezza**: Implementato hashing delle password con `bcrypt`.
- **Gestione Errori**: Aggiunte classi di errore personalizzate e handler dedicati.
- **Validazione Dati**: Migliorata la validazione dei dati in ingresso.
