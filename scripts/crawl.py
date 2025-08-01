#!/usr/bin/env python3
import os, json, datetime, pathlib, requests, trafilatura
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from readability import Document
from supabase import create_client, Client
from dateutil import parser as dtparser
from fetcher import fetch_and_parse, slug, DEFAULT_CFG
import pytz
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.timezone_utils import safe_date_parse, now_jst_naive_iso

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

# 共通ユーティリティ関数を使用
def safe_date(txt):
    """安全な日付パース（日本時間）- 共通ユーティリティ関数を使用"""
    return safe_date_parse(txt)

def upsert(row: dict):
    try:
        # まず既存記事をチェック
        existing = supabase.table("articles").select("id").eq("url", row["url"]).execute()
        
        if existing.data:
            # 既存記事があれば何もしない
            print("SKIP (existing):", row["url"])
            return
        else:
            # 新規記事として挿入
            res = supabase.table("articles").insert(row).execute()
            err = getattr(res, "error", None) or (res.get("error") if isinstance(res, dict) else None)
            print("INSERT", "ERROR:" if err else "OK:", err or row["url"])
            
            # ログ記録用のカウント
            if not err:
                log_data["articles_added"] += 1
            else:
                log_data["errors_count"] += 1
                log_data["details"]["errors"].append({"url": row["url"], "error": str(err)})
                
    except Exception as e:
        log_data["errors_count"] += 1
        log_data["details"]["errors"].append({"url": row["url"], "error": str(e)})
        print("UPSERT ERROR:", str(e))


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


# ── ログ記録用の変数初期化 ────────────────────────────
start_time = time.time()
log_data = {
    "task_name": "Daily Article Crawl",
    "task_type": "daily_crawl",
    "sources_processed": 0,
    "articles_found": 0,
    "articles_added": 0,
    "errors_count": 0,
    "details": {"sources": [], "errors": []}
}

# ── ソース読み込み（Supabaseから） ────────────────────────
sources_result = supabase.table("sources").select("*").eq("acquisition_mode", "auto").execute()
sources = sources_result.data

print(f"自動収集対象: {len(sources)} 件")

# ── メインループ ────────────────────────────────────
for src in sources:
    log_data["sources_processed"] += 1
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

    log_data["details"]["sources"].append(src.get('name', src.get('domain')))
    
    for feed_url in urls:
        entries = fetch_and_parse(feed_url, cfg)
        save_raw(f'{src["name"]}-{slug(feed_url)}', entries)
        
        log_data["articles_found"] += len(entries)

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

            # 日本時間での追加時刻を設定（共通ユーティリティ関数を使用）
            added_at_jst = now_jst_naive_iso()
            
            upsert({
                "src_type": src["category"],
                "source_id": src["id"],  # 外部キー追加
                "title"   : e.get("title"),
                "url"     : e.get("link") or e.get("id"),
                "published_at": safe_date(e.get("published") or e.get("updated")),
                "body"    : body,
                "added_at": added_at_jst,
            })

# ── ログをDBに記録 ────────────────────────────────
end_time = time.time()
log_data["duration_seconds"] = int(end_time - start_time)
log_data["status"] = "failed" if log_data["errors_count"] > 0 else "success"

# detailsをJSON文字列に変換
log_data["details"] = json.dumps(log_data["details"], ensure_ascii=False)

# task_logsテーブルに記録
log_result = supabase.table("task_logs").insert(log_data).execute()
if hasattr(log_result, "error") and log_result.error:
    print(f"ログ記録エラー: {log_result.error}")
else:
    print(f"\n実行ログ記録完了:")
    print(f"  - 処理ソース数: {log_data['sources_processed']}")
    print(f"  - 発見記事数: {log_data['articles_found']}")
    print(f"  - 追加記事数: {log_data['articles_added']}")
    print(f"  - エラー数: {log_data['errors_count']}")
    print(f"  - 実行時間: {log_data['duration_seconds']}秒")

print("crawl finished")
