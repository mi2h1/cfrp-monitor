#!/usr/bin/env python3
import os, yaml, urllib.parse, requests, feedparser, re
from supabase import create_client, Client
from bs4 import BeautifulSoup
from datetime import datetime

SB = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
UA = {"User-Agent":"Mozilla/5.0 (compatible; CFRPbot/0.1)"}

def feed_exists(url):
    try:
        f = feedparser.parse(url)
        return len(f.entries) > 0
    except Exception:
        return False

def discover_feed(home):
    try:
        html = requests.get(home, headers=UA, timeout=10).text
    except Exception:
        return None
    soup = BeautifulSoup(html, "html.parser")
    # <link rel="alternate" ...>
    for l in soup.find_all("link", attrs={"rel":"alternate"}):
        href = l.get("href")
        if href and "rss" in l.get("type",""):
            full = urllib.parse.urljoin(home, href)
            if feed_exists(full):
                return full
    # common fallback paths
    for p in ("/rss", "/feed", "/rss.xml", "/feed.xml", "/atom.xml"):
        test = urllib.parse.urljoin(home, p)
        if feed_exists(test): return test
    return None

def robots_forbid(home):
    try:
        r = requests.get(urllib.parse.urljoin(home, "/robots.txt"), headers=UA, timeout=5)
        if r.status_code == 200 and re.search(r"(?mi)^User-agent:\s*\*\s*$(.*?)^User-agent:", r.text+"\nUser-agent:", re.S).group(1).strip().startswith("Disallow: /"):
            return True
    except Exception:
        pass
    return False

def classify(src):
    home = src["home"]
    domain = urllib.parse.urlparse(home).netloc
    entry = {
        "domain": domain,
        "category": src["category"],
        "relevance": 3,
        "access_level": 1,
        "acquisition_mode": "manual",
        "last_checked": datetime.utcnow().isoformat()
    }

    if robots_forbid(home):
        entry["acquisition_mode"] = "manual_off"
        return entry

    feed = src.get("hint_feed") or discover_feed(home)
    if feed:
        entry["urls"] = [feed]
        entry["access_level"] = 2
        entry["acquisition_mode"] = "auto"
    return entry

# ---------- MAIN -------------
candidates = yaml.safe_load(open("candidate_sources.yml"))
records = [classify(s) for s in candidates]

# YAML 保存（Git 追跡用）
yaml.dump(records, open("seed_sources.yml","w"),
          sort_keys=False, allow_unicode=True, width=80)

# DB upsert
for r in records:
    SB.table("sources").upsert(r, on_conflict="domain").execute()

print("✅ sources upserted:", len(records))
