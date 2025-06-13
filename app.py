import os
from flask import Flask, render_template, request, Response
from elasticsearch import Elasticsearch
from ssl import create_default_context
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pandas as pd

# 1. Load environment
load_dotenv()
CA_PATH = os.getenv("CA_PATH")
ES_USER = os.getenv("ES_USER")
ES_PASS = os.getenv("ES_MAN")

# 2. Hardcoded clusters
CLUSTERS = {
    "apps": "https://prd-appsanddesktops-es.central.wpol.nl:9243",
    "backbone": "https://prd-backbone-es.central.wpol.nl:9243",
    "prd historical": "https://prd-historical-es.central.wpol.nl:9243",
}


# 3. ES-connect helper
def es_connect(url: str) -> Elasticsearch:
    ctx = create_default_context(cafile=CA_PATH)
    return Elasticsearch(
        [url],
        basic_auth=(ES_USER, ES_PASS),
        ssl_context=ctx,
    )


# 4. Flask-app initialiseren
app = Flask(__name__)


# 5. Home-route met formulier
@app.route("/", methods=["GET"])
def home():
    return render_template(
        "index.html",
        clusters=CLUSTERS,
        default_index=os.getenv("INDEX_PAT"),
    )


# 6. Export-route
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

    # c) Datum-bereik bepalen
    end = datetime.utcnow()
    start = end - timedelta(days=days - 1)

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

    # Controleer of aggregaties terugkwamen
    if "aggregations" not in res:
        return Response(
            "❗ Geen aggregaties gevonden. Controleer of het index-patroon en de veldnaam correct zijn én er data is in de gekozen periode.",
            mimetype="text/plain",
            status=400,
        )

    # f) Data omzetten naar DataFrame
    dates = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
    records = []
    for bucket in res["aggregations"]["by_field"]["buckets"]:
        row = {"field": bucket["key"]}
        for day_bucket in bucket["per_day"]["buckets"]:
            datum = day_bucket["key_as_string"][:10]
            row[datum] = day_bucket["doc_count"]
        records.append(row)

    df_numeric = pd.DataFrame.from_records(records).set_index("field")
    df_numeric = df_numeric.reindex(columns=dates, fill_value=0)

    # g) Bereken verschillen en maak display-versie met “↓”-markering
    diff = df_numeric.diff(axis=1)
    df_display = df_numeric.astype(str)
    for col in dates[1:]:
        df_display[col] = df_display[col] + diff[col].apply(
            lambda x: "↓" if x < 0 else ""
        )

    # h) Indien “decreasing” alleen rijen met daling tonen
    if action == "decreasing":
        mask = (diff < 0).any(axis=1)
        df_display = df_display[mask]

    # … na de “decreasing”-filter en vóór alles het export-deel …

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


# 7. App-runner
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
