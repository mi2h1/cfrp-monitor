#!/usr/bin/env python3
"""
複合素材関連の新しい情報源を自動発見するスクリプト（拡張版）
CFRP, GFRP, AFRP など複合材料全般をカバー
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

class CompositeSourceDiscoverer:
    def __init__(self):
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_cx = os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; CompositeSourceDiscoverer/1.0)'
        })
        
        # 複合材料の包括的キーワードリスト
        self.keywords = {
            'primary': [
                'composite materials', 'composites', 'FRP', 'fiber reinforced plastic',
                'CFRP', 'carbon fiber', 'carbon fibre',
                'GFRP', 'glass fiber', 'glass fibre', 'fiberglass',
                'AFRP', 'aramid fiber', 'kevlar',
                'composite manufacturing', 'advanced materials'
            ],
            'secondary': [
                'MMC', 'metal matrix composites',
                'CMC', 'ceramic matrix composites', 
                'natural fiber composites', 'bio-composites',
                'basalt fiber', 'BFRP',
                'prepreg', 'resin transfer molding', 'RTM',
                'autoclave', 'vacuum infusion', 'VARTM',
                'pultrusion', 'filament winding'
            ],
            'applications': [
                'aerospace composites', 'automotive composites',
                'marine composites', 'wind energy composites',
                'construction composites', 'sports composites'
            ],
            'japanese': [
                '複合材料', '複合素材', 'コンポジット',
                '炭素繊維', 'カーボンファイバー',
                'ガラス繊維', 'アラミド繊維',
                '繊維強化プラスチック', 'プリプレグ'
            ],
            'chinese': [
                '复合材料', '复合材', '碳纤维', '玻璃纤维', '纤维增强',
                '碳纤', '玻纤', '复材', '增强塑料', '层合板',
                '预浸料', '高压釜', '树脂传递模塑', '拉挤成型',
                '缠绕成型', '手糊成型', '模压成型', '真空导入'
            ]
        }
        
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
            common_paths = ['/rss', '/feed', '/rss.xml', '/feed.xml', '/atom.xml', 
                          '/news/rss', '/blog/rss', '/articles/rss']
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
                feed = feedparser.parse(response.content)
                return len(feed.entries) > 0
        except:
            pass
        return False
    
    def evaluate_relevance(self, url: str, title: str = "", snippet: str = "") -> float:
        """サイトの複合材料関連度を評価（0.0-1.0）"""
        score = 0.0
        text = f"{title} {snippet} {url}".lower()
        
        # 主要キーワードマッチング（高スコア）
        for keyword in self.keywords['primary']:
            if keyword.lower() in text:
                score += 0.3
                
        # 二次キーワードマッチング（中スコア）
        for keyword in self.keywords['secondary']:
            if keyword.lower() in text:
                score += 0.2
                
        # 用途キーワードマッチング（低スコア）
        for keyword in self.keywords['applications']:
            if keyword.lower() in text:
                score += 0.1
                
        # 日本語キーワード
        for keyword in self.keywords['japanese']:
            if keyword in text:
                score += 0.25
                
        # ドメイン名にキーワードが含まれる場合は高スコア
        domain = urlparse(url).netloc.lower()
        domain_keywords = ['composite', 'fiber', 'material', 'advanced', 'frp']
        for keyword in domain_keywords:
            if keyword in domain:
                score += 0.4
                
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
        """新しい複合材料情報源を発見"""
        # 検索クエリ（複合材料全般）
        queries = [
            # 基本的な複合材料検索
            '"composite materials" news RSS',
            '"fiber reinforced plastic" OR FRP news feed',
            'CFRP OR GFRP OR AFRP news RSS',
            
            # 製造技術関連
            '"composite manufacturing" industry news',
            '"resin transfer molding" RTM news',
            'prepreg OR autoclave news RSS',
            
            # 用途別検索
            '"aerospace composites" industry news',
            '"automotive composites" news feed',
            '"wind energy composites" RSS',
            
            # 学術・技術情報
            'composites science technology RSS',
            '"advanced materials" composite news',
            
            # 日本語検索
            '複合材料 OR 複合素材 ニュース RSS',
            'カーボンファイバー OR 炭素繊維 ニュース',
            '繊維強化プラスチック RSS'
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
                if relevance < 0.4:  # 複合材料は専門性が高いので閾値を上げる
                    continue
                    
                print(f"\n調査中: {title} ({site_url})")
                print(f"関連度: {relevance:.2f}")
                
                # RSSフィード検出
                feeds = self.find_rss_feeds(site_url)
                
                for feed_url in feeds:
                    if feed_url not in existing_urls:
                        # 材料分野を推定
                        category = self.categorize_source(title, snippet)
                        
                        source = {
                            'name': title or urlparse(site_url).netloc,
                            'urls': [feed_url],
                            'site_url': site_url,
                            'relevance_score': relevance,
                            'category': category,
                            'discovered_at': datetime.now().isoformat(),
                            'status': 'candidate'
                        }
                        discovered_sources.append(source)
                        print(f"  → 新規フィード発見: {feed_url} ({category})")
                
                time.sleep(1)  # API制限対策
        
        return discovered_sources
    
    def categorize_source(self, title: str, snippet: str) -> str:
        """情報源のカテゴリを推定"""
        text = f"{title} {snippet}".lower()
        
        # 学術・研究
        if any(word in text for word in ['research', 'journal', 'science', 'university', 'academic']):
            return 'research'
            
        # 製造・産業
        elif any(word in text for word in ['manufacturing', 'industry', 'production', 'factory']):
            return 'manufacturing'
            
        # 市場・ビジネス
        elif any(word in text for word in ['market', 'business', 'trade', 'commercial']):
            return 'market'
            
        # ニュース・一般
        else:
            return 'news'
    
    def save_candidates(self, sources: List[Dict]):
        """候補をファイルに保存（レビュー用）"""
        if not sources:
            print("\n新しい複合材料情報源は見つかりませんでした。")
            return
            
        filename = f"composite_source_candidates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(os.path.dirname(__file__), '..', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(sources, f, ensure_ascii=False, indent=2)
            
        print(f"\n{len(sources)} 件の複合材料情報源候補を保存しました: {filename}")
        
        # カテゴリ別の統計
        categories = {}
        for source in sources:
            cat = source.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
            
        print("\nカテゴリ別内訳:")
        for cat, count in categories.items():
            print(f"  {cat}: {count} 件")
            
        print("\nレビュー後、適切なものをsourcesテーブルに追加してください。")

def main():
    discoverer = CompositeSourceDiscoverer()
    
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
    
    print("複合材料情報源の自動発見を開始します...")
    print("対象: CFRP, GFRP, AFRP, MMC, CMC, その他複合材料")
    
    sources = discoverer.discover_sources()
    discoverer.save_candidates(sources)

if __name__ == "__main__":
    main()