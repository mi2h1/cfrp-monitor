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

    # v2 と v1 どちらでも error を拾う
    err = getattr(resp, "error", None)
    if err is None and isinstance(resp, dict):
        err = resp.get("error")

    if err:
        print("UPSERT ERROR:", err, "row:", row)
    else:
        print("UPSERT OK:", row["url"])

# ── シード読み込み ─────────────────────────────────────
with open("seed_sources.yml", encoding="utf-8") as f:
    seeds = yaml.safe_load(f)

# ── メインループ ──────────────────────────────────────
for s in seeds:
    if s.get("acquisition_mode") != "auto":
        continue

    # 1. RSS フィード
    if "urls" in s:
        for url in s["urls"]:
            feed = feedparser.parse(url)
            save_raw(s["name"], feed)

            for e in feed.entries:
                row = {
                    "src_type": s.get("category"),
                    "title":    e.get("title"),
                    "url":      e.get("link"),
                    "pub_date": safe_date(e.get("published") or e.get("updated")),
                }
                upsert_row(row)

    # 2. API (RSS/Atom/XML テキスト想定)
    elif "api" in s:
        resp = requests.get(s["api"], timeout=30)
        feed = feedparser.parse(resp.text)
        save_raw(s["name"], feed)

        for e in feed.entries:
            row = {
                "src_type": s.get("category"),
                "title":    e.get("title"),
                # arXiv は <id> に DOI が入るので link が無ければ id を使用
                "url":      e.get("link") or e.get("id"),
                "pub_date": safe_date(e.get("published") or e.get("updated")),
            }
            upsert_row(row)

print("✅ done!")
