# NetMaster Monitoring Suite

**NetMaster** è una suite software client-server robusta e modulare, progettata per il monitoraggio delle performance di sistemi su una rete locale. Il server centrale raccoglie, memorizza e gestisce i dati inviati dagli agent, offrendo un'architettura scalabile e facilmente manutenibile.

## Architettura e Design

Il progetto segue un'architettura moderna basata sulla **separazione delle responsabilità**:

- **`server.py`**: Il cuore dell'applicazione. Gestisce le richieste API, l'autenticazione e la logica di business, orchestrando gli altri moduli.
- **`agent.py`**: L'agent leggero da installare sulle macchine client. Raccoglie metriche di sistema (CPU, memoria, disco) e le invia al server in modo sicuro.
- **`database.py`**: Un modulo dedicato che astrae tutta la logica di interazione con il database SQLite. Il server non interagisce mai direttamente con il DB, ma solo attraverso questo modulo.
- **`config.json`**: Un file di configurazione centralizzato per gestire le impostazioni di server, agent e credenziali in un unico posto.

## Funzionalità Principali

- **Architettura Modulare**: Codice pulito e disaccoppiato per una facile manutenzione e scalabilità.
- **Autenticazione Sicura**: Tutti gli endpoint API sono protetti da autenticazione Basic. Le password sono gestite in modo sicuro tramite hashing con `bcrypt`.
- **Database Robusto**: Gestione del database SQLite centralizzata nel modulo `database.py`.
- **Logging Avanzato**: Sistema di logging con rotazione dei file per server e agent, che separa i log normali dagli errori per un debug più efficiente.
- **Configurazione Flessibile**: Un unico file `config.json` per configurare facilmente URL, intervalli di raccolta e credenziali.
- **Script di Avvio Semplificati**: File batch (`.bat`) per avviare, testare e debuggare i componenti del sistema con un solo comando.

## Prerequisiti

- Python 3.8+ installato
- Git (per clonare il repository)

## Installazione

1.  **Clona il repository**:
    ```bash
    git clone <URL_DEL_TUO_REPOSITORY>
    cd progetto-server
    ```

2.  **Crea e attiva l'ambiente virtuale**:
    ```bash
    python -m venv .venv
    .\.venv\Scripts\activate
    ```

3.  **Installa le dipendenze**:
    ```bash
    pip install -r requirements.txt
    ```

## Configurazione

Prima di avviare il sistema, configura il file `config.json`. Assicurati di impostare correttamente:

- `server_url`: L'URL completo a cui l'agent invierà i dati (es. `http://localhost:5000/api/report`).
- `username` e `password`: Le credenziali per l'autenticazione.
- `collection_interval`: L'intervallo in secondi tra un invio di dati e l'altro.

## Esecuzione

Utilizza gli script batch forniti per gestire l'applicazione:

-   **Avvia il server**: `start_server.bat`
-   **Avvia un agente**: `start_agent.bat`

I log verranno generati automaticamente nella cartella `logs/`.

## Endpoint API

Tutti gli endpoint richiedono autenticazione Basic.

- `POST /api/report`: Endpoint principale per la ricezione dei dati dagli agent.
- `GET /api/history`: Recupera lo storico dei dati di monitoraggio.
- `GET /api/thresholds`: Visualizza le soglie di allarme configurate.
- `POST /api/thresholds`: Imposta nuove soglie di allarme.
- `GET /api/notifications/config`: Visualizza la configurazione delle notifiche.
- `POST /api/notifications/config`: Imposta la configurazione delle notifiche.

## Licenza

Questo progetto è rilasciato sotto la Licenza MIT. Vedi il file `LICENSE` per maggiori dettagli.
