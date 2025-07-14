#!/usr/bin/env python3
"""
ローカル実行用: 既存のJSONファイルからDBへの候補移行
"""
import subprocess
import sys
import os

def main():
    print("🔄 既存の候補JSONファイルをDBに移行します")
    print("=" * 50)
    
    # 環境変数チェック
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        print("❌ 環境変数が設定されていません:")
        print("  - SUPABASE_URL")
        print("  - SUPABASE_KEY")
        print("\n設定例:")
        print("  export SUPABASE_URL='your-supabase-url'")
        print("  export SUPABASE_KEY='your-supabase-key'")
        return
    
    # 確認
    response = input("\n⚠️  この操作は既存のJSONファイルからDBに候補を移行します。\n続行しますか？ (yes/no): ")
    
    if response.lower() != 'yes':
        print("❌ 操作をキャンセルしました")
        return
    
    try:
        # 移行スクリプトを実行
        print("\n🚀 移行スクリプトを実行中...")
        result = subprocess.run([
            sys.executable, 
            "scripts/migrate_json_candidates.py"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("エラー出力:", result.stderr)
        
        if result.returncode == 0:
            print("\n✅ 移行が正常に完了しました！")
            print("📋 情報源管理画面の「🔍 探索候補」タブで確認してください")
        else:
            print(f"\n❌ 移行でエラーが発生しました (終了コード: {result.returncode})")
            
    except Exception as e:
        print(f"❌ 実行エラー: {str(e)}")

if __name__ == "__main__":
    main()