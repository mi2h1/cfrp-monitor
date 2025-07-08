#!/usr/bin/env python3
"""
データベースを完全にクリアして過去1ヶ月のrawデータから再構築
"""
import os
import json
import glob
from datetime import datetime, timedelta
from pathlib import Path
from supabase import create_client, Client
from dateutil import parser as dtparser
import pytz

# Supabase接続
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def clear_database():
    """データベースを完全クリア"""
    print("🗑️ データベースをクリア中...")
    
    try:
        # 既存データを取得してから削除
        items_result = supabase.table("items").select("id").execute()
        if items_result.data:
            for item in items_result.data:
                supabase.table("items").delete().eq("id", item["id"]).execute()
        print(f"   items削除: {len(items_result.data)} 件")
        
        sources_result = supabase.table("sources").select("id").execute()
        if sources_result.data:
            for source in sources_result.data:
                supabase.table("sources").delete().eq("id", source["id"]).execute()
        print(f"   sources削除: {len(sources_result.data)} 件")
        
    except Exception as e:
        print(f"   ⚠️ クリア処理で一部エラー: {e}")
        print("   続行します...")

def setup_sources():
    """基本的なsourcesを再セットアップ"""
    print("📝 sourcesテーブルを再構築中...")
    
    initial_sources = [
        {
            "name": "CompositesWorld",
            "urls": ["https://www.compositesworld.com/rss/news"],
            "parser": "rss",
            "acquisition_mode": "auto",
            "category": "news",
            "domain": "compositesworld.com",
            "country_code": "US",
            "relevance": 8
        },
        {
            "name": "arXiv CFRP papers", 
            "urls": ["https://export.arxiv.org/api/query?search_query=all:CFRP&max_results=50&sortBy=submittedDate&sortOrder=descending"],
            "parser": "rss",
            "acquisition_mode": "auto", 
            "category": "paper",
            "domain": "arxiv.org",
            "country_code": "US",
            "relevance": 9
        }
    ]
    
    for source in initial_sources:
        result = supabase.table("sources").insert(source).execute()
        print(f"   ✓ {source['name']} 追加")
    
    return {src["name"]: src for src in initial_sources}

def safe_date(txt):
    """安全な日付パース（日本時間）"""
    try:
        if not txt:
            return None
        
        # 日付をパース
        parsed_date = dtparser.parse(txt)
        
        # タイムゾーンが設定されていない場合はUTCと仮定
        if parsed_date.tzinfo is None:
            parsed_date = pytz.utc.localize(parsed_date)
        
        # 日本時間に変換
        jst = pytz.timezone('Asia/Tokyo')
        japan_time = parsed_date.astimezone(jst)
        
        return japan_time.date().isoformat()
    except Exception:
        return None

def safe_datetime(txt):
    """安全な日時パース（日本時間）"""
    try:
        if not txt:
            # 現在の日本時間を返す
            jst = pytz.timezone('Asia/Tokyo')
            return datetime.now(jst).isoformat()
        
        # 日時をパース
        parsed_datetime = dtparser.parse(txt)
        
        # タイムゾーンが設定されていない場合はUTCと仮定
        if parsed_datetime.tzinfo is None:
            parsed_datetime = pytz.utc.localize(parsed_datetime)
        
        # 日本時間に変換
        jst = pytz.timezone('Asia/Tokyo')
        japan_time = parsed_datetime.astimezone(jst)
        
        return japan_time.isoformat()
    except Exception:
        # エラー時は現在の日本時間
        jst = pytz.timezone('Asia/Tokyo')
        return datetime.now(jst).isoformat()

def get_source_id_by_filename(filename, source_mapping):
    """ファイル名からsource_idを特定"""
    if "CompositesWorld" in filename:
        return source_mapping["CompositesWorld"]["id"] if "CompositesWorld" in source_mapping else 1
    elif "arXiv" in filename:
        return source_mapping["arXiv CFRP papers"]["id"] if "arXiv CFRP papers" in source_mapping else 2
    return None

def rebuild_items_from_raw():
    """rawデータからitemsを再構築"""
    print("🔄 rawデータからitemsを再構築中...")
    
    # sourcesテーブルから現在の情報を取得
    sources_result = supabase.table("sources").select("*").execute()
    source_mapping = {s["name"]: s for s in sources_result.data}
    
    raw_dir = Path("raw")
    processed_count = 0
    
    # 1ヶ月前から今日まで
    start_date = datetime.now() - timedelta(days=30)
    
    for date_dir in sorted(raw_dir.glob("2025-*")):
        try:
            date_str = date_dir.name
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            # 1ヶ月前以降のデータのみ処理
            if file_date < start_date:
                continue
                
            print(f"   📅 {date_str} を処理中...")
            
            # 各JSONファイルを処理
            for json_file in date_dir.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        entries = json.load(f)
                    
                    source_id = get_source_id_by_filename(json_file.name, source_mapping)
                    if not source_id:
                        print(f"      ⚠️ source_id特定失敗: {json_file.name}")
                        continue
                    
                    # 各エントリーをitemsに追加
                    for entry in entries:
                        # 日本時間での追加時刻を設定（タイムゾーン情報なしで保存）
                        jst = pytz.timezone('Asia/Tokyo')
                        added_at_jst = datetime.now(jst).replace(tzinfo=None).isoformat()
                        
                        item_data = {
                            "src_type": "news" if "CompositesWorld" in json_file.name else "paper",
                            "source_id": source_id,
                            "title": entry.get("title"),
                            "url": entry.get("link") or entry.get("id"),
                            "pub_date": safe_date(entry.get("published") or entry.get("updated")),
                            "body": entry.get("content", [{}])[0].get("value") if entry.get("content") else entry.get("summary"),
                            "added_at": added_at_jst
                        }
                        
                        # 必須フィールドチェック
                        if not item_data["url"] or not item_data["title"]:
                            continue
                        
                        try:
                            result = supabase.table("items").upsert(item_data, on_conflict="url").execute()
                            processed_count += 1
                            
                            if processed_count % 50 == 0:
                                print(f"      📊 {processed_count} 件処理完了")
                                
                        except Exception as e:
                            print(f"      ❌ アイテム追加エラー: {e}")
                
                except Exception as e:
                    print(f"      ❌ ファイル処理エラー {json_file}: {e}")
        
        except Exception as e:
            print(f"   ❌ 日付ディレクトリエラー {date_dir}: {e}")
    
    print(f"✅ 再構築完了: {processed_count} 件のアイテムを追加")

def main():
    """メイン処理"""
    print("🚀 データベース再構築開始")
    print("=" * 50)
    
    # 環境変数チェック
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        print("❌ エラー: SUPABASE_URL と SUPABASE_KEY 環境変数を設定してください")
        return
    
    try:
        # Step 1: データベースクリア
        clear_database()
        
        # Step 2: 基本sourcesセットアップ  
        setup_sources()
        
        # Step 3: rawデータからitems再構築
        rebuild_items_from_raw()
        
        print("=" * 50)
        print("🎉 データベース再構築が完了しました！")
        
        # 最終確認
        items_count = supabase.table("items").select("id", count="exact").execute()
        sources_count = supabase.table("sources").select("id", count="exact").execute()
        
        print(f"📊 最終結果:")
        print(f"   - Sources: {sources_count.count} 件")
        print(f"   - Items: {items_count.count} 件")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    main()