#!/usr/bin/env python3
"""
既存のsourcesテーブルのdomainを使ってpolicy_urlを自動検索・更新
プライバシーポリシー、利用規約、著作権ポリシーなどを自動発見
"""
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import random
from typing import Dict, List, Optional
from supabase import create_client, Client

# Supabase接続
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

class PolicyURLFinder:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # 各言語でのポリシー関連キーワード
        self.policy_keywords = {
            'english': [
                'privacy policy', 'privacy', 'terms of service', 'terms of use', 
                'copyright', 'legal', 'disclaimer', 'cookie policy', 'data protection'
            ],
            'japanese': [
                'プライバシーポリシー', 'プライバシー', '個人情報保護方針', 
                '利用規約', '著作権', '免責事項', 'Cookie', 'クッキー'
            ],
            'chinese': [
                '隐私政策', '隐私条款', '使用条款', '版权', '免责声明', '数据保护'
            ],
            'korean': [
                '개인정보처리방침', '개인정보보호정책', '이용약관', '저작권', '면책조항'
            ],
            'german': [
                'datenschutz', 'datenschutzerklärung', 'nutzungsbedingungen', 
                'impressum', 'rechtliches', 'urheberrecht'
            ],
            'french': [
                'politique de confidentialité', 'mentions légales', 'conditions d\'utilisation',
                'droits d\'auteur', 'protection des données'
            ]
        }
        
        # よくあるポリシーページのパス
        self.common_policy_paths = [
            '/privacy', '/privacy-policy', '/privacy.html', '/privacy.php',
            '/terms', '/terms-of-service', '/terms-of-use', '/terms.html',
            '/legal', '/legal-notice', '/disclaimer', '/copyright',
            '/cookie-policy', '/data-protection',
            # 日本語サイト用
            '/privacy/', '/policy/', '/legal/', '/terms/',
            '/privacypolicy/', '/privacypolicy.html',
            # 中国語サイト用  
            '/privacy-policy.html', '/terms.html', '/legal.html'
        ]
    
    def get_sources_from_db(self) -> List[Dict]:
        """データベースから全sourcesを取得"""
        try:
            result = supabase.table("sources").select("id, name, domain, country_code, policy_url").execute()
            return result.data
        except Exception as e:
            print(f"データベース取得エラー: {e}")
            return []
    
    def try_common_paths(self, domain: str) -> Optional[str]:
        """よくあるパスでポリシーページを試行"""
        base_url = f"https://{domain}"
        
        for path in self.common_policy_paths:
            url = f"{base_url}{path}"
            try:
                response = self.session.head(url, timeout=10, allow_redirects=True)
                if response.status_code == 200:
                    # 実際にポリシー関連コンテンツか確認
                    if self.verify_policy_content(url):
                        return url
            except:
                continue
        
        return None
    
    def search_in_page_links(self, domain: str) -> Optional[str]:
        """サイトのフッター・ヘッダーからポリシーリンクを検索"""
        try:
            base_url = f"https://{domain}"
            response = self.session.get(base_url, timeout=15)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # フッター、ヘッダー、サイドバーからリンクを検索
            target_areas = soup.find_all(['footer', 'header', 'nav', 'aside'])
            if not target_areas:
                # 全体から検索（ページが小さい場合）
                target_areas = [soup]
            
            for area in target_areas:
                links = area.find_all('a', href=True)
                
                for link in links:
                    href = link.get('href')
                    text = link.get_text().lower().strip()
                    
                    # キーワードマッチング
                    if self.matches_policy_keywords(text):
                        full_url = urljoin(base_url, href)
                        if self.verify_policy_content(full_url):
                            return full_url
        
        except Exception as e:
            print(f"  ページ解析エラー ({domain}): {e}")
        
        return None
    
    def matches_policy_keywords(self, text: str) -> bool:
        """テキストがポリシー関連キーワードにマッチするか判定"""
        text_lower = text.lower()
        
        for lang_keywords in self.policy_keywords.values():
            for keyword in lang_keywords:
                if keyword.lower() in text_lower:
                    return True
        
        return False
    
    def verify_policy_content(self, url: str) -> bool:
        """URLが実際にポリシー関連のコンテンツか確認"""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return False
            
            # HTMLの場合のみチェック
            if 'text/html' not in response.headers.get('content-type', ''):
                return False
            
            content = response.text.lower()
            
            # ポリシー関連の重要キーワードの存在チェック
            policy_indicators = [
                'privacy', 'personal information', 'data protection', 'cookie',
                'プライバシー', '個人情報', '利用規約', '免責',
                '隐私', '个人信息', '使用条款',
                '개인정보', '이용약관', 
                'datenschutz', 'données personnelles'
            ]
            
            found_indicators = sum(1 for indicator in policy_indicators if indicator in content)
            
            # 最低2個以上のキーワードがあればポリシーページと判定
            return found_indicators >= 2
            
        except:
            return False
    
    def find_policy_url(self, domain: str, country_code: str) -> Optional[str]:
        """指定ドメインのポリシーURLを検索"""
        print(f"  🔍 {domain} を検索中...")
        
        # 1. よくあるパスを試行
        policy_url = self.try_common_paths(domain)
        if policy_url:
            print(f"    ✓ 共通パスで発見: {policy_url}")
            return policy_url
        
        # 2. ページ内リンクを検索
        policy_url = self.search_in_page_links(domain)
        if policy_url:
            print(f"    ✓ ページ内リンクで発見: {policy_url}")
            return policy_url
        
        print(f"    ❌ ポリシーURL未発見")
        return None
    
    def update_policy_url(self, source_id: int, policy_url: str) -> bool:
        """データベースのpolicy_urlを更新"""
        try:
            result = supabase.table("sources").update({
                "policy_url": policy_url
            }).eq("id", source_id).execute()
            
            return True
        except Exception as e:
            print(f"    ❌ DB更新エラー: {e}")
            return False
    
    def process_all_sources(self, limit: Optional[int] = None):
        """全sourcesのpolicy_url検索・更新を実行"""
        sources = self.get_sources_from_db()
        
        if limit:
            sources = sources[:limit]
        
        print(f"🚀 {len(sources)} 個のソースのポリシーURL検索開始")
        print("=" * 60)
        
        found_count = 0
        updated_count = 0
        
        for i, source in enumerate(sources, 1):
            source_id = source['id']
            name = source['name']
            domain = source['domain']
            country_code = source.get('country_code', 'Unknown')
            current_policy = source.get('policy_url')
            
            print(f"\n[{i}/{len(sources)}] {name} ({domain})")
            
            # 既にpolicy_urlがある場合はスキップ
            if current_policy:
                print(f"    ℹ️ 既存のポリシーURL: {current_policy}")
                continue
            
            # ポリシーURL検索
            policy_url = self.find_policy_url(domain, country_code)
            
            if policy_url:
                found_count += 1
                
                # データベース更新
                if self.update_policy_url(source_id, policy_url):
                    updated_count += 1
                    print(f"    ✅ DB更新完了")
                
            # レート制限（サイトに負荷をかけないよう）
            time.sleep(random.uniform(2, 4))
        
        print("\n" + "=" * 60)
        print(f"🎯 完了: {found_count} 個のポリシーURL発見, {updated_count} 個DB更新")
        
        return {
            'processed': len(sources),
            'found': found_count,
            'updated': updated_count
        }
    
    def generate_report(self, results: Dict):
        """結果レポート生成"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"policy_url_discovery_report_{timestamp}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Policy URL Discovery Report\n\n")
            f.write(f"**実行日時:** {datetime.now().isoformat()}\n\n")
            
            f.write("## 📊 結果サマリー\n\n")
            f.write(f"- **処理対象:** {results['processed']} sources\n")
            f.write(f"- **発見:** {results['found']} policy URLs\n")
            f.write(f"- **DB更新:** {results['updated']} records\n")
            f.write(f"- **成功率:** {results['found']/results['processed']*100:.1f}%\n\n")
            
            f.write("## 📝 検索対象キーワード\n\n")
            for lang, keywords in self.policy_keywords.items():
                f.write(f"### {lang.title()}\n")
                f.write(f"- {', '.join(keywords)}\n\n")
            
            f.write("## 🔍 検索パス\n\n")
            f.write("### 共通パス試行\n")
            for path in self.common_policy_paths[:10]:  # 最初の10個のみ表示
                f.write(f"- `{path}`\n")
            f.write(f"- その他 {len(self.common_policy_paths)-10} パス\n\n")
            
            f.write("### ページ内リンク検索\n")
            f.write("- フッター、ヘッダー、ナビゲーション内のリンクを検索\n")
            f.write("- キーワードマッチング + コンテンツ検証\n\n")
        
        print(f"📄 レポート生成: {report_file}")

def main():
    finder = PolicyURLFinder()
    
    # 環境変数チェック
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        print("❌ エラー: SUPABASE_URL と SUPABASE_KEY 環境変数を設定してください")
        return
    
    print("🔍 Policy URL Discovery System")
    print("sourcesテーブルのdomainからpolicy_urlを自動検索・更新")
    print()
    
    # テスト実行（最初の5個のみ）
    test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
    limit = 5 if test_mode else None
    
    if test_mode:
        print("🧪 テストモード: 最初の5個のソースのみ処理")
    
    # ポリシーURL検索実行
    results = finder.process_all_sources(limit=limit)
    
    # レポート生成
    finder.generate_report(results)
    
    print(f"\n✅ Policy URL discovery completed!")

if __name__ == "__main__":
    main()