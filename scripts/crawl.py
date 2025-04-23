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
    path = RAW_DIR / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    # default=str を追加して「非 JSON 対応オブジェクトは文字列化」
    json.dump(data, path.open("w", encoding="utf-8"),
              ensure_ascii=False, indent=2, default=str)

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
    elif "api" in s:                          # API 定義も Atom/RSS 想定
        resp = requests.get(s["api"], timeout=30)
        feed = feedparser.parse(resp.text)
        save_raw(s["name"], feed)             # ← ここも同じ関数で OK
        data_iter = feed.entries

print("done!")
