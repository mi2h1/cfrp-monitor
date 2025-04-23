#!/usr/bin/env python3
import os, yaml, json, datetime, pathlib, feedparser, requests
from supabase import create_client, Client
from dateutil import parser as dtparser      # requirements.txt に python-dateutil を追加

# ── Supabase クライアント ──────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── きょうの日付ごとの raw 保存先 ─────────────────────
TODAY = datetime.date.today().isoformat()
RAW_DIR = pathlib.Path("raw") / TODAY
RAW_DIR.mkdir(parents=True, exist_ok=True)

def save_raw(name: str, data):
    """フィード全文を JSON で保存（非 JSON 型は文字列化）"""
    path = RAW_DIR / f"{name}.json"
    json.dump(data, path.open("w", encoding="utf-8"),
              ensure_ascii=False, indent=2, default=str)

def safe_date(text: str | None):
    """文字列を YYYY-MM-DD に変換。失敗したら None"""
    if not text:
        return None
    try:
        return dtparser.parse(text).date().isoformat()
    except Exception:
        return None

def upsert_row(row: dict):
    """Supabase upsert + 成否ログ"""
    resp = supabase.table("items").upsert(row, on_conflict="url").execute()

    err = getattr(resp, "error", None)
    if err is None and isinstance(resp, dict):
        err = resp.get("error")

    if err:
        print("UPSERT ERROR:", err, "row:", row)
    else:
        print("UPSERT OK:", row["url"])

# ---------- ★ NewsAPI 用関数 -------------------------------------------
def handle_newsapi(source: dict):
    """NewsAPI で取得 → raw 保存 → items へ upsert"""
    if not os.getenv("NEWSAPI_KEY"):
        print("⚠️  NEWSAPI_KEY が未設定なのでスキップ:", source["name"])
        return

    qinfo   = source["newsapi_query"]
    params  = {
        "q"       : qinfo.get("q", ""),
        "domains" : qinfo.get("domains", ""),
        "pageSize": qinfo.get("pageSize", 100),
        "from"    : TODAY,            # 当日分に絞る
        "language": qinfo.get("language", "en"),
        "apiKey"  : os.getenv("NEWSAPI_KEY"),
    }
    r = requests.get("https://newsapi.org/v2/everything", params=params, timeout=30)
    data = r.json()
    save_raw(f'{source["name"]}-newsapi', data)   # raw 保存

    if data.get("status") != "ok":
        print("NewsAPI ERROR:", data)
        return

    for art in data.get("articles", []):
        row = {
            "src_type": source.get("category"),
            "title"   : art.get("title"),
            "url"     : art.get("url"),
            "pub_date": safe_date(art.get("publishedAt")),
        }
        upsert_row(row)
# ----------------------------------------------------------------------

# ── シード読み込み ─────────────────────────────────────
with open("seed_sources.yml", encoding="utf-8") as f:
    seeds = yaml.safe_load(f)

# ── メインループ ──────────────────────────────────────
for s in seeds:
    if s.get("acquisition_mode") != "auto":
        continue

    # 1. RSS フィード ----------------------------------------------------
    if "urls" in s:
        for url in s["urls"]:
            feed = feedparser.parse(url)
            save_raw(s["name"], feed)

            for e in feed.entries:
                row = {
                    "src_type": s.get("category"),
                    "title"   : e.get("title"),
                    "url"     : e.get("link"),
                    "pub_date": safe_date(e.get("published") or e.get("updated")),
                }
                upsert_row(row)

    # 2. Atom / 独自 API （テキスト → feedparser）------------------------
    elif "api" in s:
        resp = requests.get(s["api"], timeout=30)
        feed = feedparser.parse(resp.text)
        save_raw(s["name"], feed)

        for e in feed.entries:
            row = {
                "src_type": s.get("category"),
                "title"   : e.get("title"),
                "url"     : e.get("link") or e.get("id"),
                "pub_date": safe_date(e.get("published") or e.get("updated")),
            }
            upsert_row(row)

    # 3. ★ NewsAPI ------------------------------------------------------
    elif "newsapi_query" in s:
        handle_newsapi(s)

print("✅ done!")
