#!/usr/bin/env python3
import os, yaml, json, datetime, pathlib, feedparser, requests
from supabase import create_client, Client
from dateutil import parser as dtparser

SUPABASE_URL, SUPABASE_KEY = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TODAY = datetime.date.today()
RAW_DIR = pathlib.Path("raw") / TODAY.isoformat(); RAW_DIR.mkdir(parents=True, exist_ok=True)

def save_raw(name, data):
    json.dump(data, (RAW_DIR / f"{name}.json").open("w", encoding="utf-8"),
              ensure_ascii=False, indent=2, default=str)

def safe_date(txt):                       # YYYY-MM-DD 化
    try: return dtparser.parse(txt).date().isoformat() if txt else None
    except Exception: return None

def upsert_row(row):
    resp = supabase.table("items").upsert(row, on_conflict="url").execute()
    err = getattr(resp, "error", None) or (resp.get("error") if isinstance(resp, dict) else None)
    print("UPSERT", "ERROR:" if err else "OK:", err or row["url"])

# ---------- NewsAPI --------------------------------------------------
def handle_newsapi(src):
    key = os.getenv("NEWSAPI_KEY")
    if not key:
        print("⚠️  NEWSAPI_KEY 未設定 → skip:", src["name"]); return

    qinfo   = src["newsapi_query"]
    days    = int(qinfo.get("days_back", 1))        # デフォ 1 日
    params  = {
        "q"       : qinfo.get("q", ""),             # 空でも OK
        "domains" : qinfo.get("domains", ""),
        "pageSize": qinfo.get("pageSize", 100),
        "from"    : (TODAY - datetime.timedelta(days=days)).isoformat(),
        "language": qinfo.get("language", "en"),
        "sortBy"  : "publishedAt",
        "apiKey"  : key,
    }
    r = requests.get("https://newsapi.org/v2/everything", params=params, timeout=30)
    data = r.json()
    save_raw(f'{src["name"]}-newsapi', data)

    print(f"▶ NewsAPI {src['name']} → status: {data.get('status')}  articles: {len(data.get('articles', []))}")

    if data.get("status") != "ok":
        return                                      # APIキー誤りなど

    for art in data["articles"]:
        upsert_row({
            "src_type": src.get("category"),
            "title"   : art.get("title"),
            "url"     : art.get("url"),
            "pub_date": safe_date(art.get("publishedAt")),
        })
# --------------------------------------------------------------------


with open("seed_sources.yml", encoding="utf-8") as f:
    seeds = yaml.safe_load(f)

for s in seeds:
    if s.get("acquisition_mode") != "auto": continue

    if "urls" in s:                                  # RSS
        for url in s["urls"]:
            feed = feedparser.parse(url); save_raw(s["name"], feed)
            for e in feed.entries:
                upsert_row({
                    "src_type": s["category"],
                    "title":    e.get("title"),
                    "url":      e.get("link"),
                    "pub_date": safe_date(e.get("published") or e.get("updated")),
                })

    elif "api" in s:                                 # Atom/API
        feed = feedparser.parse(requests.get(s["api"], timeout=30).text)
        save_raw(s["name"], feed)
        for e in feed.entries:
            upsert_row({
                "src_type": s["category"],
                "title":    e.get("title"),
                "url":      e.get("link") or e.get("id"),
                "pub_date": safe_date(e.get("published") or e.get("updated")),
            })

    elif "newsapi_query" in s:                       # ★ NewsAPI
        handle_newsapi(s)

print("✅ done!")
