# Flask Index Compare Tool - Installatie Instructies

## Voor Eindgebruikers

### Systeemvereisten
- Windows 7 of hoger
- Minimaal 512MB vrij RAM
- Netwerkverbinding naar Elasticsearch clusters

### Installatie
1. **Download de applicatie files:**
   - `flask_index_compare_tool.exe` (hoofdapplicatie)
   - `start_app.bat` (optionele starter)

2. **Uitvoeren:**
   - **Optie A:** Dubbelklik op `start_app.bat` voor een gebruiksvriendelijke ervaring
   - **Optie B:** Dubbelklik direct op `flask_index_compare_tool.exe`

3. **Eerste gebruik:**
   - Een console venster opent zich
   - De browser opent automatisch naar http://127.0.0.1:5000
   - Als browser niet opent: ga handmatig naar http://127.0.0.1:5000

### Gebruik
1. **Inloggen:**
   - Voer je Elasticsearch gebruikersnaam en wachtwoord in

2. **Clusters beheren:**
   - Voeg Elasticsearch cluster URLs toe
   - Formaat: https://your-elasticsearch-url:9200

3. **Data exporteren:**
   - Selecteer een cluster
   - Voer index pattern in (bijv. `logstash-*`)
   - Kies veld voor aggregatie
   - Selecteer aantal dagen (1-7)
   - Download CSV resultaat

### Afsluiten
- **Optie A:** Gebruik "Shutdown" knop in webinterface
- **Optie B:** Druk Ctrl+C in console venster
- **Optie C:** Sluit console venster

### Troubleshooting

**Applicatie start niet:**
- Voer uit als Administrator
- Controleer Windows Defender/Antivirus
- Zorg dat poort 5000 vrij is

**Kan niet verbinden met Elasticsearch:**
- Controleer cluster URL (inclusief https://)
- Verificeer gebruikersnaam en wachtwoord
- Test netwerk connectiviteit

**Browser opent niet automatisch:**
- Ga handmatig naar: http://127.0.0.1:5000
- Controleer of andere software poort 5000 gebruikt

**CSV export faalt:**
- Controleer of er data is voor de geselecteerde periode
- Verificeer veldnamen (hoofdlettergevoelig)
- Controleer index pattern syntax

### Support
Voor technische ondersteuning, contacteer uw IT afdeling.

---
**Flask Index Compare Tool v1.0**  
Gebouwd met PyInstaller voor Windows deployment
