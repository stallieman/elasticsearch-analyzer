**elasticsearch-analyzer**

Een eenvoudige Flask-webapplicatie om data uit Elasticsearch te exporteren naar CSV of XLSX, met dag-over-dag analyses en markeringen.

---

## Inhoud van de repository

* `app.py`       	– De Flask-applicatie met alle logica voor query, verwerking en export.
* `templates/`   	– Map met de HTML-template `index.html` voor het formulier.
* `requirements.txt`  – Alle Python-dependencies.
* `.env.example`  	– Voorbeeld configuratiebestand (copy & paste naar `.env`).
* `.gitignore`    	– Bestanden en mappen die niet in Git worden opgenomen.
* `LICENSE`       	– License (bijv. MIT).

---

## Quickstart

1. **Repo klonen**

   ```bash
   git clone https://github.com/stallieman/elasticsearch-analyzer.git
   cd elasticsearch-analyzer
   ```

2. **Virtuele omgeving opzetten**

   ```bash
   python -m venv venv
   # Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # (Linux/macOS: source venv/bin/activate)
   ```

3. **Dependencies installeren**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configuratie**

   * Kopieer het voorbeeldbestand:

     ```bash
     cp .env.example .env
     ```
   * Open `.env` en vul in:

     ```dotenv
     ES_USER= jouw_gebruikersnaam
     ES_MAN=  jouw_wachtwoord
     CA_PATH= pad/naar/rootca.man.wpol.nl.cer
     ```
   * **Op macOS (zsh):** voeg deze variabelen toe aan `~/.zshrc` en laad het opnieuw:

     ```bash
     echo 'export ES_USER="jouw_gebruikersnaam"' >> ~/.zshrc
     echo 'export ES_MAN="jouw_wachtwoord"' >> ~/.zshrc
     echo 'export CA_PATH="/pad/naar/rootca.man.wpol.nl.cer"' >> ~/.zshrc
     source ~/.zshrc
     ```

5. **Runnen** **Runnen** **Runnen**

   ```bash
   # Optioneel: debug mode
   $env:FLASK_DEBUG=1  # PowerShell
   # Start de app
   flask run --host=127.0.0.1 --port=5000
   ```

6. **Gebruik**

   * Open in je browser `http://127.0.0.1:5000/`.
   * Kies cluster, index-patroon, veldnaam, aantal dagen (1–7).
   * Klik op **Export alle data** of **Export alleen dalers**.

7. **CSV openen in Excel**

   * Importeer als UTF-8 CSV ([Power Query of Legacy-wizard](#)).
   * Of download XLSX (indien beschikbaar).

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
