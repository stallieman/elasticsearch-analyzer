# Flask Index Compare Tool - Productie Versie

## Installatie en Gebruik

### Voor Eindgebruikers (Windows VM)

1. **Download de applicatie:**
   - Download het `dist` folder met `flask_index_compare_tool.exe`
   - Kopieer deze naar een gewenste locatie op je computer

2. **Uitvoeren van de applicatie:**
   - Dubbelklik op `flask_index_compare_tool.exe`
   - Een console venster opent zich
   - De browser opent automatisch naar http://127.0.0.1:5000
   - Als de browser niet automatisch opent, ga handmatig naar: http://127.0.0.1:5000

3. **Afsluiten:**
   - Gebruik de "Shutdown" knop in de webinterface, OF
   - Druk Ctrl+C in het console venster, OF
   - Sluit het console venster

### Voor Ontwikkelaars - EXE Bouwen

1. **Vereisten:**
   - Python 3.8 of hoger
   - Alle packages uit requirements.txt

2. **EXE Bouwen:**
   ```cmd
   # Optie 1: Gebruik het batch script
   build_exe.bat
   
   # Optie 2: Handmatig bouwen
   pip install pyinstaller
   pyinstaller --clean production.spec
   ```

3. **Output:**
   - Het executable bestand komt in de `dist/` folder
   - Naam: `flask_index_compare_tool.exe`

## Functionaliteit

- **Elasticsearch Index Vergelijking:** Vergelijk data tussen verschillende dagen
- **CSV Export:** Exporteer resultaten naar CSV bestanden
- **Cluster Management:** Beheer meerdere Elasticsearch clusters
- **Veilige Verbindingen:** SSL certificaat ondersteuning
- **Web Interface:** Gebruiksvriendelijke browser interface

## Technische Details

- **Framework:** Flask (Python web framework)
- **Database:** Elasticsearch
- **Export:** Pandas voor CSV generatie
- **Security:** SSL/TLS ondersteuning met certificaten
- **Packaging:** PyInstaller voor executable

## Systeemvereisten

- **Besturingssysteem:** Windows 7 of hoger
- **Geheugen:** Minimaal 512MB RAM
- **Schijfruimte:** ~100MB voor de applicatie
- **Netwerk:** Toegang tot Elasticsearch clusters

## Troubleshooting

1. **Applicatie start niet:**
   - Controleer of alle bestanden in de dist folder aanwezig zijn
   - Voer uit als Administrator indien nodig

2. **Browser opent niet automatisch:**
   - Ga handmatig naar http://127.0.0.1:5000
   - Controleer of poort 5000 vrij is

3. **Kan niet verbinden met Elasticsearch:**
   - Controleer cluster URLs
   - Verificeer gebruikersnaam en wachtwoord
   - Controleer netwerk connectiviteit

4. **CSV export werkt niet:**
   - Controleer of er data beschikbaar is voor de geselecteerde periode
   - Verificeer veld namen (case-sensitive)

## Support

Voor vragen of problemen, contacteer de ontwikkelaar of IT support.
