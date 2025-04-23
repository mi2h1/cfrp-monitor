#!/usr/bin/env python3
import os, yaml, json, datetime, pathlib, requests, feedparser
from supabase import create_client, Client
from dateutil import parser as dtparser

# ── Supabase 接続 ────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── 保存ディレクトリ ──────────────────────────────────
TODAY = datetime.date.today()
RAW_DIR = pathlib.Path("raw") / TODAY.isoformat()
RAW_DIR.mkdir(parents=True, exist_ok=True)

UA_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CFRPbot/0.1)"}

# ── ユーティリティ ───────────────────────────────────
def save_raw(name: str, data):
    """取得したフィードや API レスポンスを JSON で保存"""
    (RAW_DIR / f"{name}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8"
    )

def safe_date(txt: str | None):
    """文字列 → YYYY-MM-DD。失敗時 None"""
    try:
        return dtparser.parse(txt).date().isoformat() if txt else None
    except Exception:
        return None

def upsert_row(row: dict):
    """Supabase upsert と結果ログ出力"""
    resp = supabase.table("items").upsert(row, on_conflict="url").execute()
    err = getattr(resp, "error", None) or (resp.get("error") if isinstance(resp, dict) else None)
    print("UPSERT", "ERROR:" if err else "OK:", err or row["url"])

def fetch_rss(url: str):
    """UA ヘッダ付きで RSS を取得し feedparser で解析"""
    resp = requests.get(url, headers=UA_HEADERS, timeout=30)
    return feedparser.parse(resp.content)

# ── シード読み込み ───────────────────────────────────
with open("seed_sources.yml", encoding="utf-8") as f:
    seeds = yaml.safe_load(f)

# ── メインループ ────────────────────────────────────
for src in seeds:
    if src.get("acquisition_mode") != "auto":
        continue

    # 1. RSS フィード一覧 --------------------------------
    if "urls" in src:
        for url in src["urls"]:
            feed = fetch_rss(url)
            save_raw(f'{src["name"]}-{url.split("/")[-1]}', feed)

            for e in feed.entries:
                upsert_row({
                    "src_type": src["category"],
                    "title"   : e.get("title"),
                    "url"     : e.get("link"),
                    "pub_date": safe_date(e.get("published") or e.get("updated")),
                })

    # 2. XML / Atom API ----------------------------------
    elif "api" in src:
        xml = requests.get(src["api"], headers=UA_HEADERS, timeout=30).text
        feed = feedparser.parse(xml)
        save_raw(src["name"], feed)

        for e in feed.entries:
            upsert_row({
                "src_type": src["category"],
                "title"   : e.get("title"),
                "url"     : e.get("link") or e.get("id"),
                "pub_date": safe_date(e.get("published") or e.get("updated")),
            })

print("✅ crawl finished")
