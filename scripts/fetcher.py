"""
fetcher.py : 汎用フェッチ & パースユーティリティ
-----------------------------------------------
yaml の各ソース dict をそのまま渡せるようにしてあるので、
crawl.py 側で個別 if/else は不要になります。
"""
import json, time, requests, feedparser
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_CFG = {
    "ua": "Mozilla/5.0 (compatible; CFRPbot/0.1)",
    "retry": 3,
    "backoff": 1,          # 秒
    "timeout": 30,
    "http_fallback": False
}

# ---------- セッション生成 -------------------------------------------------
def _session(cfg):
    r = Retry(total=cfg["retry"],
              backoff_factor=cfg["backoff"],
              status_forcelist=[429, 502, 503, 504])
    s = requests.Session()
    s.headers.update({"User-Agent": cfg["ua"]})
    s.mount("https://", HTTPAdapter(max_retries=r))
    s.mount("http://",  HTTPAdapter(max_retries=r))
    return s

# ---------- フェッチ本体 ---------------------------------------------------
def fetch_text(url: str, cfg: dict) -> str | None:
    sess = _session(cfg)
    try:
        resp = sess.get(url, timeout=cfg["timeout"])
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        # HTTPS → HTTP フォールバック
        if cfg.get("http_fallback") and url.startswith("https://"):
            new_url = url.replace("https://", "http://", 1)
            new_cfg = {**cfg, "http_fallback": False}
            return fetch_text(new_url, new_cfg)
        print("⚠️ fetch failed:", url, "->", e)
        return None

# ---------- パーサ群 -------------------------------------------------------
def parse_rss(text: str):
    return feedparser.parse(text).entries

PARSERS = {
    "rss": parse_rss,
    # 必要に応じて "json": parse_json など追加
}

# ---------- 外部 API -------------------------------------------------------
def fetch_and_parse(url: str, cfg: dict):
    txt = fetch_text(url, cfg)
    if not txt:
        return []
    parser_id = cfg.get("parser", "
