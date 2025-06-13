# elasticsearch-analyzer

Een eenvoudige Flask-webapplicatie om data uit Elasticsearch te exporteren naar CSV, met dag-over-dag analyses en markeringen. Deze tool biedt nu ook de mogelijkheid om Elasticsearch-clusters dynamisch toe te voegen en te beheren via de webinterface.

---

## Inhoud van de repository

* `app.py`          – De Flask-applicatie met alle logica voor query, verwerking en export, inclusief het dynamisch laden en opslaan van clusterconfiguraties.
* `templates/`      – Map met de HTML-template `index.html` voor het formulier en de functionaliteit voor het toevoegen van clusters.
* `clusters.json`   – **NIEUW:** Dit bestand slaat de configuraties van je Elasticsearch-clusters op. Het wordt automatisch aangemaakt/bijgewerkt door de applicatie.
* `requirements.txt`– Alle Python-dependencies.
* `.env.example`    – Voorbeeld configuratiebestand (copy & paste naar `.env`).
* `.gitignore`      – Bestanden en mappen die niet in Git worden opgenomen.
* `LICENSE`         – License (bijv. MIT).

---

## Quickstart

1.  **Repo klonen**

    ```bash
    git clone [https://github.com/stallieman/elasticsearch-analyzer.git](https://github.com/stallieman/elasticsearch-analyzer.git)
    cd elasticsearch-analyzer
    ```

2.  **Virtuele omgeving opzetten**

    ```bash
    python -m venv venv
    # Windows PowerShell:
    .\venv\Scripts\Activate.ps1
    # (Linux/macOS: source venv/bin/activate)
    ```

3.  **Dependencies installeren**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuratie**

    * Kopieer het voorbeeldbestand:

        ```bash
        cp .env.example .env
        ```
    * Open `.env` en vul in (let op: Elasticsearch cluster URL's worden nu beheerd via de UI en `clusters.json`):

        ```dotenv
        ES_USER=jouw_gebruikersnaam
        ES_MAN=jouw_wachtwoord
        CA_PATH=pad/naar/rootca.man.wpol.nl.cer
        ```
    * **Op macOS (zsh):** voeg deze variabelen toe aan `~/.zshrc` en laad het opnieuw:

        ```bash
        echo 'export ES_USER="jouw_gebruikersnaam"' >> ~/.zshrc
        echo 'export ES_MAN="jouw_wachtwoord"' >> ~/.zshrc
        echo 'export CA_PATH="/pad/naar/rootca.man.wpol.nl.cer"' >> ~/.zshrc
        source ~/.zshrc
        ```

5.  **Runnen**

    ```bash
    # Optioneel: debug mode (handig voor ontwikkeling)
    $env:FLASK_DEBUG=1 # PowerShell
    # Start de app
    flask run --host=127.0.0.1 --port=5000
    ```

6.  **Gebruik**

    * Open in je browser `http://127.0.0.1:5000/`.
    * **Clusters Beheren:**
        * Onderaan de pagina vind je een formulier om **nieuwe Elasticsearch clusters toe te voegen**. Voer een **Naam** (bijv. `Dev Cluster`) en de volledige **URL** (bijv. `https://your-dev-es:9243`) in.
        * Na het toevoegen verschijnt het cluster direct in de dropdown-lijst voor export. De configuraties worden opgeslagen in `clusters.json`.
    * **Data Exporteren:**
        * Kies het gewenste cluster uit de dropdown.
        * Vul het index-patroon (bijv. `desktop_servers-*`), de veldnaam voor aggregatie (bijv. `machine.name`) en het aantal dagen (1–7) in.
        * **Belangrijk:** De meest recente dag in de export is altijd **gisteren**, om ervoor te zorgen dat alle data van de laatste volledige dag is verwerkt.
        * Kies voor "Alle data" of "Alleen dalers (↓)".
        * Klik op **Exporteer als CSV**.

7.  **CSV openen in Excel**

    * Importeer als UTF-8 CSV ([Power Query of Legacy-wizard](https://support.microsoft.com/nl-nl/office/tekstbestanden-importeren-of-exporteren-tekst-of-csv-bestanden-importeren-of-exporteren-5250ee63-3982-4113-d49e-d7f999999999) - *URL is een voorbeeld, pas deze aan naar een relevante Microsoft/Office support pagina als je die hebt*).
    * De kolomkoppen zijn de datums in `YYYY-MM-DD` formaat.

---

## Extra hulpprogramma's

* **Black** formatter:

    ```bash
    pip install black
    black app.py
    ```

---

## License

Zie het `LICENSE`-bestand voor de volledige licentievoorwaarden.