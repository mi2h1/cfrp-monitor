#!/usr/bin/env python3
import os, yaml, json, datetime, pathlib
from supabase import create_client, Client
from dateutil import parser as dtparser
from fetcher import fetch_and_parse, slug, DEFAULT_CFG

# ----- Supabase ------------------------------------------------------------
supabase: Client = create_client(os.getenv("SUPABASE_URL"),
                                 os.getenv("SUPABASE_KEY"))

# ----- 保存ディレクトリ -----------------------------------------------------
today = datetime.date.today().isoformat()
RAW_DIR = pathlib.Path("raw") / today
RAW_DIR.mkdir(parents=True, exist_ok=True)

def save_raw(name: str, data):
    (RAW_DIR / f"{name}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8"
    )

def safe_date(txt):
    try: return dtparser.parse(txt).date().isoformat() if txt else None
    except Exception: return None

def upsert(row: dict):
    res = supabase.table("items").upsert(row, on_conflict="url").execute()
    err = getattr(res, "error", None) or (res.get("error") if isinstance(res, dict) else None)
    print("UPSERT", "ERROR:" if err else "OK:", err or row["url"])

# ----- ソース読み込み -------------------------------------------------------
with open("seed_sources.yml", encoding="utf-8") as f:
    sources = yaml.safe_load(f)

# ----- メインループ ---------------------------------------------------------
for src in sources:
    if src.get("acquisition_mode", "auto") != "auto":
        continue

    cfg = {**DEFAULT_CFG, **src}                 # デフォルトをマージ
    urls = cfg.get("urls") or [cfg.get("url") or cfg.get("api")]

    for u in urls:
        entries = fetch_and_parse(u, cfg)
        save_raw(f'{src["name"]}-{slug(u)}', entries)

        for e in entries:
            upsert({
                "src_type": src["category"],
                "title"   : e.get("title"),
                "url"     : e.get("link") or e.get("id"),
                "pub_date": safe_date(e.get("published") or e.get("updated")),
            })

print("✅ crawl finished")
