#!/usr/bin/env python3
"""
CFRP関連の新しい情報源を自動発見するスクリプト
Google Custom Search APIとRSSフィード検出を使用
"""
import os
import json
import time
import requests
import feedparser
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
from supabase import create_client, Client

# Supabase接続
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

class SourceDiscoverer:
    def __init__(self):
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_cx = os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; CFRPSourceDiscoverer/1.0)'
        })
        
    def search_google(self, query: str, num_results: int = 10) -> List[Dict]:
        """Google Custom Search APIで検索"""
        if not self.google_api_key or not self.google_cx:
            print("警告: Google API認証情報が設定されていません")
            return []
            
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': self.google_api_key,
            'cx': self.google_cx,
            'q': query,
            'num': num_results
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('items', [])
        except Exception as e:
            print(f"Google検索エラー: {e}")
            return []
    
    def find_rss_feeds(self, url: str) -> List[str]:
        """ウェブサイトからRSSフィードを検出"""
        feeds = []
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # <link> タグからRSSフィードを探す
            rss_links = soup.find_all('link', type=['application/rss+xml', 'application/atom+xml'])
            for link in rss_links:
                href = link.get('href')
                if href:
                    feed_url = urljoin(url, href)
                    feeds.append(feed_url)
            
            # 一般的なRSSフィードのパスも試す
            common_paths = ['/rss', '/feed', '/rss.xml', '/feed.xml', '/atom.xml', '/news/rss']
            for path in common_paths:
                feed_url = urljoin(url, path)
                if self.validate_feed(feed_url):
                    feeds.append(feed_url)
                    
        except Exception as e:
            print(f"RSS検出エラー ({url}): {e}")
            
        return list(set(feeds))  # 重複を除去
    
    def validate_feed(self, feed_url: str) -> bool:
        """フィードURLが有効か確認"""
        try:
            response = self.session.get(feed_url, timeout=5)
            if response.status_code == 200:
                # feedparserで解析可能か確認
                feed = feedparser.parse(response.content)
                return len(feed.entries) > 0
        except:
            pass
        return False
    
    def evaluate_relevance(self, url: str, title: str = "", snippet: str = "") -> float:
        """サイトのCFRP関連度を評価（0.0-1.0）"""
        keywords = [
            'cfrp', 'carbon fiber', 'composite', 'carbon fibre',
            'reinforced plastic', 'composite materials', 'composites world',
            '炭素繊維', '複合材料', 'カーボンファイバー'
        ]
        
        score = 0.0
        text = f"{title} {snippet} {url}".lower()
        
        # キーワードマッチング
        for keyword in keywords:
            if keyword in text:
                score += 0.2
                
        # ドメイン名にキーワードが含まれる場合は高スコア
        domain = urlparse(url).netloc.lower()
        for keyword in keywords:
            if keyword.replace(' ', '') in domain:
                score += 0.3
                
        return min(score, 1.0)
    
    def get_existing_sources(self) -> set:
        """既存のソースURLを取得"""
        try:
            result = supabase.table('sources').select('urls').execute()
            existing_urls = set()
            for source in result.data:
                if source.get('urls'):
                    existing_urls.update(source['urls'])
            return existing_urls
        except Exception as e:
            print(f"既存ソース取得エラー: {e}")
            return set()
    
    def discover_sources(self):
        """新しい情報源を発見"""
        # 検索クエリ
        queries = [
            '"CFRP news" OR "carbon fiber news" RSS',
            '"composite materials" news feed',
            'carbon fiber industry blog',
            'CFRP manufacturing news',
            'advanced composites news RSS',
            '"carbon fiber reinforced plastic" news'
        ]
        
        existing_urls = self.get_existing_sources()
        discovered_sources = []
        
        for query in queries:
            print(f"\n検索中: {query}")
            results = self.search_google(query)
            
            for result in results:
                site_url = result.get('link', '')
                title = result.get('title', '')
                snippet = result.get('snippet', '')
                
                # 関連度評価
                relevance = self.evaluate_relevance(site_url, title, snippet)
                if relevance < 0.3:
                    continue
                    
                print(f"\n調査中: {title} ({site_url})")
                print(f"関連度: {relevance:.2f}")
                
                # RSSフィード検出
                feeds = self.find_rss_feeds(site_url)
                
                for feed_url in feeds:
                    if feed_url not in existing_urls:
                        source = {
                            'name': title or urlparse(site_url).netloc,
                            'urls': [feed_url],
                            'site_url': site_url,
                            'relevance_score': relevance,
                            'discovered_at': datetime.now().isoformat(),
                            'status': 'candidate'  # 候補として保存
                        }
                        discovered_sources.append(source)
                        print(f"  → 新規フィード発見: {feed_url}")
                
                time.sleep(1)  # API制限対策
        
        return discovered_sources
    
    def save_candidates(self, sources: List[Dict]):
        """候補をファイルに保存（レビュー用）"""
        if not sources:
            print("\n新しい情報源は見つかりませんでした。")
            return
            
        filename = f"candidate_sources_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(os.path.dirname(__file__), '..', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(sources, f, ensure_ascii=False, indent=2)
            
        print(f"\n{len(sources)} 件の候補を保存しました: {filename}")
        print("\nレビュー後、適切なものをsourcesテーブルに追加してください。")

def main():
    discoverer = SourceDiscoverer()
    
    # Google API認証情報の確認
    if not discoverer.google_api_key:
        print("エラー: GOOGLE_API_KEY環境変数を設定してください")
        print("Google Custom Search APIの設定方法:")
        print("1. https://console.cloud.google.com でプロジェクトを作成")
        print("2. Custom Search APIを有効化")
        print("3. APIキーを作成")
        print("4. https://cse.google.com で検索エンジンを作成")
        print("5. 環境変数を設定:")
        print("   export GOOGLE_API_KEY='your-api-key'")
        print("   export GOOGLE_CUSTOM_SEARCH_ENGINE_ID='your-cx-id'")
        return
    
    print("CFRP情報源の自動発見を開始します...")
    sources = discoverer.discover_sources()
    discoverer.save_candidates(sources)

if __name__ == "__main__":
    main()