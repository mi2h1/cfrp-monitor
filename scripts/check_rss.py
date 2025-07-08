#!/usr/bin/env python3
"""
URLを指定してRSSフィードの存在を確認する簡易ツール
手動で新しいサイトを調査する際に使用
"""
import sys
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import feedparser

def find_rss_feeds(url):
    """指定されたURLからRSSフィードを検出"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (compatible; RSSChecker/1.0)'
    })
    
    feeds = []
    
    print(f"調査中: {url}")
    
    try:
        # メインページを取得
        response = session.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # <link>タグからRSSフィードを探す
        print("\n[1] <link>タグを検索...")
        rss_links = soup.find_all('link', type=['application/rss+xml', 'application/atom+xml'])
        for link in rss_links:
            href = link.get('href')
            title = link.get('title', 'No title')
            if href:
                feed_url = urljoin(url, href)
                print(f"  ✓ 発見: {title} - {feed_url}")
                feeds.append(feed_url)
        
        # 一般的なRSSパスを試す
        print("\n[2] 一般的なRSSパスをチェック...")
        common_paths = [
            '/rss', '/feed', '/rss.xml', '/feed.xml', '/atom.xml',
            '/news/rss', '/news/feed', '/blog/rss', '/blog/feed',
            '/feeds/posts/default', '/index.rss', '/index.xml'
        ]
        
        for path in common_paths:
            feed_url = urljoin(url, path)
            try:
                resp = session.get(feed_url, timeout=5)
                if resp.status_code == 200:
                    feed = feedparser.parse(resp.content)
                    if feed.entries:
                        print(f"  ✓ 発見: {path} - {feed_url} ({len(feed.entries)} 記事)")
                        feeds.append(feed_url)
            except:
                pass
        
        # ページ内のRSSアイコンリンクを探す
        print("\n[3] ページ内のRSSリンクを検索...")
        rss_keywords = ['rss', 'feed', 'atom', 'xml']
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '').lower()
            text = link.get_text().lower()
            if any(keyword in href or keyword in text for keyword in rss_keywords):
                feed_url = urljoin(url, link['href'])
                if feed_url not in feeds and not feed_url.endswith(('.html', '.htm', '.php')):
                    try:
                        resp = session.get(feed_url, timeout=5)
                        if resp.status_code == 200:
                            feed = feedparser.parse(resp.content)
                            if feed.entries:
                                print(f"  ✓ 発見: {feed_url} ({len(feed.entries)} 記事)")
                                feeds.append(feed_url)
                    except:
                        pass
        
    except Exception as e:
        print(f"エラー: {e}")
        return []
    
    # 重複を除去
    feeds = list(set(feeds))
    
    if feeds:
        print(f"\n合計 {len(feeds)} 個のフィードを発見:")
        for i, feed in enumerate(feeds, 1):
            print(f"{i}. {feed}")
            
        # Supabase追加用のSQL例を表示
        domain = urlparse(url).netloc.replace('www.', '')
        print(f"\n[Supabase追加用SQL]")
        print(f"""
INSERT INTO sources (name, urls, parser, acquisition_mode, category)
VALUES (
    '{domain}',
    ARRAY['{feeds[0]}'],
    'rss',
    'auto',
    'news'
);
""")
    else:
        print("\nRSSフィードが見つかりませんでした。")
        print("ヒント: サイトのフッターやサイドバーでRSSリンクを探してみてください。")
    
    return feeds

def main():
    if len(sys.argv) < 2:
        print("使用方法: python check_rss.py <URL>")
        print("例: python check_rss.py https://www.compositesworld.com")
        sys.exit(1)
    
    url = sys.argv[1]
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    find_rss_feeds(url)

if __name__ == "__main__":
    main()