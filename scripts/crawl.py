#!/usr/bin/env python3
import os, yaml, json, datetime, pathlib, time
import requests, feedparser
from supabase import create_client, Client
from dateutil import parser as dtparser
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ── Supabase ───────────────────────────────────────────
SUPABASE_URL  = os.getenv("SUPABASE_URL")
SUPABASE_KEY  = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── 保存先フォルダ ────────────────────────────────────
TODAY    = datetime.date.today()
RAW_DIR  = pathlib.Path("raw") / TODAY.isoformat()
RAW_DIR.mkdir(parents=True, exist_ok=True)

UA_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CFRPbot/0.1)"}

# ── 共通セッション（リトライ 3 回、1→2→4 秒） ─────────
retry = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504, 429])
session = requests.Session()
session.headers.update(UA_HEADERS)
session.mount("https://", HTTPAdapter(max_retries=retry))
session.mount("http://",  HTTPAdapter(max_retries=retry))

# ── ユーティリティ ───────────────────────────────────
def save_raw(name: str, data):
    (RAW_DIR / f"{name}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8"
    )

def safe_date(txt: str | None):
    try:
        return dtparser.parse(txt).date().isoformat() if txt else None
    except Exception:
        return None

def upsert_row(row: dict):
    resp = supabase.table("items").upsert(row, on_conflict="url").execute()
    err  = getattr(resp, "error", None) or (resp.get("error") if isinstance(resp, dict) else None)
    print("UPSERT", "ERROR:" if err else "OK:", err or row["url"])

def fetch_rss(url: str):
    try:
        r = session.get(url, timeout=30)
        r.raise_for_status()
        return feedparser.parse(r.content)
    except Exception as e:
        print("⚠️ RSS fetch failed:", url, "->", e)
        return None

def fetch_xml(url: str):
    try:
        r = session.get(url, timeout=30)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print("⚠️ API fetch failed:", url, "->", e)
        return None

# ── シード読み込み ───────────────────────────────────
with open("seed_sources.yml", encoding="utf-8") as f:
    seeds = yaml.safe_load(f)

# ── メインループ ────────────────────────────────────
for src in seeds:
    if src.get("acquisition_mode") != "auto":
        continue

    # 1. RSS フィード --------------------------------------------------
    if "urls" in src:
        for url in src["urls"]:
            feed = fetch_rss(url)
            if not feed:
                continue
            save_raw(f'{src["name"]}-{url.split("/")[-1]}', feed)

            for e in feed.entries:
                upsert_row({
                    "src_type": src["category"],
                    "title"   : e.get("title"),
                    "url"     : e.get("link"),
                    "pub_date": safe_date(e.get("published") or e.get("updated")),
                })

    # 2. XML / Atom API ----------------------------------------------
    elif "api" in src:
        xml = fetch_xml(src["api"])
        if not xml:
            continue
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
