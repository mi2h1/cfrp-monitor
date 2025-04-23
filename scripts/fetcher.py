# scripts/fetcher.py
"""
共通フェッチ&パースモジュール
YAML で指定したメタ情報（ua, retry, http_fallback など）を使って
どんなソースでも fetch_and_parse() 1 本で取れるようにしてある。
"""

import json, requests, feedparser
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ── デフォルト設定 ─────────────────────────────────────
DEFAULT_CFG = {
    "ua":            "Mozilla/5.0 (compatible; CFRPbot/0.1)",
    "retry":         3,      # リトライ回数
    "backoff":       1,      # 1→2→4 秒
    "timeout":       30,
    "http_fallback": False,  # https 失敗時に http へ?
    "parser":        "rss",  # rss / json / (拡張可)
}

# ── 内部：requests.Session を作る ───────────────────────
def _session(cfg: dict) -> requests.Session:
    r = Retry(
        total          = cfg.get("retry",   DEFAULT_CFG["retry"]),
        backoff_factor = cfg.get("backoff", DEFAULT_CFG["backoff"]),
        status_forcelist=[429, 502, 503, 504],
    )
    s = requests.Session()
    s.headers.update({"User-Agent": cfg.get("ua", DEFAULT_CFG["ua"])})
    s.mount("https://", HTTPAdapter(max_retries=r))
    s.mount("http://",  HTTPAdapter(max_retries=r))
    return s

# ── テキスト取得（HTTP→HTTPS フォールバック付き） ────
def fetch_text(url: str, cfg: dict) -> str | None:
    sess = _session(cfg)
    try:
        resp = sess.get(url, timeout=cfg.get("timeout", DEFAULT_CFG["timeout"]))
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        if cfg.get("http_fallback") and url.startswith("https://"):
            new_url = url.replace("https://", "http://", 1)
            new_cfg = {**cfg, "http_fallback": False}
            return fetch_text(new_url, new_cfg)
        print("⚠️ fetch failed:", url, "->", e)
        return None

# ── パーサ関数群 ────────────────────────────────────────
def parse_rss(text: str):
    return feedparser.parse(text).entries

def parse_json(text: str):
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "items" in data and isinstance(data["items"], list):
            return data["items"]
    except Exception as e:
        print("⚠️ json parse failed:", e)
    return []

PARSERS = {
    "rss":  parse_rss,
    "json": parse_json,
}

# ── 外部 API：fetch → parse 一括ラッパ ─────────────────
def fetch_and_parse(url: str, cfg: dict):
    txt = fetch_text(url, cfg)
    if txt is None:
        return []
    parser_id = cfg.get("parser", DEFAULT_CFG["parser"])
    parser = PARSERS.get(parser_id)
    if not parser:
        print("⚠️ unknown parser:", parser_id, "->", url)
        return []
    return parser(txt)

# ── ヘルパ：URL からファイル名向けスラッグ生成 ─────────
def slug(url: str) -> str:
    p = urlparse(url)
    return (p.netloc + p.path).strip("/").replace("/", "_")[:80]
