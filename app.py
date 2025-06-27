import os
import json
import re
from flask import Flask, render_template, request, Response, redirect, url_for
from elasticsearch import Elasticsearch, exceptions as es_exceptions
from ssl import create_default_context
from dotenv import load_dotenv
from datetime import datetime, timedelta, time
import pandas as pd

# ─── Load environment ─────────────────────────────────────────
load_dotenv()
CA_PATH      = os.getenv("CA_PATH")
ES_USER      = os.getenv("ES_USER")
ES_PASS      = os.getenv("ES_MAN")
DEFAULT_INDEX = os.getenv("INDEX_PAT")

# ─── clusters.json helper ──────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
CLUSTER_FILE  = os.path.join(BASE_DIR, "clusters.json")

def load_clusters():
    if not os.path.exists(CLUSTER_FILE):
        return {}
    try:
        text = open(CLUSTER_FILE).read().strip()
        return json.loads(text) if text else {}
    except json.JSONDecodeError:
        print("clusters.json is corrupt; starting empty")
        return {}

def save_clusters(data):
    with open(CLUSTER_FILE, "w") as f:
        json.dump(data, f, indent=4)

CLUSTERS = load_clusters()

def es_connect(url):
    ctx = create_default_context(cafile=CA_PATH)
    return Elasticsearch([url], basic_auth=(ES_USER, ES_PASS), ssl_context=ctx)

# ─── Flask app ─────────────────────────────────────────────────
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    global CLUSTERS
    CLUSTERS = load_clusters()
    return render_template("index.html", clusters=CLUSTERS, default_index=DEFAULT_INDEX)

@app.route("/add_cluster", methods=["POST"])
def add_cluster():
    name = request.form["cluster_name"].strip()
    url  = request.form["cluster_url"].strip()
    if not name or not url:
        return Response("❗ Cluster naam en URL zijn verplicht.", status=400)
    if not (url.startswith("http://") or url.startswith("https://")):
        return Response("❗ Cluster URL moet beginnen met http:// of https://", status=400)
    global CLUSTERS
    if name in CLUSTERS:
        return redirect(url_for("home", message="Cluster bestaat al", status="error"))
    CLUSTERS[name] = url
    save_clusters(CLUSTERS)
    return redirect(url_for("home", message="Cluster toegevoegd!", status="success"))

# ─── Export endpoint ────────────────────────────────────────────
@app.route("/export", methods=["POST"])
def export():
    cluster_key    = request.form["cluster"]
    index_pat      = request.form["index_pat"]
    agg_field      = request.form["field_name"].strip()
    filter_field   = request.form.get("filter_field", "").strip()
    filter_pattern = request.form.get("filter_pattern", "").strip()
    days           = int(request.form["days"])
    action         = request.form.get("action", "all")

    # ── Basic validation ─────────────────────────────────────────
    if cluster_key not in CLUSTERS:
        return Response("❗ Ongeldig cluster gekozen.", status=400)
    if days < 1 or days > 7:
        return Response("❗ Aantal dagen moet tussen 1 en 7 liggen.", status=400)
    if not re.match(r"^[\w\.\-]+$", agg_field):
        return Response("❗ Ongeldig aggregatie-veld.", status=400)
    if filter_field and not re.match(r"^[\w\.\-]+$", filter_field):
        return Response("❗ Ongeldig filter-veld.", status=400)
    if filter_pattern and not re.match(r"^[\w\.\-\*@\?]+$", filter_pattern):
        return Response("❗ Ongeldig filter-patroon.", status=400)
    # ───────────────────────────────────────────────────────────────

    es = es_connect(CLUSTERS[cluster_key])

    # ── Date range ────────────────────────────────────────────────
    yesterday = (datetime.utcnow() - timedelta(days=1)).date()
    start_dt  = datetime.combine(yesterday - timedelta(days=days-1), time.min)
    end_dt    = datetime.combine(yesterday, time.max).replace(microsecond=999959)

    # ── Build filters ─────────────────────────────────────────────
    filters = [
        {"range": {"@timestamp": {"gte": start_dt.isoformat(), "lte": end_dt.isoformat()}}}
    ]
    if filter_field and filter_pattern:
        if "*" in filter_pattern or "?" in filter_pattern:
            filters.append({
                "wildcard": {filter_field: {"value": filter_pattern}}
            })
        else:
            filters.append({
                "term": {filter_field: filter_pattern}
            })
    # ───────────────────────────────────────────────────────────────

    # ── Aggregation query ────────────────────────────────────────
    body = {
        "size": 0,
        "query": {"bool": {"filter": filters}},
        "aggs": {
            "by_field": {
                "terms": {"field": agg_field, "size": 10000},
                "aggs": {
                    "per_day": {
                        "date_histogram": {
                            "field": "@timestamp",
                            "calendar_interval": "day",
                            "min_doc_count": 0,
                            "extended_bounds": {
                                "min": start_dt.isoformat(),
                                "max": end_dt.isoformat()
                            }
                        }
                    }
                }
            }
        }
    }

    try:
        res = es.search(index=index_pat, body=body)
    except es_exceptions.BadRequestError as e:
        print(json.dumps(e.info, indent=2))
        return Response("❗ Elasticsearch BadRequestError. Zie server-console voor details.", status=400)

    buckets = res.body.get("aggregations", {}).get("by_field", {}).get("buckets", [])
    if not buckets:
        return Response(f"❗ Geen data gevonden voor '{agg_field}'.", status=400)

    # ── Build DataFrame & CSV ─────────────────────────────────────
    dates = [(start_dt.date() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
    records = []
    for b in buckets:
        row = {"field": b["key"]}
        for day in b["per_day"]["buckets"]:
            dt = day["key_as_string"][:10]
            row[dt] = day["doc_count"]
        records.append(row)

    df = pd.DataFrame.from_records(records).set_index("field").reindex(columns=dates, fill_value=0)
    diff = df.diff(axis=1)
    df_disp = df.astype(str)
    for col in dates[1:]:
        df_disp[col] = df_disp[col] + diff[col].apply(lambda x: "↓" if x < 0 else "")

    if action == "decreasing":
        df_disp = df_disp[(diff < 0).any(axis=1)]

    df_disp = df_disp.reset_index()
    csv_bytes = df_disp.to_csv(index=False).encode("utf-8-sig")
    filename = f"export_{agg_field}_{days}d"
    if action == "decreasing":
        filename += "_decreasing"
    filename += ".csv"

    return Response(
        csv_bytes,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ─── Run ───────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
