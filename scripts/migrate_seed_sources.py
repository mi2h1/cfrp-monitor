#!/usr/bin/env python3
"""
seed_sources.ymlのデータをsourcesテーブルに移行するスクリプト
使用方法: python scripts/migrate_seed_sources.py

前提条件:
1. migration/01_add_sources_columns.sql を実行済み
2. SUPABASE_URL, SUPABASE_KEY 環境変数が設定済み
"""

import os
import yaml
import urllib.parse
from supabase import create_client, Client
from datetime import datetime

def main():
    # Supabase接続
    supabase: Client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    
    # seed_sources.yml読み込み
    with open("seed_sources.yml", encoding="utf-8") as f:
        sources = yaml.safe_load(f)
    
    print(f"🚀 移行開始: {len(sources)} 件のソース")
    
    migrated = 0
    errors = 0
    
    for src in sources:
        try:
            # URLsからドメイン抽出
            urls = src.get("urls", [])
            if not urls:
                # apiキーがある場合はそれを使用
                if src.get("api"):
                    urls = [src["api"]]
                else:
                    print(f"⚠️  URL未設定: {src.get('name', '不明')}")
                    continue
            
            # 最初のURLからドメイン抽出
            domain = urllib.parse.urlparse(urls[0]).netloc.lower()
            
            # 移行データ作成
            migration_data = {
                "domain": domain,
                "name": src.get("name"),
                "category": src.get("category", "other"),
                "urls": urls,
                "parser": src.get("parser", "rss"),
                "ua": src.get("ua"),
                "http_fallback": src.get("http_fallback", False),
                "retry_count": src.get("retry", 3),
                "backoff_factor": src.get("backoff", 1.0),
                "acquisition_mode": "auto",  # seed_sources.yml由来は自動収集
                "access_level": 2,  # URL設定済みなのでレベル2
                "relevance": 3,  # デフォルト優先度
                "last_checked": datetime.utcnow().isoformat()
            }
            
            # upsert実行
            result = supabase.table("sources").upsert(
                migration_data, 
                on_conflict="domain"
            ).execute()
            
            if hasattr(result, 'error') and result.error:
                raise Exception(result.error)
            
            print(f"✅ 移行完了: {src.get('name')} ({domain})")
            migrated += 1
            
        except Exception as e:
            print(f"❌ 移行失敗: {src.get('name', '不明')} - {e}")
            errors += 1
    
    print(f"\n📊 移行結果:")
    print(f"  ✅ 成功: {migrated} 件")
    print(f"  ❌ 失敗: {errors} 件")
    print(f"  📝 合計: {migrated + errors} 件")
    
    # 移行後の確認
    print(f"\n🔍 移行後の確認:")
    auto_sources = supabase.table("sources").select("*").eq("acquisition_mode", "auto").execute()
    print(f"  自動収集対象: {len(auto_sources.data)} 件")
    
    for src in auto_sources.data:
        print(f"    - {src.get('name', src.get('domain'))}")

if __name__ == "__main__":
    main()