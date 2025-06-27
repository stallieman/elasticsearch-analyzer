import os, json, re
from flask import (
    Flask, render_template, request, Response,
    redirect, url_for, session, flash
)
from elasticsearch import Elasticsearch, exceptions as es_exceptions
from ssl import create_default_context
from dotenv import load_dotenv
from datetime import datetime, timedelta, time
import pandas as pd

# ─── Basisinstellingen ─────────────────────────────────────────
load_dotenv()
#CA_PATH       = os.getenv("CA_PATH")              # blijft uit .env komen
CA_PATH = os.path.join(os.path.dirname(__file__), "certificate", "rootca.man.wpol.nl.cer")
DEFAULT_INDEX = os.getenv("INDEX_PAT") or ""      # optioneel

# ─── cluster-beheer ────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
CLUSTER_FILE = os.path.join(BASE_DIR, "clusters.json")

def load_clusters():
    if not os.path.exists(CLUSTER_FILE):
        return {}
    try:
        txt = open(CLUSTER_FILE).read().strip()
        return json.loads(txt) if txt else {}
    except json.JSONDecodeError:
        print("clusters.json ongeldig — start leeg")
        return {}

def save_clusters(d):
    with open(CLUSTER_FILE, "w") as f:
        json.dump(d, f, indent=4)

CLUSTERS = load_clusters()

# ─── Elasticsearch connectie ───────────────────────────────────
def es_connect(url: str) -> Elasticsearch:
    ctx = create_default_context(cafile=CA_PATH)
    # gebruiker/wachtwoord uit de actieve sessie
    es_user = session.get("es_user")
    es_pass = session.get("es_pass")
    return Elasticsearch([url], basic_auth=(es_user, es_pass), ssl_context=ctx)

# ─── Flask-app ─────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "VERVANGDOOR_IETS_RANDOMS_EN_LANGS"

# ----------------------- LOGIN -------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("es_user", "").strip()
        pwd  = request.form.get("es_pass", "").strip()
        if not user or not pwd:
            flash("Gebruikersnaam en wachtwoord zijn verplicht.", "error")
            return render_template("login.html")
        session["es_user"] = user
        session["es_pass"] = pwd
        return redirect(url_for("home"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Je bent uitgelogd.", "success")
    return redirect(url_for("login"))

# ----------------------- HOME -------------------------------
@app.route("/", methods=["GET"])
def home():
    if "es_user" not in session:
        return redirect(url_for("login"))

    global CLUSTERS
    CLUSTERS = load_clusters()
    return render_template(
        "index.html",
        clusters=CLUSTERS,
        default_index=DEFAULT_INDEX
    )

# ------------------- CLUSTER TOEVOEGEN ----------------------
@app.route("/add_cluster", methods=["POST"])
def add_cluster():
    if "es_user" not in session:
        return redirect(url_for("login"))

    name = request.form["cluster_name"].strip()
    url  = request.form["cluster_url"].strip()
    if not name or not url:
        return Response("❗ Naam en URL verplicht.", 400)
    if not url.startswith(("http://", "https://")):
        return Response("❗ URL moet met http(s) beginnen.", 400)

    global CLUSTERS
    if name in CLUSTERS:
        return redirect(url_for("home", message="Cluster bestaat al", status="error"))

    CLUSTERS[name] = url
    save_clusters(CLUSTERS)
    return redirect(url_for("home", message="Cluster toegevoegd!", status="success"))

# --------------------- EXPORT -------------------------------
@app.route("/export", methods=["POST"])
def export():
    if "es_user" not in session:
        return redirect(url_for("login"))

    cluster_key    = request.form["cluster"]
    index_pat      = request.form["index_pat"]
    agg_field      = request.form["field_name"].strip()
    filter_field   = request.form.get("filter_field", "").strip()
    filter_pattern = request.form.get("filter_pattern", "").strip()
    days           = int(request.form["days"])
    action         = request.form.get("action", "all")

    # ── Validatie ────────────────────────────────────────────
    if cluster_key not in CLUSTERS:
        return Response("❗ Ongeldig cluster.", 400)
    if days < 1 or days > 7:
        return Response("❗ Dagen 1-7 toegestaan.", 400)
    if not re.match(r"^[\w.\-]+$", agg_field):
        return Response("❗ Ongeldig aggregatie-veld.", 400)
    if filter_field and not re.match(r"^[\w.\-]+$", filter_field):
        return Response("❗ Ongeldig filterveld.", 400)
    if filter_pattern and not re.match(r"^[\w.\-\*@\?]+$", filter_pattern):
        return Response("❗ Ongeldig patroon.", 400)

    es = es_connect(CLUSTERS[cluster_key])

    # Tijdsrange
    yest = (datetime.utcnow() - timedelta(days=1)).date()
    start_dt = datetime.combine(yest - timedelta(days=days - 1), time.min)
    end_dt   = datetime.combine(yest, time.max).replace(microsecond=999959)

    filters = [{
        "range": {"@timestamp": {"gte": start_dt.isoformat(), "lte": end_dt.isoformat()}}
    }]
    if filter_field and filter_pattern:
        filt = (
            {"wildcard": {filter_field: {"value": filter_pattern}}}
            if "*" in filter_pattern or "?" in filter_pattern
            else {"term": {filter_field: filter_pattern}}
        )
        filters.append(filt)

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
        return Response("❗ Elasticsearch BadRequestError – zie console.", 400)

    buckets = res.body.get("aggregations", {}).get("by_field", {}).get("buckets", [])
    if not buckets:
        return Response(f"❗ Geen data gevonden voor '{agg_field}'.", 400)

    dates = [(start_dt.date() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
    recs  = []
    for b in buckets:
        row = {"field": b["key"]}
        for d in b["per_day"]["buckets"]:
            row[d["key_as_string"][:10]] = d["doc_count"]
        recs.append(row)

    df = (pd.DataFrame.from_records(recs)
          .set_index("field")
          .reindex(columns=dates, fill_value=0))
    diff = df.diff(axis=1)
    out  = df.astype(str)
    for c in dates[1:]:
        out[c] += diff[c].apply(lambda x: "↓" if x < 0 else "")
    if action == "decreasing":
        out = out[(diff < 0).any(axis=1)]
    out = out.reset_index()

    csv_bytes = out.to_csv(index=False).encode("utf-8-sig")
    fn = f"export_{agg_field}_{days}d"
    if action == "decreasing":
        fn += "_decreasing"
    fn += ".csv"

    return Response(
        csv_bytes,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={fn}"}
    )

# --------------------- MAIN -------------------------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
