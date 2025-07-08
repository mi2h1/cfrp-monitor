#!/usr/bin/env python3
"""
RSS/Atomフィードの有効性を検証するユーティリティ
新情報源発見時に自動的に呼び出される
"""
import requests
import feedparser
from urllib.parse import urlparse
import time
from typing import Dict, List, Optional

class RSSValidator:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.timeout = 15
    
    def validate_rss_url(self, url: str) -> Dict:
        """
        RSSフィードURLを検証
        
        Returns:
            Dict: {
                'valid': bool,
                'accessible': bool,
                'feed_type': 'rss' | 'atom' | None,
                'item_count': int,
                'latest_item': Dict or None,
                'error': str or None,
                'recommended_mode': 'auto' | 'manual' | 'disabled'
            }
        """
        result = {
            'valid': False,
            'accessible': False,
            'feed_type': None,
            'item_count': 0,
            'latest_item': None,
            'error': None,
            'recommended_mode': 'disabled'
        }
        
        try:
            # URLアクセステスト
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            
            if response.status_code == 403:
                result['error'] = 'Access Forbidden (403)'
                result['recommended_mode'] = 'manual'  # 手動チェック推奨
                return result
                
            if response.status_code == 404:
                result['error'] = 'Not Found (404)'
                result['recommended_mode'] = 'disabled'
                return result
                
            if response.status_code != 200:
                result['error'] = f'HTTP Error {response.status_code}'
                result['recommended_mode'] = 'manual'
                return result
            
            result['accessible'] = True
            
            # フィードパース
            feed = feedparser.parse(response.content)
            
            # フィードの有効性チェック
            if hasattr(feed, 'bozo') and feed.bozo:
                if hasattr(feed, 'bozo_exception'):
                    result['error'] = f'Parse error: {str(feed.bozo_exception)[:100]}'
                result['recommended_mode'] = 'manual'
                return result
            
            # フィードタイプ判定
            if feed.version:
                if 'rss' in feed.version:
                    result['feed_type'] = 'rss'
                elif 'atom' in feed.version:
                    result['feed_type'] = 'atom'
            
            # エントリー数確認
            if hasattr(feed, 'entries'):
                result['item_count'] = len(feed.entries)
                
                if result['item_count'] > 0:
                    # 最新記事の情報
                    latest = feed.entries[0]
                    result['latest_item'] = {
                        'title': getattr(latest, 'title', 'No title'),
                        'link': getattr(latest, 'link', ''),
                        'published': getattr(latest, 'published', getattr(latest, 'updated', '')),
                    }
                    
                    result['valid'] = True
                    result['recommended_mode'] = 'auto'  # 自動収集可能
                else:
                    result['error'] = 'No entries found'
                    result['recommended_mode'] = 'manual'
            else:
                result['error'] = 'No feed entries'
                result['recommended_mode'] = 'disabled'
                
        except requests.exceptions.Timeout:
            result['error'] = 'Timeout'
            result['recommended_mode'] = 'manual'
        except requests.exceptions.SSLError:
            result['error'] = 'SSL Error'
            result['recommended_mode'] = 'manual'
        except Exception as e:
            result['error'] = f'Error: {str(e)[:100]}'
            result['recommended_mode'] = 'disabled'
        
        return result
    
    def find_rss_urls(self, domain: str) -> List[str]:
        """
        ドメインから可能性のあるRSS URLを探索
        """
        # よくあるRSSのパス
        common_paths = [
            '/rss',
            '/feed',
            '/rss.xml',
            '/feed.xml',
            '/atom.xml',
            '/rss/feed.xml',
            '/feeds/rss',
            '/index.rss',
            '/news/rss',
            '/blog/rss',
            '/en/rss',
            '/ja/rss'
        ]
        
        base_url = f"https://{domain}"
        found_urls = []
        
        # robots.txtからヒントを探す
        try:
            robots_url = f"{base_url}/robots.txt"
            response = self.session.get(robots_url, timeout=5)
            if response.status_code == 200:
                for line in response.text.split('\n'):
                    if 'rss' in line.lower() or 'feed' in line.lower():
                        # URLを抽出する処理
                        pass
        except:
            pass
        
        # 一般的なパスをテスト
        for path in common_paths:
            test_url = base_url + path
            try:
                response = self.session.head(test_url, timeout=5, allow_redirects=True)
                if response.status_code == 200:
                    # Content-Typeチェック
                    content_type = response.headers.get('Content-Type', '').lower()
                    if any(t in content_type for t in ['xml', 'rss', 'atom']):
                        found_urls.append(test_url)
            except:
                continue
            
            time.sleep(0.5)  # レート制限対策
        
        return found_urls

def validate_new_source(domain: str, urls: List[str] = None) -> Dict:
    """
    新情報源のRSS検証を実行
    
    Args:
        domain: ドメイン名
        urls: テストするURL（指定がない場合は自動探索）
    
    Returns:
        Dict: 検証結果とacquisition_mode推奨値
    """
    validator = RSSValidator()
    
    # URLが指定されていない場合は探索
    if not urls:
        urls = validator.find_rss_urls(domain)
        if not urls:
            return {
                'domain': domain,
                'rss_found': False,
                'recommended_mode': 'manual',
                'reason': 'No RSS URLs found'
            }
    
    # 各URLをテスト
    best_result = None
    for url in urls:
        result = validator.validate_rss_url(url)
        if result['valid']:
            return {
                'domain': domain,
                'rss_found': True,
                'rss_url': url,
                'feed_type': result['feed_type'],
                'item_count': result['item_count'],
                'recommended_mode': 'auto',
                'reason': 'Valid RSS feed found'
            }
        
        # 有効でなくても、手動チェック推奨の場合は保持
        if not best_result or result['recommended_mode'] == 'manual':
            best_result = result
            best_result['url'] = url
    
    # 最良の結果を返す
    if best_result:
        return {
            'domain': domain,
            'rss_found': False,
            'rss_url': best_result.get('url'),
            'recommended_mode': best_result['recommended_mode'],
            'reason': best_result.get('error', 'Unknown error')
        }
    
    return {
        'domain': domain,
        'rss_found': False,
        'recommended_mode': 'disabled',
        'reason': 'No accessible URLs found'
    }

if __name__ == "__main__":
    # テスト実行
    test_domains = [
        'mdpi.com',
        'compositesworld.com',
        'example.com'
    ]
    
    for domain in test_domains:
        print(f"\n🔍 Testing {domain}...")
        result = validate_new_source(domain)
        print(f"RSS Found: {result['rss_found']}")
        print(f"Recommended Mode: {result['recommended_mode']}")
        print(f"Reason: {result['reason']}")