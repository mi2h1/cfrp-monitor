#!/usr/bin/env python3
"""
sourcesテーブルにactiveフラグを追加して取得制御
- 取得困難なソースは一時停止
- 情報源としては保持
- 定時タスクでは active=true のみ処理
"""
import os
import requests
from urllib.parse import urlparse
import time
from typing import Dict, List, Optional
from supabase import create_client, Client

# Supabase接続
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

class SourceActivationManager:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def add_active_column(self):
        """sourcesテーブルにactiveカラムを追加（SQL実行が必要）"""
        sql_commands = [
            "-- sourcesテーブルにactiveフラグ追加",
            "ALTER TABLE sources ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT true;",
            "",
            "-- デフォルトで全てのソースをアクティブに設定",
            "UPDATE sources SET active = true WHERE active IS NULL;",
            "",
            "-- activeカラムにインデックス追加（パフォーマンス向上）",
            "CREATE INDEX IF NOT EXISTS idx_sources_active ON sources(active);",
            "",
            "-- 確認用クエリ",
            "-- SELECT name, domain, active FROM sources ORDER BY active DESC, name;"
        ]
        
        with open('add_active_column.sql', 'w', encoding='utf-8') as f:
            f.write('\n'.join(sql_commands))
        
        print("📄 SQL生成完了: add_active_column.sql")
        print("このSQLをSupabaseで実行してください")
    
    def test_source_accessibility(self, source: Dict) -> Dict:
        """ソースのアクセス可能性をテスト"""
        result = {
            'source_id': source['id'],
            'name': source['name'],
            'domain': source['domain'],
            'urls': source.get('urls', []),
            'accessible': False,
            'issues': [],
            'recommended_active': True
        }
        
        if not result['urls']:
            result['issues'].append('URL未設定')
            result['recommended_active'] = False
            return result
        
        for url in result['urls']:
            print(f"  テスト中: {url}")
            
            try:
                # HEADリクエストで状態確認
                response = self.session.head(url, timeout=10, allow_redirects=True)
                
                if response.status_code == 200:
                    print(f"    ✅ OK ({response.status_code})")
                    result['accessible'] = True
                    break
                elif response.status_code == 404:
                    print(f"    ❌ 404 Not Found")
                    result['issues'].append('404 Not Found')
                elif response.status_code in [403, 429]:
                    print(f"    ⚠️ アクセス制限 ({response.status_code})")
                    result['issues'].append(f'アクセス制限 ({response.status_code})')
                else:
                    print(f"    ⚠️ 応答異常 ({response.status_code})")
                    result['issues'].append(f'応答異常 ({response.status_code})')
                    
            except requests.exceptions.SSLError:
                print(f"    ❌ SSL証明書エラー")
                result['issues'].append('SSL証明書エラー')
            except requests.exceptions.ConnectionError:
                print(f"    ❌ 接続エラー")
                result['issues'].append('接続エラー')
            except requests.exceptions.Timeout:
                print(f"    ❌ タイムアウト")
                result['issues'].append('タイムアウト')
            except Exception as e:
                print(f"    ❌ その他エラー: {e}")
                result['issues'].append(f'その他エラー: {str(e)[:50]}')
        
        # アクセス困難な場合は非アクティブを推奨
        if not result['accessible'] and result['issues']:
            if any(issue in ['404 Not Found', 'SSL証明書エラー', '接続エラー'] for issue in result['issues']):
                result['recommended_active'] = False
        
        return result
    
    def get_all_sources(self) -> List[Dict]:
        """全sourcesを取得"""
        try:
            result = supabase.table("sources").select("id, name, domain, urls, active").execute()
            return result.data
        except Exception as e:
            print(f"データベース取得エラー: {e}")
            return []
    
    def update_source_active_status(self, source_id: int, active: bool, reason: str = "") -> bool:
        """ソースのactiveステータス更新"""
        try:
            data = {"active": active}
            if reason:
                data["notes"] = f"Auto-disabled: {reason}"
            
            result = supabase.table("sources").update(data).eq("id", source_id).execute()
            return True
        except Exception as e:
            print(f"    ❌ DB更新エラー: {e}")
            return False
    
    def analyze_all_sources(self):
        """全ソースの分析とactiveステータス更新"""
        sources = self.get_all_sources()
        
        print(f"🔍 {len(sources)} 個のソースのアクセス可能性を分析")
        print("=" * 60)
        
        active_count = 0
        inactive_count = 0
        updated_count = 0
        
        results = []
        
        for i, source in enumerate(sources, 1):
            print(f"\n[{i}/{len(sources)}] {source['name']} ({source['domain']})")
            
            # アクセス可能性テスト
            test_result = self.test_source_accessibility(source)
            results.append(test_result)
            
            current_active = source.get('active', True)
            recommended_active = test_result['recommended_active']
            
            if current_active != recommended_active:
                # ステータス更新
                reason = ', '.join(test_result['issues'][:2])  # 最初の2つの問題
                if self.update_source_active_status(source['id'], recommended_active, reason):
                    updated_count += 1
                    status_change = "✅ アクティブ化" if recommended_active else "⏸️ 非アクティブ化"
                    print(f"    {status_change}: {reason}")
            
            if recommended_active:
                active_count += 1
            else:
                inactive_count += 1
            
            # レート制限
            time.sleep(1)
        
        print("\n" + "=" * 60)
        print(f"🎯 分析完了")
        print(f"✅ アクティブ: {active_count} 個")
        print(f"⏸️ 非アクティブ: {inactive_count} 個")
        print(f"🔄 ステータス更新: {updated_count} 個")
        
        return results
    
    def generate_status_report(self, results: List[Dict]):
        """ステータスレポート生成"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"source_activation_report_{timestamp}.md"
        
        active_sources = [r for r in results if r['recommended_active']]
        inactive_sources = [r for r in results if not r['recommended_active']]
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Source Activation Status Report\n\n")
            f.write(f"**実行日時:** {datetime.now().isoformat()}\n\n")
            
            f.write("## 📊 概要\n\n")
            f.write(f"- **総ソース数:** {len(results)}\n")
            f.write(f"- **アクティブ:** {len(active_sources)} ({len(active_sources)/len(results)*100:.1f}%)\n")
            f.write(f"- **非アクティブ:** {len(inactive_sources)} ({len(inactive_sources)/len(results)*100:.1f}%)\n\n")
            
            if active_sources:
                f.write("## ✅ アクティブソース\n\n")
                for source in active_sources:
                    f.write(f"### {source['name']}\n")
                    f.write(f"- **ドメイン:** {source['domain']}\n")
                    f.write(f"- **URL数:** {len(source['urls'])}\n")
                    f.write(f"- **ステータス:** 正常\n\n")
            
            if inactive_sources:
                f.write("## ⏸️ 非アクティブソース\n\n")
                for source in inactive_sources:
                    f.write(f"### {source['name']}\n")
                    f.write(f"- **ドメイン:** {source['domain']}\n")
                    f.write(f"- **問題:** {', '.join(source['issues'])}\n")
                    f.write(f"- **推奨:** 一時停止\n\n")
        
        print(f"📄 レポート生成: {report_file}")

def update_crawl_script():
    """crawl.pyにactiveフィルタを追加するコード生成"""
    
    crawl_update_code = '''
# crawl.py の修正（activeフィルタ追加）

# 変更前:
# sources_result = supabase.table("sources").select("*").eq("acquisition_mode", "auto").execute()

# 変更後:
sources_result = supabase.table("sources").select("*").eq("acquisition_mode", "auto").eq("active", True).execute()

print(f"自動収集対象（アクティブのみ）: {len(sources.data)} 件")
'''
    
    with open('crawl_active_filter.py', 'w', encoding='utf-8') as f:
        f.write(crawl_update_code)
    
    print("📄 crawl.py修正コード生成: crawl_active_filter.py")

def main():
    manager = SourceActivationManager()
    
    # 環境変数チェック
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        print("❌ エラー: SUPABASE_URL と SUPABASE_KEY 環境変数を設定してください")
        return
    
    print("🎛️ Source Activation Management System")
    print("アクセス困難なソースを自動的に非アクティブ化")
    print()
    
    # Step 1: activeカラム追加SQL生成
    print("📋 Step 1: activeカラム追加")
    manager.add_active_column()
    
    print("\n⏳ add_active_column.sql を実行してから続行してください...")
    input("SQLを実行したら Enter を押してください...")
    
    # Step 2: 全ソースの分析
    print("\n📋 Step 2: ソース分析実行")
    results = manager.analyze_all_sources()
    
    # Step 3: レポート生成
    manager.generate_status_report(results)
    
    # Step 4: crawl.py修正コード生成
    update_crawl_script()
    
    print("\n🎯 完了! 次のステップ:")
    print("1. crawl_active_filter.py のコードを crawl.py に適用")
    print("2. 非アクティブソースは定時タスクから除外される")
    print("3. 将来的に修復可能になったら手動でアクティブ化")

if __name__ == "__main__":
    main()