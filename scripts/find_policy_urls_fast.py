#!/usr/bin/env python3
"""
高速版ポリシーURL検索（残りのソースのみ）
タイムアウト短縮・並列処理で効率化
"""
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
from typing import Dict, List, Optional
from supabase import create_client, Client
from concurrent.futures import ThreadPoolExecutor, as_completed

# Supabase接続
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

class FastPolicyFinder:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 高確率パスのみに絞り込み（速度優先）
        self.priority_paths = [
            '/privacy', '/privacy-policy', '/terms', '/legal',
            '/privacy.html', '/privacy/', '/datenschutz'
        ]
    
    def get_sources_without_policy(self) -> List[Dict]:
        """policy_urlが未設定のソースのみ取得"""
        try:
            result = supabase.table("sources").select("id, name, domain").is_("policy_url", "null").execute()
            return result.data
        except Exception as e:
            print(f"データベース取得エラー: {e}")
            return []
    
    def try_fast_paths(self, domain: str) -> Optional[str]:
        """高速パス試行（タイムアウト短縮）"""
        base_url = f"https://{domain}"
        
        for path in self.priority_paths:
            url = f"{base_url}{path}"
            try:
                response = self.session.head(url, timeout=5, allow_redirects=True)
                if response.status_code == 200:
                    return url
            except:
                continue
        
        return None
    
    def search_homepage_links(self, domain: str) -> Optional[str]:
        """ホームページから高速リンク検索"""
        try:
            base_url = f"https://{domain}"
            response = self.session.get(base_url, timeout=8)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # フッターのみに限定（高速化）
            footer = soup.find('footer')
            if not footer:
                return None
            
            links = footer.find_all('a', href=True)
            
            policy_keywords = [
                'privacy', 'プライバシー', '个人信息', '개인정보', 'datenschutz'
            ]
            
            for link in links:
                text = link.get_text().lower().strip()
                href = link.get('href')
                
                if any(keyword in text for keyword in policy_keywords):
                    return urljoin(base_url, href)
        
        except:
            pass
        
        return None
    
    def find_policy_for_source(self, source: Dict) -> Optional[str]:
        """単一ソースのポリシーURL検索"""
        domain = source['domain']
        name = source['name']
        
        print(f"  🔍 {name} ({domain})")
        
        # 1. 高速パス試行
        policy_url = self.try_fast_paths(domain)
        if policy_url:
            print(f"    ✓ 発見: {policy_url}")
            return policy_url
        
        # 2. ホームページリンク検索
        policy_url = self.search_homepage_links(domain)
        if policy_url:
            print(f"    ✓ 発見: {policy_url}")
            return policy_url
        
        print(f"    ❌ 未発見")
        return None
    
    def update_policy_url(self, source_id: int, policy_url: str) -> bool:
        """DB更新"""
        try:
            supabase.table("sources").update({
                "policy_url": policy_url
            }).eq("id", source_id).execute()
            return True
        except Exception as e:
            print(f"    ❌ DB更新エラー: {e}")
            return False
    
    def process_remaining_sources(self):
        """残りのソースを並列処理"""
        sources = self.get_sources_without_policy()
        
        if not sources:
            print("✅ 全てのソースにpolicy_urlが設定済みです")
            return
        
        print(f"🚀 残り {len(sources)} 個のソースを高速処理")
        print("=" * 50)
        
        found_count = 0
        updated_count = 0
        
        # 並列処理で高速化（最大3スレッド）
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_source = {
                executor.submit(self.find_policy_for_source, source): source 
                for source in sources
            }
            
            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    policy_url = future.result()
                    
                    if policy_url:
                        found_count += 1
                        
                        # DB更新
                        if self.update_policy_url(source['id'], policy_url):
                            updated_count += 1
                        
                        # 少し間隔を開ける
                        time.sleep(1)
                
                except Exception as e:
                    print(f"    ❌ エラー ({source['name']}): {e}")
        
        print("=" * 50)
        print(f"🎯 高速処理完了: {found_count} 個発見, {updated_count} 個更新")
        
        return {
            'processed': len(sources),
            'found': found_count,
            'updated': updated_count
        }

def main():
    finder = FastPolicyFinder()
    
    # 環境変数チェック
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        print("❌ エラー: SUPABASE_URL と SUPABASE_KEY 環境変数を設定してください")
        return
    
    print("⚡ 高速Policy URL Discovery")
    print("未設定のソースのみを並列処理で高速検索")
    print()
    
    # 高速処理実行
    results = finder.process_remaining_sources()
    
    if results:
        print(f"\n✅ 高速処理完了!")
        
        # 最終状況確認
        print("\n📊 最終確認中...")
        time.sleep(2)
        
        all_sources = supabase.table("sources").select("policy_url").execute()
        filled = sum(1 for s in all_sources.data if s.get('policy_url'))
        total = len(all_sources.data)
        
        print(f"📊 最終結果: {filled}/{total} 個 ({filled/total*100:.1f}%) にpolicy_url設定完了")

if __name__ == "__main__":
    main()