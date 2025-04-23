#!/usr/bin/env python3
import os, pandas as pd, urllib.parse, datetime as dt
from supabase import create_client, Client

CSV = "data/CFRP_情報源リスト_完全包括版.csv"   # ← 置き場所に合わせて調整

# ── Supabase ──────────────────────────────────────────
sb: Client = create_client(os.getenv("SUPABASE_URL"),
                           os.getenv("SUPABASE_KEY"))

# 列名 → ソース列変換ヘルパ
def get_domain(url: str) -> str:
    return urllib.parse.urlparse(str(url)).netloc.lower()

def normalize_category(cat: str) -> str:
    if "ニュース" in cat:   return "news"
    if "論文"   in cat:     return "paper"
    if "特許"   in cat:     return "patent"
    if "ブログ" in cat:     return "blog"
    return "other"

def mode(flag: str) -> str:
    return "auto" if str(flag).strip() in ("〇","○","Yes","yes","Y","自動","可") else "manual"

# ── CSV 読み込み ──────────────────────────────────────
df = pd.read_csv(CSV).fillna("")

imported, skipped = 0, 0
for _, r in df.iterrows():
    url = str(r["URL"]).strip()
    if not url:
        skipped += 1
        continue

    row = {
        "domain":           get_domain(url),
        "category":         normalize_category(r["情報カテゴリ"]),
        "acquisition_mode": mode(r["自動収集"]),
        "relevance":        int(r.get("優先度", 3) or 3),
        "access_level":     2 if mode(r["自動収集"])=="auto" else 1,
        "country_code":     r.get("国・地域") or None,
        "policy_url":       f'https://{get_domain(url)}/robots.txt',
        "last_checked":     dt.datetime.utcnow().isoformat()
    }

    sb.table("sources").upsert(row, on_conflict="domain").execute()
    imported += 1

print(f"✅ imported {imported} rows  (skipped {skipped} without URL)")
