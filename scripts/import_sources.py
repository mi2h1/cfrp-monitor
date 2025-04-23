#!/usr/bin/env python3
"""
CSV → Supabase.sources   one-shot importer
"""

import os, pandas as pd, urllib.parse, datetime as dt
from supabase import create_client, Client

# ── Supabase client ───────────────────────────────
sb: Client = create_client(os.getenv("SUPABASE_URL"),
                           os.getenv("SUPABASE_KEY"))

# ── 列名 → sources 列へのマッピング  ────────────────
CSV = "data/CFRP_情報源リスト_完全包括版.csv"
df  = pd.read_csv(CSV).fillna("")

def domain(url: str) -> str:
    return urllib.parse.urlparse(str(url)).netloc.lower()

def mode(flag: str) -> str:           # 自動収集列 → acquisition_mode
    return "auto" if flag.strip() in ("〇", "○", "Yes", "yes", "Y") else "manual"

def category(cat: str) -> str:        # カテゴリ列 → 独自コード
    m = {"ニュース": "news", "論文": "paper", "特許": "patent"}
    return m.get(cat.strip(), "other")

for _, r in df.iterrows():
    row = {
        # 必須
        "domain":           domain(r["URL"]),
        "category":         category(r["カテゴリ"]),
        "acquisition_mode": mode(r["自動収集"]),
        # 任意（無ければデフォルト）
        "relevance":        int(r.get("優先度", 3) or 3),
        "access_level":     int(r.get("アクセスレベル", 1) or 1),
        "restrict_lvl":     int(r.get("制約度", 0) or 0),
        "country_code":     r.get("国コード") or None,
        "policy_url":       r.get("利用規約 URL") or f'https://{domain(r["URL"])}/robots.txt',
        "last_checked":     dt.datetime.utcnow().isoformat(),
    }
    # upsert on "domain"
    sb.table("sources").upsert(row, on_conflict="domain").execute()

print(f"✅ imported {len(df)} rows into sources")
