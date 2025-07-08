#!/usr/bin/env python3
"""
既存のacquisition_modeを活用したソース制御
- auto: 定時タスクで自動処理
- manual: 手動のみ
- disabled: 一時停止（問題があるソース）
"""
import os
import requests
from typing import Dict, List
from supabase import create_client, Client

# Supabase接続
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

class AcquisitionModeManager:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def add_disabled_mode(self):
        """acquisition_modeに'disabled'を追加するSQL生成"""
        sql_commands = [
            "-- acquisition_mode に 'disabled' オプションを追加",
            "-- 現在: 'auto', 'manual'",
            "-- 追加: 'disabled' (一時停止用)",
            "",
            "-- CHECKconstraint を更新（PostgreSQLの場合）", 
            "-- ALTER TABLE sources DROP CONSTRAINT IF EXISTS sources_acquisition_mode_check;",
            "-- ALTER TABLE sources ADD CONSTRAINT sources_acquisition_mode_check ",
            "--   CHECK (acquisition_mode IN ('auto', 'manual', 'disabled'));",
            "",
            "-- 現在の acquisition_mode 確認",
            "SELECT acquisition_mode, COUNT(*) as count",
            "FROM sources",
            "GROUP BY acquisition_mode;",
            "",
            "-- 問題のあるソースを disabled に変更（例）",
            "-- UPDATE sources SET acquisition_mode = 'disabled' ",
            "-- WHERE domain = 'problematic-domain.com';",
        ]
        
        with open('add_disabled_acquisition_mode.sql', 'w', encoding='utf-8') as f:
            f.write('\n'.join(sql_commands))
        
        print("📄 SQL生成完了: add_disabled_acquisition_mode.sql")
    
    def test_source_url(self, url: str) -> Dict:
        """URLの状態テスト"""
        try:
            response = self.session.head(url, timeout=10, allow_redirects=True)
            return {
                'accessible': response.status_code == 200,
                'status_code': response.status_code,
                'error': None
            }
        except Exception as e:
            return {
                'accessible': False,
                'status_code': 0,
                'error': str(e)[:100]
            }
    
    def analyze_and_update_sources(self):
        """ソース分析してacquisition_modeを更新"""
        # 全ソース取得
        try:
            result = supabase.table("sources").select("id, name, domain, urls, acquisition_mode").execute()
            sources = result.data
        except Exception as e:
            print(f"❌ データベース取得エラー: {e}")
            return
        
        print(f"🔍 {len(sources)} 個のソースを分析")
        print("=" * 60)
        
        updates = []
        
        for i, source in enumerate(sources, 1):
            source_id = source['id']
            name = source['name']
            domain = source['domain']
            urls = source.get('urls', [])
            current_mode = source['acquisition_mode']
            
            print(f"\n[{i}/{len(sources)}] {name} ({domain})")
            print(f"  現在: {current_mode}")
            
            if not urls:
                print("  ⚠️ URL未設定")
                updates.append({
                    'id': source_id,
                    'name': name,
                    'new_mode': 'disabled',
                    'reason': 'URL未設定'
                })
                continue
            
            # URL accessibility test
            all_accessible = True
            issues = []
            
            for url in urls:
                test_result = self.test_source_url(url)
                print(f"  テスト: {url}")
                
                if test_result['accessible']:
                    print(f"    ✅ OK ({test_result['status_code']})")
                else:
                    print(f"    ❌ NG ({test_result['status_code']}) - {test_result['error']}")
                    all_accessible = False
                    error_msg = test_result['error'][:30] if test_result['error'] else 'Unknown error'
                    issues.append(f"{test_result['status_code']}: {error_msg}")
            
            # acquisition_mode recommendation
            if current_mode == 'auto' and not all_accessible:
                updates.append({
                    'id': source_id,
                    'name': name,
                    'new_mode': 'disabled',
                    'reason': ', '.join(issues[:2])
                })
                print(f"  💡 推奨: auto → disabled")
            elif current_mode == 'disabled' and all_accessible:
                updates.append({
                    'id': source_id,
                    'name': name, 
                    'new_mode': 'auto',
                    'reason': '問題解決'
                })
                print(f"  💡 推奨: disabled → auto")
            else:
                print(f"  ✅ 現状維持: {current_mode}")
        
        return updates
    
    def apply_updates(self, updates: List[Dict]):
        """更新の適用"""
        if not updates:
            print("\n✅ 更新の必要なソースはありません")
            return
        
        print(f"\n🔄 {len(updates)} 個のソースを更新")
        print("=" * 40)
        
        for update in updates:
            try:
                result = supabase.table("sources").update({
                    "acquisition_mode": update['new_mode']
                }).eq("id", update['id']).execute()
                
                print(f"✅ {update['name']}: → {update['new_mode']}")
                print(f"   理由: {update['reason']}")
                
            except Exception as e:
                print(f"❌ {update['name']}: 更新エラー - {e}")
    
    def show_current_status(self):
        """現在のacquisition_mode分布を表示"""
        try:
            result = supabase.table("sources").select("acquisition_mode").execute()
            sources = result.data
            
            mode_counts = {}
            for source in sources:
                mode = source.get('acquisition_mode', 'unknown')
                mode_counts[mode] = mode_counts.get(mode, 0) + 1
            
            print("📊 現在のacquisition_mode分布:")
            for mode, count in sorted(mode_counts.items()):
                emoji = "🤖" if mode == "auto" else "👤" if mode == "manual" else "⏸️" if mode == "disabled" else "❓"
                print(f"  {emoji} {mode}: {count} 個")
                
        except Exception as e:
            print(f"❌ 状況確認エラー: {e}")

def update_crawl_script_code():
    """crawl.py用の修正コード生成"""
    crawl_code = '''
# crawl.py の修正コード

# 変更前:
# sources_result = supabase.table("sources").select("*").eq("acquisition_mode", "auto").execute()

# 変更後（そのまま、'auto'のみ取得）:
sources_result = supabase.table("sources").select("*").eq("acquisition_mode", "auto").execute()
sources = sources_result.data

print(f"自動収集対象: {len(sources)} 件 (acquisition_mode='auto')")

# disabled ソースは自動的に除外される
# manual ソースも除外される（手動実行用）
'''
    
    with open('crawl_acquisition_mode_filter.py', 'w', encoding='utf-8') as f:
        f.write(crawl_code)
    
    print("📄 crawl.py用コード生成: crawl_acquisition_mode_filter.py")

def main():
    manager = AcquisitionModeManager()
    
    # 環境変数チェック
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        print("❌ エラー: SUPABASE_URL と SUPABASE_KEY 環境変数を設定してください")
        return
    
    print("🎛️ Acquisition Mode Management System")
    print("既存のacquisition_modeを活用したソース制御")
    print()
    
    # Step 1: 現在の状況確認
    print("📋 Step 1: 現在の状況確認")
    manager.show_current_status()
    
    # Step 2: disabled モード追加SQL生成
    print("\n📋 Step 2: acquisition_mode拡張")
    manager.add_disabled_mode()
    
    # Step 3: ソース分析
    print("\n📋 Step 3: ソース分析実行")
    updates = manager.analyze_and_update_sources()
    
    # Step 4: 更新適用
    print("\n📋 Step 4: 更新適用")
    if updates:
        print("以下の更新を適用しますか？")
        for update in updates:
            print(f"  - {update['name']}: → {update['new_mode']} ({update['reason']})")
        
        if input("\n適用しますか？ (y/N): ").lower() == 'y':
            manager.apply_updates(updates)
        else:
            print("更新をキャンセルしました")
    
    # Step 5: 最終状況
    print("\n📋 Step 5: 最終状況")
    manager.show_current_status()
    
    # Step 6: crawl.py用コード生成
    update_crawl_script_code()
    
    print("\n🎯 完了! ")
    print("- 問題のあるソースは 'disabled' に変更")
    print("- crawl.py は 'auto' のみ処理（変更不要）")
    print("- 'manual' は手動実行用として保持")

if __name__ == "__main__":
    main()