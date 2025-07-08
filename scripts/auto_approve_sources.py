#!/usr/bin/env python3
"""
高品質な情報源候補を自動承認するスクリプト
品質スコアと検証結果に基づいて自動でSourcesテーブルに追加
"""
import os
import json
import glob
from datetime import datetime
from typing import List, Dict
from supabase import create_client, Client

# Supabase接続
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

class SourceAutoApprover:
    def __init__(self):
        self.approval_criteria = {
            'min_relevance_score': 0.7,      # 関連度スコア最低値
            'min_occurrence_count': 5,        # 最低出現回数（記事分析由来）
            'required_feed_validation': True,  # フィード検証必須
            'blocked_domains': [              # ブロックドメイン
                'spam.com', 'fake-news.com', 'low-quality.net'
            ],
            'trusted_domains': [              # 信頼できるドメイン
                'arxiv.org', 'mdpi.com', 'acmanet.org', 
                'sampe.org', 'avk-tv.de', 'manufacturing.net'
            ]
        }
        
    def load_candidate_files(self) -> List[Dict]:
        """候補ファイルを読み込み"""
        candidates = []
        
        # 候補ファイルのパターン
        patterns = [
            '*_candidates_*.json',
            '*_source_candidates_*.json', 
            'article_source_candidates_*.json',
            'multilingual_sources_*.json'
        ]
        
        for pattern in patterns:
            files = glob.glob(pattern)
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for item in data:
                                item['source_file'] = file_path
                                candidates.append(item)
                        else:
                            print(f"警告: {file_path} は期待される形式ではありません")
                except Exception as e:
                    print(f"ファイル読み込みエラー {file_path}: {e}")
        
        return candidates
    
    def evaluate_source_quality(self, candidate: Dict) -> Dict:
        """情報源の品質を評価"""
        score = 0
        reasons = []
        
        # 1. 関連度スコア評価
        relevance = candidate.get('relevance_score', 0)
        if relevance >= 0.8:
            score += 30
            reasons.append(f"高い関連度スコア ({relevance:.2f})")
        elif relevance >= 0.6:
            score += 20
            reasons.append(f"中程度の関連度スコア ({relevance:.2f})")
        elif relevance >= 0.4:
            score += 10
            reasons.append(f"低い関連度スコア ({relevance:.2f})")
        
        # 2. ドメイン信頼性
        urls = candidate.get('urls', [])
        if urls:
            domain = urls[0].split('/')[2] if len(urls[0].split('/')) > 2 else ''
            
            if any(trusted in domain for trusted in self.approval_criteria['trusted_domains']):
                score += 25
                reasons.append(f"信頼できるドメイン ({domain})")
            elif any(blocked in domain for blocked in self.approval_criteria['blocked_domains']):
                score -= 50
                reasons.append(f"ブロックされたドメイン ({domain})")
        
        # 3. 出現回数（記事分析由来の場合）
        occurrence = candidate.get('occurrence_count', 0)
        if occurrence >= 10:
            score += 20
            reasons.append(f"高い出現回数 ({occurrence}回)")
        elif occurrence >= 5:
            score += 10
            reasons.append(f"中程度の出現回数 ({occurrence}回)")
        
        # 4. フィード検証済み
        if candidate.get('feed_url') and candidate.get('feed_validated', False):
            score += 15
            reasons.append("RSS フィード検証済み")
        
        # 5. 言語・地域の多様性
        language = candidate.get('language', 'english')
        if language in ['chinese', 'german', 'japanese']:
            score += 10
            reasons.append(f"多言語対応 ({language})")
        
        # 6. カテゴリの価値
        category = candidate.get('category', '')
        if category in ['research', 'industry_news']:
            score += 5
            reasons.append(f"価値の高いカテゴリ ({category})")
        
        return {
            'score': score,
            'reasons': reasons,
            'approved': score >= 70,  # 70点以上で自動承認
            'review_required': 40 <= score < 70  # 40-69点は手動レビュー
        }
    
    def get_existing_sources(self) -> set:
        """既存のソースURLを取得"""
        try:
            result = supabase.table('sources').select('urls').execute()
            existing_urls = set()
            for source in result.data:
                if source.get('urls'):
                    existing_urls.update(source['urls'])
            return existing_urls
        except Exception as e:
            print(f"既存ソース取得エラー: {e}")
            return set()
    
    def auto_approve_sources(self, dry_run: bool = False):
        """自動承認プロセスを実行"""
        candidates = self.load_candidate_files()
        existing_urls = self.get_existing_sources()
        
        print(f"📋 {len(candidates)} 個の候補を評価中...")
        
        approved_sources = []
        review_required = []
        rejected_sources = []
        
        for candidate in candidates:
            # 既存チェック
            candidate_urls = candidate.get('urls', [])
            if not candidate_urls or any(url in existing_urls for url in candidate_urls):
                continue
            
            # 品質評価
            evaluation = self.evaluate_source_quality(candidate)
            candidate['evaluation'] = evaluation
            
            if evaluation['approved']:
                approved_sources.append(candidate)
            elif evaluation['review_required']:
                review_required.append(candidate)
            else:
                rejected_sources.append(candidate)
        
        # 結果出力
        print(f"\n📊 評価結果:")
        print(f"✅ 自動承認: {len(approved_sources)} 件")
        print(f"🔍 手動レビュー必要: {len(review_required)} 件")
        print(f"❌ 却下: {len(rejected_sources)} 件")
        
        # 自動承認された情報源をデータベースに追加
        if approved_sources and not dry_run:
            print(f"\n🤖 自動承認された情報源を追加中...")
            for source in approved_sources:
                try:
                    # ドメイン抽出
                    urls = source.get('urls', [])
                    domain = None
                    if urls and len(urls) > 0:
                        try:
                            domain = urls[0].split('/')[2]
                        except:
                            domain = 'unknown.com'
                    
                    new_source = {
                        'name': source.get('name', 'Unknown Source'),
                        'urls': urls,
                        'parser': 'rss',
                        'acquisition_mode': 'auto',
                        'category': source.get('category', 'news'),
                        'domain': domain,
                        'country_code': source.get('country_code', 'US'),
                        'relevance': min(10, max(1, source.get('evaluation', {}).get('score', 50) // 10))  # 1-10の範囲
                    }
                    
                    result = supabase.table('sources').insert(new_source).execute()
                    print(f"  ✓ 追加完了: {new_source['name']}")
                    
                except Exception as e:
                    print(f"  ✗ 追加エラー: {source.get('name', 'Unknown')} - {e}")
        
        # 結果レポート生成
        self.generate_approval_report(approved_sources, review_required, rejected_sources, dry_run)
        
        return {
            'approved': len(approved_sources),
            'review_required': len(review_required), 
            'rejected': len(rejected_sources)
        }
    
    def generate_approval_report(self, approved: List[Dict], review: List[Dict], rejected: List[Dict], dry_run: bool):
        """承認結果レポートを生成"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"source_approval_report_{timestamp}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# 情報源自動承認レポート\n\n")
            f.write(f"**実行日時:** {datetime.now().isoformat()}\n")
            f.write(f"**モード:** {'ドライラン' if dry_run else '実際の追加'}\n\n")
            
            f.write(f"## 📊 概要\n\n")
            f.write(f"- ✅ 自動承認: {len(approved)} 件\n")
            f.write(f"- 🔍 手動レビュー必要: {len(review)} 件\n")
            f.write(f"- ❌ 却下: {len(rejected)} 件\n\n")
            
            if approved:
                f.write(f"## ✅ 自動承認された情報源\n\n")
                for source in approved:
                    eval_data = source.get('evaluation', {})
                    f.write(f"### {source.get('name', 'Unknown')}\n")
                    f.write(f"- **URL:** {source.get('urls', ['N/A'])[0]}\n")
                    f.write(f"- **スコア:** {eval_data.get('score', 0)}\n")
                    f.write(f"- **理由:** {', '.join(eval_data.get('reasons', []))}\n\n")
            
            if review:
                f.write(f"## 🔍 手動レビューが必要な情報源\n\n")
                for source in review:
                    eval_data = source.get('evaluation', {})
                    f.write(f"### {source.get('name', 'Unknown')}\n")
                    f.write(f"- **URL:** {source.get('urls', ['N/A'])[0]}\n")
                    f.write(f"- **スコア:** {eval_data.get('score', 0)}\n")
                    f.write(f"- **理由:** {', '.join(eval_data.get('reasons', []))}\n\n")
        
        print(f"📄 レポート生成完了: {report_file}")

def main():
    approver = SourceAutoApprover()
    
    # 環境変数チェック
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        print("エラー: SUPABASE_URL と SUPABASE_KEY 環境変数を設定してください")
        return
    
    # 実行モード確認
    dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
    
    print("🤖 情報源自動承認システム開始")
    print(f"📋 モード: {'ドライラン' if dry_run else '実際の追加'}")
    
    results = approver.auto_approve_sources(dry_run=dry_run)
    
    print(f"\n🎯 完了: {results['approved']} 件承認, {results['review_required']} 件要レビュー")

if __name__ == "__main__":
    main()