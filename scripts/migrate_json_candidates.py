#!/usr/bin/env python3
"""
既存のJSONファイルから候補データをDBに移行するスクリプト
GitHub Actions で手動実行可能
"""
import os
import json
import glob
import time
from datetime import datetime
from urllib.parse import urlparse
from supabase import create_client, Client

# Supabase接続
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def extract_domain(url: str) -> str:
    """URLからドメインを抽出"""
    try:
        parsed = urlparse(url)
        return parsed.netloc or url
    except:
        return url

def detect_country_from_language(language: str) -> str:
    """言語から国コードを推定"""
    mapping = {
        'japanese': 'JP',
        'german': 'DE',
        'french': 'FR',
        'chinese': 'CN',
        'korean': 'KR',
        'italian': 'IT',
        'spanish': 'ES',
        'russian': 'RU',
        'english': 'US'
    }
    return mapping.get(language, 'unknown')

def migrate_multilingual_json():
    """多言語JSONファイルを移行"""
    print("🌍 多言語JSONファイルの移行開始")
    
    # 多言語JSONファイルを検索
    json_files = glob.glob("multilingual_sources_*.json")
    
    if not json_files:
        print("多言語JSONファイルが見つかりません")
        return 0
    
    total_migrated = 0
    
    for json_file in json_files:
        print(f"\n📁 処理中: {json_file}")
        
        # ファイル名から言語を抽出
        filename = os.path.basename(json_file)
        language = 'unknown'
        
        if 'japanese' in filename:
            language = 'japanese'
        elif 'german' in filename:
            language = 'german'
        elif 'chinese' in filename:
            language = 'chinese'
        elif 'korean' in filename:
            language = 'korean'
        elif 'french' in filename:
            language = 'french'
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                sources = json.load(f)
            
            print(f"  - {len(sources)} 件の候補を発見")
            
            for source in sources:
                try:
                    # 候補データを変換
                    candidate_data = {
                        'name': source.get('name', 'Unknown'),
                        'domain': extract_domain(source.get('site_url', '')),
                        'urls': source.get('urls', []),
                        'site_url': source.get('site_url', ''),
                        'category': 'unknown',
                        'language': language,
                        'country_code': detect_country_from_language(language),
                        'relevance_score': float(source.get('relevance_score', 0.5)),
                        'discovery_method': 'weekly_multilingual_discovery',
                        'metadata': {
                            'discovered_at': source.get('discovered_at', ''),
                            'source_type': 'multilingual_search',
                            'search_language': language,
                            'feeds_found': len(source.get('urls', [])),
                            'migrated_from': json_file
                        }
                    }
                    
                    # 重複チェック（ドメインでUPSERT）
                    existing = supabase.table('source_candidates').select('id').eq('domain', candidate_data['domain']).execute()
                    
                    if existing.data:
                        print(f"    スキップ（重複）: {candidate_data['name']} ({candidate_data['domain']})")
                    else:
                        # 新規候補を挿入
                        result = supabase.table('source_candidates').insert(candidate_data).execute()
                        print(f"    追加: {candidate_data['name']} ({candidate_data['domain']})")
                        total_migrated += 1
                        
                except Exception as e:
                    print(f"    エラー: {source.get('name', 'Unknown')} - {str(e)}")
                    
        except Exception as e:
            print(f"  ファイル読み込みエラー: {str(e)}")
    
    return total_migrated

def migrate_article_json():
    """記事ベースJSONファイルを移行"""
    print("\n📰 記事ベースJSONファイルの移行開始")
    
    # 記事ベースJSONファイルを検索
    json_files = glob.glob("article_source_candidates_*.json")
    
    if not json_files:
        print("記事ベースJSONファイルが見つかりません")
        return 0
    
    total_migrated = 0
    
    for json_file in json_files:
        print(f"\n📁 処理中: {json_file}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                candidates = json.load(f)
            
            print(f"  - {len(candidates)} 件の候補を発見")
            
            for candidate in candidates:
                try:
                    # 候補データを変換
                    candidate_data = {
                        'name': candidate.get('name', 'Unknown'),
                        'domain': extract_domain(candidate.get('domain', '')),
                        'urls': [candidate.get('feed_url', '')],
                        'site_url': candidate.get('domain', ''),
                        'category': 'unknown',
                        'language': 'unknown',
                        'country_code': 'unknown',
                        'relevance_score': 0.7,
                        'discovery_method': 'weekly_source_discovery',
                        'metadata': {
                            'occurrence_count': candidate.get('occurrence_count', 0),
                            'discovered_at': candidate.get('discovered_at', ''),
                            'source_type': 'article_analysis',
                            'migrated_from': json_file
                        }
                    }
                    
                    # 重複チェック（ドメインでUPSERT）
                    existing = supabase.table('source_candidates').select('id').eq('domain', candidate_data['domain']).execute()
                    
                    if existing.data:
                        print(f"    スキップ（重複）: {candidate_data['name']} ({candidate_data['domain']})")
                    else:
                        # 新規候補を挿入
                        result = supabase.table('source_candidates').insert(candidate_data).execute()
                        print(f"    追加: {candidate_data['name']} ({candidate_data['domain']})")
                        total_migrated += 1
                        
                except Exception as e:
                    print(f"    エラー: {candidate.get('name', 'Unknown')} - {str(e)}")
                    
        except Exception as e:
            print(f"  ファイル読み込みエラー: {str(e)}")
    
    return total_migrated

def main():
    print("🚀 JSONファイルからDBへの候補移行開始")
    print("=" * 50)
    
    start_time = time.time()
    
    # 現在のディレクトリのJSONファイルを確認
    all_json_files = glob.glob("*.json")
    multilingual_files = glob.glob("multilingual_sources_*.json")
    article_files = glob.glob("article_source_candidates_*.json")
    
    print(f"📊 ファイル発見状況:")
    print(f"  - 全JSONファイル: {len(all_json_files)} 件")
    print(f"  - 多言語ファイル: {len(multilingual_files)} 件")
    print(f"  - 記事ベースファイル: {len(article_files)} 件")
    
    if not multilingual_files and not article_files:
        print("\n❌ 移行対象のJSONファイルが見つかりません")
        print("以下のファイルを確認してください：")
        print("  - multilingual_sources_*.json")
        print("  - article_source_candidates_*.json")
        return
    
    # 移行実行
    multilingual_count = migrate_multilingual_json()
    article_count = migrate_article_json()
    
    total_count = multilingual_count + article_count
    end_time = time.time()
    
    print(f"\n🎉 移行完了!")
    print(f"  - 多言語候補: {multilingual_count} 件")
    print(f"  - 記事ベース候補: {article_count} 件")
    print(f"  - 合計: {total_count} 件")
    print(f"  - 実行時間: {int(end_time - start_time)} 秒")
    
    if total_count > 0:
        print(f"\n📋 次のステップ:")
        print(f"  1. 情報源管理画面の「🔍 探索候補」タブを確認")
        print(f"  2. 候補を承認・保留・却下で管理")
        print(f"  3. 承認した候補が自動的に情報源リストに追加")

if __name__ == "__main__":
    main()