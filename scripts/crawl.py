#!/usr/bin/env python3
import yaml, os, datetime, json, pathlib, feedparser, requests
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TODAY = datetime.date.today().isoformat()
RAW_DIR = pathlib.Path("raw") / TODAY
RAW_DIR.mkdir(parents=True, exist_ok=True)

def save_raw(name, data):
    (RAW_DIR / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2))

with open("seed_sources.yml") as f:
    seeds = yaml.safe_load(f)

for s in seeds:
    if s["acquisition_mode"] != "auto": continue
    if "urls" in s:              # RSS
        for url in s["urls"]:
            feed = feedparser.parse(url)
            save_raw(s["name"], feed)
            for e in feed.entries:
                # フィード件名を items テーブルに upsert
                supabase.table("items").upsert({
                    "src_type": s["category"],
                    "title": e.get("title"),
                    "url": e.get("link"),
                    "pub_date": e.get("published", "")[:10],
                }, on_conflict="url").execute()
    elif "api" in s:             # API
        r = requests.get(s["api"], timeout=30)
        save_raw(s["name"], r.json() if r.headers.get("content-type","").startswith("application/json") else r.text)
        # ここに API 用パースを追加
print("done!")
