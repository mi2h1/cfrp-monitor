#!/usr/bin/env python3
import os, json, datetime, pathlib, requests, trafilatura
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from readability import Document
from supabase import create_client, Client
from dateutil import parser as dtparser
from fetcher import fetch_and_parse, slug, DEFAULT_CFG
import pytz

# ── Supabase ─────────────────────────────────────────────
supabase: Client = create_client(os.getenv("SUPABASE_URL"),
                                 os.getenv("SUPABASE_KEY"))

# ── 保存ディレクトリ ───────────────────────────────────
today   = datetime.date.today().isoformat()
RAW_DIR = pathlib.Path("raw") / today
RAW_DIR.mkdir(parents=True, exist_ok=True)

def save_raw(name: str, data):
    (RAW_DIR / f"{name}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8"
    )

def safe_date(txt):
    """安全な日付パース（日本時間）"""
    try:
        if not txt:
            return None
        
        # 日付をパース
        parsed_date = dtparser.parse(txt)
        
        # タイムゾーンが設定されていない場合はUTCと仮定
        if parsed_date.tzinfo is None:
            parsed_date = pytz.utc.localize(parsed_date)
        
        # 日本時間に変換
        jst = pytz.timezone('Asia/Tokyo')
        japan_time = parsed_date.astimezone(jst)
        
        return japan_time.date().isoformat()
    except Exception:
        return None

def upsert(row: dict):
    res = supabase.table("items").upsert(row, on_conflict="url").execute()
    err = getattr(res, "error", None) or (res.get("error") if isinstance(res, dict) else None)
    print("UPSERT", "ERROR:" if err else "OK:", err or row["url"])


# ── HTML 本文抽出ユーティリティ ────────────────────────
UA_HEADERS = {"User-Agent": DEFAULT_CFG["ua"]}
retry_cfg  = Retry(total=3, backoff_factor=1,
                   status_forcelist=[429, 502, 503, 504])
session = requests.Session()
session.headers.update(UA_HEADERS)
session.mount("https://", HTTPAdapter(max_retries=retry_cfg))
session.mount("http://",  HTTPAdapter(max_retries=retry_cfg))

def extract_html_body(html: str) -> str | None:
    """本文テキストを抽出（Trafilatura → Readability フォールバック）"""
    text = trafilatura.extract(html, include_comments=False, include_tables=False)
    if text and len(text.split()) > 50:
        return text
    # fallback
    try:
        cleaned = trafilatura.extract(Document(html).summary())
        return cleaned
    except Exception:
        return None

def fetch_article_body(url: str) -> str | None:
    try:
        r = session.get(url, timeout=25)
        r.raise_for_status()
        return extract_html_body(r.text)
    except Exception as e:
        print("body fetch failed:", url, "->", e)
        return None


# ── ソース読み込み（Supabaseから） ────────────────────────
sources_result = supabase.table("sources").select("*").eq("acquisition_mode", "auto").execute()
sources = sources_result.data

print(f"自動収集対象: {len(sources)} 件")

# ── メインループ ────────────────────────────────────
for src in sources:
    # sourcesテーブルのカラムからseed_sources.yml互換の設定を構築
    cfg = {
        **DEFAULT_CFG,
        "ua": src.get("ua") or DEFAULT_CFG["ua"],
        "http_fallback": src.get("http_fallback", False),
        "retry": src.get("retry_count", 3),
        "backoff": src.get("backoff_factor", 1.0),
        "parser": src.get("parser", "rss")
    }
    
    urls = src.get("urls") or []
    if not urls:
        print(f"URL未設定: {src.get('name', src.get('domain'))}")
        continue

    for feed_url in urls:
        entries = fetch_and_parse(feed_url, cfg)
        save_raw(f'{src["name"]}-{slug(feed_url)}', entries)

        for e in entries:
            # --- 1) フィードに本文があるか確認 --------------------------
            body = None
            if "content" in e and e.content:
                body = e.content[0].value
            elif e.get("summary_detail", {}).get("type") == "text/html":
                body = e.get("summary")

            # --- 2) 無ければページをクロール ----------------------------
            if not body:
                link = e.get("link") or e.get("id")
                body = fetch_article_body(link)

            # 日本時間での追加時刻を設定（タイムゾーン情報なしで保存）
            jst = pytz.timezone('Asia/Tokyo')
            added_at_jst = datetime.datetime.now(jst).replace(tzinfo=None).isoformat()
            
            upsert({
                "src_type": src["category"],
                "source_id": src["id"],  # 外部キー追加
                "title"   : e.get("title"),
                "url"     : e.get("link") or e.get("id"),
                "pub_date": safe_date(e.get("published") or e.get("updated")),
                "body"    : body,
                "added_at": added_at_jst,
            })

print("crawl finished")
