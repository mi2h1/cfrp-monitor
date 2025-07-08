#!/usr/bin/env python3
"""
sourcesテーブルのurlsを検証し、問題があるURLを修正
- アクセス不可URLの検出
- 代替URL（.co.jp等）の探索
- RSS/フィードパスの修正
"""
import os
import requests
from urllib.parse import urlparse
import time
from typing import Dict, List, Optional, Tuple
from supabase import create_client, Client

# Supabase接続
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

class URLVerifier:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # ドメイン代替候補
        self.domain_alternatives = {
            'teijin.com': ['teijin.co.jp'],
            'toray.com': ['toray.co.jp'],
            'hexcel.com': ['hexcel.com'],  # 米国企業なので.com正しいはず
            'chemicaldaily.co.jp': ['chemicaldaily.co.jp'],
            'jeccomposites.com': ['jeccomposites.com'],
            'solvay.com': ['solvay.com'],
            'sglcarbon.com': ['sglcarbon.com', 'sglcarbon.de']
        }
        
        # RSS/フィードパス候補
        self.feed_paths = [
            '/rss.xml', '/feed.xml', '/rss/', '/feed/',
            '/news/rss.xml', '/news/feed.xml', '/news/rss/', '/news/feed/',
            '/press/rss.xml', '/press/feed.xml',
            '/en/news/rss.xml', '/en/rss.xml',
            '/jp/news/rss.xml', '/jp/rss.xml'
        ]
    
    def test_url(self, url: str) -> Tuple[bool, int, str]:
        """URLをテストして状態を返す"""
        try:
            response = self.session.head(url, timeout=10, allow_redirects=True)
            return True, response.status_code, response.url
        except Exception as e:
            return False, 0, str(e)
    
    def find_working_feed(self, base_domain: str) -> Optional[str]:
        """有効なフィードURLを探索"""
        # ドメイン代替候補を試行
        domains_to_try = self.domain_alternatives.get(base_domain, [base_domain])
        
        for domain in domains_to_try:
            print(f"    🔍 {domain} で検索中...")
            
            for path in self.feed_paths:
                test_url = f"https://{domain}{path}"
                
                success, status_code, final_url = self.test_url(test_url)
                
                if success and status_code == 200:
                    # Content-Typeも確認
                    try:
                        response = self.session.get(test_url, timeout=8)
                        content_type = response.headers.get('content-type', '').lower()
                        
                        # XML/RSSコンテンツか確認
                        if any(ct in content_type for ct in ['xml', 'rss', 'atom']) or \
                           any(keyword in response.text[:500].lower() for keyword in ['<rss', '<feed', '<channel']):
                            print(f"    ✅ 発見: {test_url}")
                            return test_url
                    except:
                        continue
                
                # 短い間隔で次をテスト
                time.sleep(0.5)
        
        return None
    
    def get_all_sources(self) -> List[Dict]:
        """全sourcesを取得"""
        try:
            result = supabase.table("sources").select("id, name, domain, urls").execute()
            return result.data
        except Exception as e:
            print(f"データベース取得エラー: {e}")
            return []
    
    def verify_and_fix_all_urls(self):
        """全URLの検証と修正"""
        sources = self.get_all_sources()
        
        print(f"🔍 {len(sources)} 個のソースのURL検証開始")
        print("=" * 60)
        
        broken_count = 0
        fixed_count = 0
        
        for i, source in enumerate(sources, 1):
            source_id = source['id']
            name = source['name']
            domain = source['domain']
            urls = source.get('urls', [])
            
            print(f"\n[{i}/{len(sources)}] {name} ({domain})")
            
            if not urls:
                print("    ⚠️ URLが未設定")
                continue
            
            all_working = True
            fixed_urls = []
            
            for url in urls:
                print(f"    テスト中: {url}")
                success, status_code, final_url = self.test_url(url)
                
                if success and status_code == 200:
                    print(f"    ✅ OK ({status_code})")
                    fixed_urls.append(url)
                else:
                    print(f"    ❌ NG ({status_code}) - {url}")
                    broken_count += 1
                    all_working = False
                    
                    # 代替URLを探索
                    print(f"    🔧 代替URL探索中...")
                    working_url = self.find_working_feed(domain)
                    
                    if working_url:
                        fixed_urls.append(working_url)
                        print(f"    🎯 修正URL: {working_url}")
                    else:
                        print(f"    ❌ 代替URL見つからず")
            
            # URLが修正された場合はDB更新
            if not all_working and fixed_urls:
                try:
                    result = supabase.table("sources").update({
                        "urls": fixed_urls
                    }).eq("id", source_id).execute()
                    
                    fixed_count += 1
                    print(f"    ✅ DB更新完了: {fixed_urls}")
                except Exception as e:
                    print(f"    ❌ DB更新エラー: {e}")
            
            # レート制限
            time.sleep(1)
        
        print("\n" + "=" * 60)
        print(f"🎯 検証完了")
        print(f"❌ 問題URL: {broken_count} 個")
        print(f"🔧 修正成功: {fixed_count} 個のソース")
        
        return {
            'total_sources': len(sources),
            'broken_urls': broken_count,
            'fixed_sources': fixed_count
        }
    
    def generate_url_report(self, results: Dict):
        """URL検証レポート生成"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"url_verification_report_{timestamp}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# URL Verification & Fix Report\n\n")
            f.write(f"**実行日時:** {datetime.now().isoformat()}\n\n")
            
            f.write("## 📊 検証結果\n\n")
            f.write(f"- **検証対象:** {results['total_sources']} sources\n")
            f.write(f"- **問題URL:** {results['broken_urls']} 個\n")
            f.write(f"- **修正成功:** {results['fixed_sources']} sources\n\n")
            
            f.write("## 🔧 修正アプローチ\n\n")
            f.write("### ドメイン代替\n")
            for original, alternatives in self.domain_alternatives.items():
                f.write(f"- `{original}` → `{', '.join(alternatives)}`\n")
            
            f.write("\n### フィードパス探索\n")
            for path in self.feed_paths[:8]:  # 最初の8個のみ表示
                f.write(f"- `{path}`\n")
            f.write(f"- その他 {len(self.feed_paths)-8} パターン\n\n")
        
        print(f"📄 レポート生成: {report_file}")

def main():
    verifier = URLVerifier()
    
    # 環境変数チェック
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        print("❌ エラー: SUPABASE_URL と SUPABASE_KEY 環境変数を設定してください")
        return
    
    print("🔧 URL Verification & Fix System")
    print("sourcesテーブルのurlsを検証し、問題があるURLを修正")
    print()
    
    # URL検証・修正実行
    results = verifier.verify_and_fix_all_urls()
    
    # レポート生成
    verifier.generate_url_report(results)
    
    print(f"\n✅ URL検証・修正が完了しました!")

if __name__ == "__main__":
    main()