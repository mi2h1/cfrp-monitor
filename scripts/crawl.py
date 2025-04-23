#!/usr/bin/env python3
import os, yaml, json, datetime, pathlib, feedparser, requests
from supabase import create_client, Client
from dateutil import parser as dtparser

# ── Supabase ──────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── 日付フォルダ ───────────────────────────────────────
TODAY = datetime.date.today()
RAW_DIR = pathlib.Path("raw") / TODAY.isoformat()
RAW_DIR.mkdir(parents=True, exist_ok=True)

def save_raw(name: str, data):
    json.dump(data, (RAW_DIR / f"{name}.json").open("w", encoding="utf-8"),
              ensure_ascii=False, indent=2, default=str)

def safe_date(txt: str | None):
    try:
        return dtparser.parse(txt).date().isoformat() if txt else None
    except Exception:
        return None

def upsert_row(row: dict):
    resp = supabase.table("items").upsert(row, on_conflict="url").execute()
    err = getattr(resp, "error", None) or (resp.get("error") if isinstance(resp, dict) else None)
    print("UPSERT", "ERROR:" if err else "OK:", err or row["url"])

# ── NewsAPI ハンドラ ────────────────────────────────────
def handle_newsapi(src: dict):
    key = os.getenv("NEWSAPI_KEY")
    if not key:
        print("⚠️  NEWSAPI_KEY 未設定 → skip:", src["name"]); return

    qinfo   = src["newsapi_query"]
    days    = int(qinfo.get("days_back", 7))             # ← デフォ 7 日
    params  = {
        "domains" : qinfo.get("domains", ""),
        "pageSize": qinfo.get("pageSize", 100),
        "from"    : (TODAY - datetime.timedelta(days=days)).isoformat(),
        "language": qinfo.get("language", "en"),
        "sortBy"  : "publishedAt",
        "apiKey"  : key,
    }
    q_word = qinfo.get("q", "").strip()
    if q_word:                          # 空なら送らない
        params["q"] = q_word

    r = requests.get("https://newsapi.org/v2/everything", params=params, timeout=30)
    data = r.json()
    save_raw(f'{src["name"]}-newsapi', data)

    print(f"▶ NewsAPI {src['name']} → status:{data.get('status')}  articles:{len(data.get('articles', []))}")

    if data.get("status") != "ok":
        return

    for art in data.get("articles", []):
        upsert_row({
            "src_type": src.get("category"),
            "title"   : art.get("title"),
            "url"     : art.get("url"),
            "pub_date": safe_date(art.get("publishedAt")),
        })

# ── シード読み込み ─────────────────────────────────────
with open("seed_sources.yml", encoding="utf-8") as f:
    seeds = yaml.safe_load(f)

# ── メインループ ──────────────────────────────────────
for s in seeds:
    if s.get("acquisition_mode") != "auto":
        continue

    if "urls" in s:                                  # RSS
        for url in s["urls"]:
            feed = feedparser.parse(url)
            save_raw(s["name"], feed)
            for e in feed.entries:
                upsert_row({
                    "src_type": s["category"],
                    "title"   : e.get("title"),
                    "url"     : e.get("link"),
                    "pub_date": safe_date(e.get("published") or e.get("updated")),
                })

    elif "api" in s:                                 # Atom / XML API
        xml = requests.get(s["api"], timeout=30).text
        feed = feedparser.parse(xml)
        save_raw(s["name"], feed)
        for e in feed.entries:
            upsert_row({
                "src_type": s["category"],
                "title"   : e.get("title"),
                "url"     : e.get("link") or e.get("id"),
                "pub_date": safe_date(e.get("published") or e.get("updated")),
            })

    elif "newsapi_query" in s:                       # NewsAPI
        handle_newsapi(s)

print("✅ crawl finished")
