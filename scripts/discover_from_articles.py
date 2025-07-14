#!/usr/bin/env python3
"""
既存の記事から新しい情報源を発見するスクリプト
記事内のリンクや引用元を分析
"""
import os
import re
import json
import time
from collections import Counter
from urllib.parse import urlparse, urljoin
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
from supabase import create_client, Client
import requests
from bs4 import BeautifulSoup
import feedparser

# Supabase接続
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

class ArticleSourceDiscoverer:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; CFRPSourceDiscoverer/1.0)'
        })
        # 複合材料関連キーワード（拡張版）
        self.keywords = [
            # 基本的な複合材料
            'cfrp', 'gfrp', 'afrp', 'frp',
            'carbon fiber', 'carbon fibre', 'glass fiber', 'glass fibre',
            'aramid fiber', 'kevlar', 'composite', 'composites',
            'reinforced plastic', 'fiber reinforced',
            
            # 製造技術
            'prepreg', 'autoclave', 'resin transfer', 'rtm',
            'vacuum infusion', 'vartm', 'pultrusion',
            'filament winding', 'braiding',
            
            # その他の複合材料
            'metal matrix', 'mmc', 'ceramic matrix', 'cmc',
            'natural fiber', 'bio-composite', 'basalt fiber',
            'sandwich panel', 'honeycomb',
            
            # 日本語
            '複合材料', '複合素材', 'コンポジット',
            '炭素繊維', 'カーボンファイバー', 'ガラス繊維',
            'アラミド繊維', '繊維強化', 'プリプレグ',
            
            # 中国語（簡体字）
            '复合材料', '复合材', '碳纤维', '玻璃纤维', '纤维增强',
            '碳纤', '玻纤', '复材', '增强塑料', '层合板',
            '预浸料', '高压釜', '树脂传递模塑', 'RTM', '拉挤成型',
            '缠绕成型', '手糊成型', '模压成型', '真空导入',
            
            # 中国語（繁体字）
            '複合材料', '碳纖維', '玻璃纖維', '纖維增強',
            '預浸料', '高壓釜', '樹脂傳遞模塑'
        ]
        
    def get_recent_articles(self, days: int = 30) -> List[Dict]:
        """最近の記事を取得"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        try:
            result = supabase.table('items')\
                .select('*')\
                .gte('published_at', cutoff_date)\
                .execute()
            return result.data
        except Exception as e:
            print(f"記事取得エラー: {e}")
            return []
    
    def extract_domains_from_text(self, text: str) -> Set[str]:
        """テキストからドメインを抽出"""
        # URL正規表現パターン
        url_pattern = re.compile(
            r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b'
            r'(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
        )
        
        urls = url_pattern.findall(text)
        domains = set()
        
        for url in urls:
            parsed = urlparse(url)
            domain = parsed.netloc
            if domain and not any(skip in domain for skip in ['twitter.com', 'facebook.com', 'youtube.com', 'linkedin.com']):
                domains.add(f"https://{domain}")
                
        return domains
    
    def analyze_article_sources(self) -> Dict[str, int]:
        """記事から情報源を分析"""
        print("既存記事から情報源を分析中...")
        articles = self.get_recent_articles(days=60)
        
        domain_counter = Counter()
        
        for article in articles:
            # 記事本文からドメイン抽出
            body = article.get('body', '')
            if body:
                domains = self.extract_domains_from_text(body)
                domain_counter.update(domains)
            
            # URLからドメイン抽出
            url = article.get('url', '')
            if url:
                parsed = urlparse(url)
                if parsed.netloc:
                    domain_counter[f"https://{parsed.netloc}"] += 1
        
        return domain_counter
    
    def check_composite_relevance(self, url: str) -> bool:
        """サイトが複合材料関連か確認"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            text = response.text.lower()
            # キーワードの出現回数をカウント
            keyword_count = sum(1 for keyword in self.keywords if keyword in text)
            
            return keyword_count >= 3  # 3つ以上のキーワードが含まれる（複合材料は範囲が広いので基準を厳しく）
        except:
            return False
    
    def find_rss_feed(self, url: str) -> Optional[str]:
        """サイトからRSSフィードを検出（シンプル版）"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # RSSリンクを探す
            rss_link = soup.find('link', type=['application/rss+xml', 'application/atom+xml'])
            if rss_link and rss_link.get('href'):
                return urljoin(url, rss_link['href'])
                
            # 一般的なパスを試す
            for path in ['/rss', '/feed', '/rss.xml', '/feed.xml']:
                feed_url = urljoin(url, path)
                try:
                    feed_response = self.session.get(feed_url, timeout=5)
                    if feed_response.status_code == 200:
                        feed = feedparser.parse(feed_response.content)
                        if feed.entries:
                            return feed_url
                except:
                    continue
                    
        except Exception as e:
            print(f"フィード検出エラー ({url}): {e}")
            
        return None
    
    def get_existing_sources(self) -> Set[str]:
        """既存の情報源ドメインを取得"""
        try:
            result = supabase.table('sources').select('urls').execute()
            domains = set()
            for source in result.data:
                for url in source.get('urls', []):
                    parsed = urlparse(url)
                    if parsed.netloc:
                        domains.add(parsed.netloc)
            return domains
        except:
            return set()
    
    def discover_new_sources(self):
        """新しい情報源を発見"""
        # 記事から頻出ドメインを取得
        domain_counts = self.analyze_article_sources()
        
        # 既存の情報源を取得
        existing_domains = self.get_existing_sources()
        
        # 候補リスト
        candidates = []
        
        print(f"\n{len(domain_counts)} 個のドメインを分析中...")
        
        for domain_url, count in domain_counts.most_common(50):
            parsed = urlparse(domain_url)
            if parsed.netloc in existing_domains:
                continue
                
            if count < 3:  # 3回以上出現したドメインのみ
                break
                
            print(f"\n調査中: {domain_url} (出現回数: {count})")
            
            # 複合材料関連性チェック
            if self.check_composite_relevance(domain_url):
                print("  → 複合材料関連サイトと判定")
                
                # RSSフィード検出
                feed_url = self.find_rss_feed(domain_url)
                if feed_url:
                    print(f"  → RSSフィード発見: {feed_url}")
                    candidates.append({
                        'name': parsed.netloc.replace('www.', ''),
                        'domain': domain_url,
                        'feed_url': feed_url,
                        'occurrence_count': count,
                        'discovered_at': datetime.now().isoformat()
                    })
        
        return candidates
    
    def save_candidates(self, candidates: List[Dict]):
        """候補を保存"""
        if not candidates:
            print("\n新しい情報源候補は見つかりませんでした。")
            return
            
        filename = f"article_source_candidates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(candidates, f, ensure_ascii=False, indent=2)
            
        print(f"\n{len(candidates)} 件の候補を保存しました: {filename}")
        print("\n次のステップ:")
        print("1. 候補を確認")
        print("2. 適切なものをsourcesテーブルに追加")
        
        # 推奨SQLも出力
        print("\n追加用SQL例:")
        for c in candidates[:3]:
            print(f"""
INSERT INTO sources (name, urls, parser, acquisition_mode)
VALUES ('{c['name']}', ARRAY['{c['feed_url']}'], 'rss', 'auto');
""")

def main():
    # ログ記録用の変数初期化
    start_time = time.time()
    log_data = {
        "task_name": "Weekly Article-Based Source Discovery",
        "task_type": "weekly_source_discovery",
        "sources_processed": 0,
        "articles_found": 0,
        "articles_added": 0,
        "errors_count": 0,
        "details": {
            "analyzed_articles": 0,
            "unique_domains": 0,
            "relevant_domains": 0,
            "domains_with_rss": 0,
            "candidates_file": "",
            "errors": []
        }
    }
    
    try:
        discoverer = ArticleSourceDiscoverer()
        candidates = discoverer.discover_new_sources()
        discoverer.save_candidates(candidates)
        
        # ログデータを更新
        log_data["articles_added"] = len(candidates)
        log_data["details"]["candidates_file"] = f"article_source_candidates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
    except Exception as e:
        log_data["errors_count"] += 1
        log_data["details"]["errors"].append(str(e))
        print(f"エラー: {e}")
        
    finally:
        # 実行時間を計算
        end_time = time.time()
        log_data["duration_seconds"] = int(end_time - start_time)
        log_data["status"] = "failed" if log_data["errors_count"] > 0 else "success"
        
        # detailsをJSON文字列に変換
        log_data["details"] = json.dumps(log_data["details"], ensure_ascii=False)
        
        # task_logsテーブルに記録
        try:
            log_result = supabase.table("task_logs").insert(log_data).execute()
            if hasattr(log_result, "error") and log_result.error:
                print(f"ログ記録エラー: {log_result.error}")
            else:
                print(f"実行ログ記録完了: {log_data['task_name']}")
                print(f"  - 発見候補数: {log_data['articles_added']}")
                print(f"  - 実行時間: {log_data['duration_seconds']}秒")
                print(f"  - ステータス: {log_data['status']}")
        except Exception as e:
            print(f"ログ記録エラー: {e}")

if __name__ == "__main__":
    main()