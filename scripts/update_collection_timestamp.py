#!/usr/bin/env python3
"""
自動収集時にlast_collected_atを更新するサンプルスクリプト

実際の定時収集スクリプト内で以下のような処理を追加する:
1. 新しい記事が見つかった場合のみlast_collected_atを更新
2. 日本時間で記録
"""

import os
from supabase import create_client, Client
from datetime import datetime, timezone, timedelta

# Supabase設定
url = "https://nvchsqotmchzpharujap.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im52Y2hzcW90bWNoenBoYXJ1amFwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDUzMDc2OTAsImV4cCI6MjA2MDg4MzY5MH0.h6MdiDYNySabXxpeS_92KWuwUQlavQqv-9GJyKCn2jo"

def update_collection_timestamp(source_id: str, found_new_articles: bool = True):
    """
    自動収集の実行結果に基づいてlast_collected_atを更新
    
    Args:
        source_id: 情報源のID
        found_new_articles: 新しい記事が見つかったかどうか
    """
    if not found_new_articles:
        print(f"Source {source_id}: 新しい記事が見つからなかったため、タイムスタンプを更新しません")
        return
    
    try:
        supabase: Client = create_client(url, key)
        
        # 日本時間（JST）で現在時刻を取得
        jst = timezone(timedelta(hours=9))
        now_jst = datetime.now(jst)
        
        # last_collected_atを更新
        result = supabase.table('sources').update({
            'last_collected_at': now_jst.isoformat()
        }).eq('id', source_id).eq('acquisition_mode', 'auto').execute()
        
        if result.data:
            print(f"✅ Source {source_id}: 最終収集日時を更新しました - {now_jst.strftime('%Y-%m-%d %H:%M:%S JST')}")
        else:
            print(f"⚠️ Source {source_id}: 更新対象が見つかりませんでした（自動収集モードではない可能性）")
            
    except Exception as e:
        print(f"❌ Source {source_id}: 最終収集日時の更新に失敗 - {str(e)}")

def simulate_collection_process():
    """
    実際の収集処理のシミュレーション
    """
    # 例: 自動収集モードのソース一覧を取得
    supabase: Client = create_client(url, key)
    
    sources_result = supabase.table('sources').select('id, name, urls').eq('acquisition_mode', 'auto').eq('deleted', False).execute()
    
    print(f"📡 自動収集対象: {len(sources_result.data)}件")
    
    for source in sources_result.data:
        print(f"\n🔄 処理中: {source['name']}")
        
        # ここで実際のRSS収集処理を行う
        # ...
        
        # 例: 50%の確率で新記事が見つかったとする
        import random
        found_new = random.choice([True, False])
        
        if found_new:
            print(f"  📰 新しい記事が見つかりました")
            update_collection_timestamp(source['id'], True)
        else:
            print(f"  📰 新しい記事はありませんでした")
            update_collection_timestamp(source['id'], False)

if __name__ == "__main__":
    print("🚀 自動収集シミュレーション開始")
    simulate_collection_process()
    print("\n✅ 完了")