#!/usr/bin/env python3
"""
HTMLスクレイピング対応の情報源追加
RSSが無いサイトでもニュース一覧ページから記事を取得
"""
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
import re
from typing import List, Dict, Optional
from supabase import create_client, Client

# Supabase接続
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

class HTMLSourceAnalyzer:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def analyze_news_page(self, url: str) -> Dict:
        """ニュースページの構造を分析"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 記事リンクを検出
            article_links = self.find_article_links(soup, url)
            
            # ページネーション検出
            pagination = self.find_pagination(soup, url)
            
            # 日付情報検出
            date_pattern = self.detect_date_pattern(soup)
            
            return {
                'url': url,
                'article_count': len(article_links),
                'article_links': article_links[:5],  # サンプル5個
                'pagination': pagination,
                'date_pattern': date_pattern,
                'scraping_feasible': len(article_links) > 0
            }
            
        except Exception as e:
            return {
                'url': url,
                'error': str(e),
                'scraping_feasible': False
            }
    
    def find_article_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """記事リンクを検出"""
        articles = []
        
        # よくあるセレクタパターン
        selectors = [
            'a[href*="/news/"]',
            'a[href*="/press/"]', 
            'a[href*="/topics/"]',
            '.news-item a',
            '.news-list a',
            '.article-title a',
            '.post-title a',
            'h3 a', 'h4 a',  # 見出しのリンク
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    title = link.get_text().strip()
                    
                    if title and len(title) > 10:  # 十分な長さのタイトル
                        articles.append({
                            'title': title,
                            'url': full_url,
                            'selector': selector
                        })
        
        # 重複除去
        seen_urls = set()
        unique_articles = []
        for article in articles:
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                unique_articles.append(article)
        
        return unique_articles
    
    def find_pagination(self, soup: BeautifulSoup, base_url: str) -> Dict:
        """ページネーション情報を検出"""
        pagination = {'has_pagination': False}
        
        # ページネーションのよくあるパターン
        pagination_selectors = [
            '.pagination a',
            '.pager a', 
            'a[href*="page="]',
            'a[href*="&page="]',
            '.next-page',
            '.page-next'
        ]
        
        for selector in pagination_selectors:
            elements = soup.select(selector)
            if elements:
                pagination['has_pagination'] = True
                pagination['selector'] = selector
                pagination['sample_links'] = [
                    urljoin(base_url, elem.get('href', '')) 
                    for elem in elements[:3]
                ]
                break
        
        return pagination
    
    def detect_date_pattern(self, soup: BeautifulSoup) -> Dict:
        """日付パターンを検出"""
        date_patterns = {
            'detected': False,
            'patterns': []
        }
        
        # 日付らしいテキストを検索
        date_regex_patterns = [
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',  # 2024/01/01
            r'\d{4}年\d{1,2}月\d{1,2}日',      # 2024年1月1日
            r'\d{1,2}/\d{1,2}/\d{4}',         # 01/01/2024
        ]
        
        text_content = soup.get_text()
        
        for pattern in date_regex_patterns:
            matches = re.findall(pattern, text_content)
            if matches:
                date_patterns['detected'] = True
                date_patterns['patterns'].append({
                    'regex': pattern,
                    'samples': matches[:3]
                })
        
        return date_patterns

def test_html_sources():
    """HTML対応候補のテスト"""
    analyzer = HTMLSourceAnalyzer()
    
    # テスト対象のニュースページ
    test_sources = [
        {
            'name': 'Toray Industries',
            'url': 'https://www.toray.co.jp/news/?language=JA&region=JAPAN',
            'expected_keywords': ['CFRP', '炭素繊維', '複合材料']
        },
        {
            'name': 'Hexcel',
            'url': 'https://www.hexcel.com/news-events/news',
            'expected_keywords': ['composites', 'carbon fiber', 'prepreg']
        },
        {
            'name': 'SGL Carbon', 
            'url': 'https://www.sglcarbon.com/en/press-center/press-releases/',
            'expected_keywords': ['carbon', 'composites', 'materials']
        }
    ]
    
    print("🔍 HTML スクレイピング対応可能性テスト")
    print("=" * 60)
    
    results = []
    
    for source in test_sources:
        print(f"\n📰 {source['name']}")
        print(f"URL: {source['url']}")
        
        analysis = analyzer.analyze_news_page(source['url'])
        results.append({**source, 'analysis': analysis})
        
        if analysis.get('scraping_feasible'):
            print(f"✅ スクレイピング可能")
            print(f"   記事数: {analysis['article_count']}")
            print(f"   ページネーション: {analysis['pagination']['has_pagination']}")
            print(f"   日付検出: {analysis['date_pattern']['detected']}")
            
            if analysis['article_links']:
                print("   サンプル記事:")
                for article in analysis['article_links'][:2]:
                    print(f"     - {article['title'][:50]}...")
        else:
            print(f"❌ スクレイピング困難")
            if 'error' in analysis:
                print(f"   エラー: {analysis['error']}")
    
    return results

def add_html_sources_to_db(sources: List[Dict]):
    """HTML対応ソースをデータベースに追加"""
    print("\n📝 HTML対応ソースをデータベースに追加")
    
    for source in sources:
        if source['analysis'].get('scraping_feasible'):
            try:
                # parser を 'html' に設定
                source_data = {
                    'name': f"{source['name']} (HTML)",
                    'urls': [source['url']],
                    'parser': 'html',  # RSS の代わりに HTML
                    'acquisition_mode': 'auto',
                    'category': 'news',
                    'domain': urlparse(source['url']).netloc,
                    'country_code': 'US' if 'hexcel' in source['url'] else 'JP',
                    'relevance': 8
                }
                
                result = supabase.table("sources").insert(source_data).execute()
                print(f"✅ 追加完了: {source['name']}")
                
            except Exception as e:
                print(f"❌ 追加エラー ({source['name']}): {e}")

def create_html_parser_extension():
    """HTML パーサー拡張をcrawl.pyに追加するコード生成"""
    
    html_parser_code = '''
# HTML パーサー拡張 (crawl.py に追加)

def parse_html_news_page(url: str, config: dict) -> List[Dict]:
    """HTML ニュースページから記事を抽出"""
    try:
        response = session.get(url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []
        
        # 記事リンクの検出（よくあるパターン）
        selectors = [
            'a[href*="/news/"]',
            'a[href*="/press/"]',
            '.news-item a',
            '.news-list a',
            'h3 a', 'h4 a'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            
            for link in links:
                href = link.get('href')
                title = link.get_text().strip()
                
                if href and title and len(title) > 10:
                    full_url = urljoin(url, href)
                    
                    # 日付抽出（親要素から）
                    date_elem = link.find_parent().find(text=re.compile(r'\\d{4}[/-]\\d{1,2}[/-]\\d{1,2}'))
                    published_at = date_elem if date_elem else None
                    
                    articles.append({
                        'title': title,
                        'link': full_url,
                        'published': published_at,
                        'id': full_url,  # RSS の 'id' 相当
                        'summary': ''  # 後で詳細ページから取得
                    })
        
        return articles[:20]  # 最新20件に制限
        
    except Exception as e:
        print(f"HTML解析エラー: {e}")
        return []

# crawl.py のメインループに追加:
# if src.get("parser") == "html":
#     entries = parse_html_news_page(feed_url, cfg)
# else:
#     entries = fetch_and_parse(feed_url, cfg)
'''
    
    with open('html_parser_extension.py', 'w', encoding='utf-8') as f:
        f.write(html_parser_code)
    
    print("📄 HTML パーサー拡張コード生成: html_parser_extension.py")

def main():
    # 環境変数チェック
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        print("❌ エラー: SUPABASE_URL と SUPABASE_KEY 環境変数を設定してください")
        return
    
    print("🌐 HTML スクレイピング対応システム")
    print("RSSが無いサイトからニュース記事を取得")
    print()
    
    # HTMLソースの分析
    results = test_html_sources()
    
    # 実行可能なソースをDBに追加するか確認
    feasible_sources = [s for s in results if s['analysis'].get('scraping_feasible')]
    
    if feasible_sources:
        print(f"\n🎯 {len(feasible_sources)} 個のサイトでHTMLスクレイピング可能")
        
        # HTML パーサー拡張コード生成
        create_html_parser_extension()
        
        print("\n次のステップ:")
        print("1. html_parser_extension.py のコードを crawl.py に統合")
        print("2. BeautifulSoup4 を requirements.txt に追加")
        print("3. HTML対応ソースをデータベースに追加")
        
    else:
        print("❌ HTMLスクレイピング可能なサイトが見つかりませんでした")

if __name__ == "__main__":
    main()