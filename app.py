import os
from flask import Flask, render_template, request, Response, redirect, url_for
from elasticsearch import Elasticsearch
from ssl import create_default_context
from dotenv import load_dotenv
from datetime import datetime, timedelta, time # Importeer 'time'
import pandas as pd
import json


# 1. Load environment
load_dotenv()
CA_PATH = os.getenv("CA_PATH")
ES_USER = os.getenv("ES_USER")
ES_PASS = os.getenv("ES_MAN")

# --- NIEUWE CLUSTER BEHEER LOGICA ---
# 2. Constante voor het JSON-bestand
CLUSTER_FILE = "clusters.json"

# 3. Functie om clusters te laden
def load_clusters() -> dict:
    """Laadt clusterconfiguraties uit een JSON-bestand, of initialiseert met standaardwaarden."""
    if os.path.exists(CLUSTER_FILE):
        try:
            with open(CLUSTER_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"WAARSCHUWING: Fout bij het lezen van {CLUSTER_FILE}. Bestand is corrupt. Initialiseer met standaardclusters.")
            # Val terug op standaardclusters als het bestand corrupt is
            return {
                "apps": "https://prd-appsanddesktops-es.central.wpol.nl:9243",
                "backbone": "https://prd-backbone-es.central.wpol.nl:9243",
                "prd historical": "https://prd-historical-es.central.wpol.nl:9243",
            }
    # Als het bestand niet bestaat, retourneer de standaardclusters en sla ze op
    initial_clusters = {
        "apps": "https://prd-appsanddesktops-es.central.wpol.nl:9243",
        "backbone": "https://prd-backbone-es.central.wpol.nl:9243",
        "prd historical": "https://prd-historical-es.central.wpol.nl:9243",
    }
    save_clusters(initial_clusters) # Sla de initiële clusters op in het bestand
    return initial_clusters

# 4. Functie om clusters op te slaan
def save_clusters(clusters_dict: dict):
    """Slaat clusterconfiguraties op naar een JSON-bestand."""
    with open(CLUSTER_FILE, 'w') as f:
        json.dump(clusters_dict, f, indent=4)

# 5. Laad clusters bij het opstarten van de applicatie
CLUSTERS = load_clusters()
# --- EINDE NIEUWE CLUSTER BEHEER LOGICA ---


# 6. ES-connect helper (ongewijzigd)
def es_connect(url: str) -> Elasticsearch:
    ctx = create_default_context(cafile=CA_PATH)
    return Elasticsearch(
        [url],
        basic_auth=(ES_USER, ES_PASS),
        ssl_context=ctx,
    )


# 7. Flask-app initialiseren
app = Flask(__name__)


# 8. Home-route met formulier - AANGEPAST om CLUSTERS opnieuw te laden
@app.route("/", methods=["GET"])
def home():
    # Laad de clusters opnieuw om ervoor te zorgen dat de dropdown de meest recente clusters toont
    global CLUSTERS
    CLUSTERS = load_clusters()
    return render_template(
        "index.html",
        clusters=CLUSTERS,
        default_index=os.getenv("INDEX_PAT"),
    )

# 9. Nieuwe route voor het toevoegen van clusters
@app.route("/add_cluster", methods=["POST"])
def add_cluster():
    cluster_name = request.form["cluster_name"].strip()
    cluster_url = request.form["cluster_url"].strip()

    if not cluster_name or not cluster_url:
        return Response("❗ Cluster naam en URL zijn verplicht.", status=400)
    
    # Eenvoudige validatie van de URL
    if not (cluster_url.startswith("http://") or cluster_url.startswith("https://")):
        return Response("❗ Cluster URL moet beginnen met http:// of https://", status=400)

    global CLUSTERS # Zorg ervoor dat we de globale CLUSTERS variabele kunnen wijzigen
    if cluster_name in CLUSTERS:
        # Gebruik een query parameter om de foutmelding door te geven
        return redirect(url_for('home', message=f"Cluster '{cluster_name}' bestaat al.", status="error"))

    CLUSTERS[cluster_name] = cluster_url
    save_clusters(CLUSTERS) # Sla de bijgewerkte clusters op in het bestand
    print(f"DEBUG: Nieuw cluster toegevoegd: {cluster_name} - {cluster_url}")
    # Gebruik een query parameter om een succesmelding door te geven
    return redirect(url_for('home', message=f"Cluster '{cluster_name}' succesvol toegevoegd!", status="success"))


# 10. Export-route (ongeijzigd van vorige iteratie)
@app.route("/export", methods=["POST"])
def export():
    # a) Form-waarden inlezen
    cluster_key = request.form["cluster"]
    index_pat = request.form["index_pat"]
    field_name = request.form["field_name"]
    days = int(request.form["days"])
    action = request.form.get("action", "all")

    # ── Input-validatie (óók binnen de functie!) ──────────────
    import re

    if cluster_key not in CLUSTERS:
        return Response("❗ Ongeldig cluster gekozen.", status=400)
    if days < 1 or days > 7:
        return Response("❗ Aantal dagen moet tussen 1 en 7 liggen.", status=400)
    if not re.match(r"^[\w\.\-]+$", field_name):
        return Response("❗ Ongeldige veldnaam.", status=400)
    # ────────────────────────────────────────────────────────────

    # b) Verbinden met het gekozen cluster
    es = es_connect(CLUSTERS[cluster_key])

    # c) Datum-bereik bepalen - AANGEPAST: MEEST RECENTE DAG IS GISTEREN
    # Bepaal de datum van gisteren in UTC
    yesterday_utc_date = (datetime.utcnow() - timedelta(days=1)).date()

    # Bepaal het einde van gisteren in UTC (23:59:59.999999 van gisteren)
    end = datetime.combine(yesterday_utc_date, time.max).replace(microsecond=999999)

    # Bepaal de startdatum door 'days - 1' dagen terug te gaan vanaf gisteren
    start_date_for_query = yesterday_utc_date - timedelta(days=days - 1)
    # Bepaal het begin van die startdatum in UTC (00:00:00.000000)
    start = datetime.combine(start_date_for_query, time.min)

    # Print voor debug
    print(f"\nDEBUG: Huidige lokale tijd: {datetime.now().astimezone()}")
    print(f"DEBUG: Datum van gisteren (UTC): {yesterday_utc_date}")
    print(f"DEBUG: Berekend querybereik (UTC): GTE {start.isoformat()} | LTE {end.isoformat()}")

    # d) Aggregatie-body opbouwen
    body = {
        "size": 0,
        "query": {
            "range": {"@timestamp": {"gte": start.isoformat(), "lte": end.isoformat()}}
        },
        "aggs": {
            "by_field": {
                "terms": {"field": field_name, "size": 10000},
                "aggs": {
                    "per_day": {
                        "date_histogram": {
                            "field": "@timestamp",
                            "calendar_interval": "day",
                            "min_doc_count": 0,
                            "extended_bounds": {
                                "min": start.isoformat(),
                                "max": end.isoformat(),
                            },
                        }
                    }
                },
            }
        },
    }

    # e) Query uitvoeren
    res = es.search(index=index_pat, body=body)

    # --- DEBUGGING EN FOUTCONTROLE AANPASSINGEN ---
    print(f"\n--- Elasticsearch Response voor '{field_name}' op '{index_pat}' ---")
    try:
        print(json.dumps(res.body, indent=2))
    except TypeError as e:
        print(f"WAARSCHUWING: Kon Elasticsearch respons niet als JSON dumpen (TypeFout: {e}).")
        print(f"Raw respons type: {type(res.body)}")
        print(f"Raw respons (geen JSON, wellicht afgekort): {str(res.body)[:500]}...") # Print als string
    print("--------------------------------------------------")

    # Controleer of aggregaties terugkwamen
    if "aggregations" not in res.body:
        return Response(
            "❗ Geen aggregaties gevonden. Controleer of het index-patroon en de veldnaam correct zijn én er data is in de gekozen periode.",
            mimetype="text/plain",
            status=400,
        )

    # Controleer of de 'by_field' aggregatie en de 'buckets' erin bestaan en gevuld zijn
    if "by_field" not in res.body["aggregations"] or \
       "buckets" not in res.body["aggregations"]["by_field"] or \
       not res.body["aggregations"]["by_field"]["buckets"]:
        print(f"DEBUG: 'by_field' aggregatie of de 'buckets' zijn leeg of ontbreken.")
        return Response(
            f"❗ Geen data gevonden voor het veld '{field_name}' in de gekozen periode. Controleer de veldnaam of de periode.",
            mimetype="text/plain",
            status=400,
        )

    # f) Data omzetten naar DataFrame
    dates_for_columns = [(start.date() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
    records = []
    
    for bucket in res.body["aggregations"]["by_field"]["buckets"]:
        if "key" not in bucket:
            print(f"WAARSCHUWING: Bucket mist 'key' attribuut. Bucket overgeslagen: {bucket}")
            continue

        row = {"field": bucket["key"]}

        if "per_day" in bucket and "buckets" in bucket["per_day"]:
            for day_bucket in bucket["per_day"]["buckets"]:
                if "key_as_string" in day_bucket and "doc_count" in day_bucket:
                    datum = day_bucket["key_as_string"][:10]
                    row[datum] = day_bucket["doc_count"]
                else:
                    print(f"WAARSCHUWING: Day bucket mist 'key_as_string' of 'doc_count'. Day bucket details: {day_bucket}")
            
            records.append(row)
        else:
            print(f"WAARSCHUWING: Bucket mist 'per_day' aggregatie of zijn 'buckets'. Bucket overgeslagen: {bucket}")
    
    print(f"DEBUG: Records gebruikt voor DataFrame: {records}")

    if not records:
        print("DEBUG: De 'records' lijst is leeg na verwerking van Elasticsearch buckets. Kan geen DataFrame maken.")
        return Response(
            f"❗ Geen records kunnen genereren voor het veld '{field_name}'. Controleer de Elasticsearch-data of de aggregatie-resultaten.",
            mimetype="text/plain",
            status=400,
        )

    df_numeric = pd.DataFrame.from_records(records).set_index("field")
    df_numeric = df_numeric.reindex(columns=dates_for_columns, fill_value=0)

    # g) Bereken verschillen en maak display-versie met “↓”-markering
    diff = df_numeric.diff(axis=1)
    df_display = df_numeric.astype(str)
    for col in dates_for_columns[1:]:
        df_display[col] = df_display[col] + diff[col].apply(
            lambda x: "↓" if x < 0 else ""
        )

    # h) Indien “decreasing” alleen rijen met daling tonen
    if action == "decreasing":
        mask = (diff < 0).any(axis=1)
        df_display = df_display[mask]

    # Reset index zodat 'field' een kolom wordt
    df_display = df_display.reset_index()

    # 1) Maak CSV-string zonder index
    csv_str = df_display.to_csv(index=False)
    # 2) Voeg BOM (utf-8-sig) toe voor Excel
    csv_bytes = csv_str.encode("utf-8-sig")

    # Bestandsnaam bepalen, met suffix als “decreasing” gekozen is
    filename = f"export_{field_name}_{days}d"
    if action == "decreasing":
        filename += "_decreasing"
    filename += ".csv"

    # Returnen als attachment met juiste headers
    return Response(
        csv_bytes,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# 11. App-runner
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True) # Zet debug=True voor ontwikkeling