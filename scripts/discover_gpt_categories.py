#!/usr/bin/env python3
"""
GPT提供の情報源カテゴリに基づく自動探索
新しく追加されたカテゴリの類似情報源を発見
"""
import os
import json
import requests
from datetime import datetime
from typing import List, Dict
from bs4 import BeautifulSoup
import time
import random

class GPTCategoryDiscoverer:
    def __init__(self):
        self.categories = {
            # 日本の炭素繊維・複合材料メーカー
            'japanese_carbon_fiber': {
                'keywords': ['炭素繊維', 'カーボンファイバー', 'CFRP', '複合材料', 'コンポジット'],
                'domains': ['toray.com', 'teijin.com', 'mitsubishichemical.com'],
                'search_terms': [
                    '炭素繊維メーカー 日本',
                    'carbon fiber manufacturers Japan',
                    'CFRP 日本企業',
                    '複合材料 メーカー'
                ]
            },
            
            # 欧州の化学・材料メーカー
            'european_materials': {
                'keywords': ['composite materials', 'carbon fiber', 'advanced materials', 'prepreg'],
                'domains': ['solvay.com', 'sglcarbon.com', 'hexcel.com'],
                'search_terms': [
                    'composite materials manufacturers Europe',
                    'carbon fiber companies Germany France',
                    'advanced materials Europe',
                    'prepreg manufacturers'
                ]
            },
            
            # 日本の産業専門メディア
            'japanese_industry_media': {
                'keywords': ['製造業', '化学工業', '材料', '技術', 'ニュース'],
                'domains': ['nikkan.co.jp', 'chemicaldaily.co.jp', 'kogyo.co.jp'],
                'search_terms': [
                    '製造業 専門紙',
                    '化学工業 ニュース',
                    '材料産業 メディア',
                    '技術情報 日本'
                ]
            },
            
            # 複合材料業界メディア・プラットフォーム
            'composites_industry_media': {
                'keywords': ['composites', 'reinforced plastics', 'fiber reinforced', 'industry news'],
                'domains': ['jeccomposites.com', 'compositesworld.com', 'reinforcedplastics.com'],
                'search_terms': [
                    'composites industry news',
                    'fiber reinforced plastics media',
                    'composite materials publications',
                    'advanced materials magazines'
                ]
            },
            
            # 中国の複合材料メーカー・メディア
            'chinese_composites': {
                'keywords': ['复合材料', '碳纤维', '玻璃纤维', '先进材料', '复材'],
                'domains': ['chinacompositesexpo.com', 'composite.cn'],
                'search_terms': [
                    '复合材料 制造商 中国',
                    '碳纤维 企业',
                    'China composites manufacturers',
                    '复合材料 新闻网站',
                    '先进材料 中国'
                ]
            },
            
            # 韓国の炭素繊維・先進材料企業
            'korean_advanced_materials': {
                'keywords': ['탄소섬유', '복합재료', '첨단소재', 'carbon fiber', 'advanced materials'],
                'domains': ['hyosung.com', 'kctech.re.kr', 'kolon.com'],
                'search_terms': [
                    '탄소섬유 제조업체 한국',
                    'Korea carbon fiber companies',
                    '첨단소재 기업',
                    '복합재료 한국',
                    'advanced materials Korea'
                ]
            }
        }
        
        self.discovered_sources = []
        
    def search_category_sources(self, category_name: str, category_data: Dict) -> List[Dict]:
        """カテゴリ別の情報源探索"""
        print(f"🔍 {category_name} カテゴリを探索中...")
        
        category_sources = []
        
        for search_term in category_data['search_terms']:
            print(f"  検索: {search_term}")
            
            # Google検索のシミュレーション（実際はAPIやスクレイピング）
            sources = self.simulate_search(search_term, category_data['keywords'])
            category_sources.extend(sources)
            
            # レート制限
            time.sleep(random.uniform(1, 3))
        
        return category_sources
    
    def simulate_search(self, search_term: str, keywords: List[str]) -> List[Dict]:
        """検索結果のシミュレーション（実環境では実際の検索API使用）"""
        # 実際の実装では Google Custom Search API や Bing Search API を使用
        simulated_results = []
        
        # 例: 日本の炭素繊維メーカー検索結果
        if '炭素繊維' in search_term or 'carbon fiber' in search_term:
            simulated_results = [
                {
                    'name': 'Kureha Corporation',
                    'domain': 'kureha.co.jp',
                    'url': 'https://www.kureha.co.jp',
                    'category': 'manufacturer',
                    'country': 'JP',
                    'description': '炭素繊維・複合材料メーカー',
                    'keywords_found': ['炭素繊維', '複合材料'],
                    'relevance_score': 0.85
                },
                {
                    'name': 'Nippon Graphite Fiber',
                    'domain': 'ngf-carbon.com',
                    'url': 'https://www.ngf-carbon.com',
                    'category': 'manufacturer',
                    'country': 'JP',
                    'description': '炭素繊維専門メーカー',
                    'keywords_found': ['carbon fiber'],
                    'relevance_score': 0.90
                }
            ]
        
        # 欧州材料メーカー
        elif 'Europe' in search_term and 'materials' in search_term:
            simulated_results = [
                {
                    'name': 'Cytec Solvay Group',
                    'domain': 'cytec.com',
                    'url': 'https://www.cytec.com',
                    'category': 'manufacturer',
                    'country': 'BE',
                    'description': 'Advanced composite materials',
                    'keywords_found': ['composite materials', 'prepreg'],
                    'relevance_score': 0.88
                },
                {
                    'name': 'Owens Corning',
                    'domain': 'owenscorning.com',
                    'url': 'https://www.owenscorning.com',
                    'category': 'manufacturer',
                    'country': 'US',
                    'description': 'Fiberglass and composite materials',
                    'keywords_found': ['composite materials', 'fiber reinforced'],
                    'relevance_score': 0.82
                }
            ]
        
        # 日本の産業メディア
        elif '製造業' in search_term or '専門紙' in search_term:
            simulated_results = [
                {
                    'name': 'Kogyo Newspaper',
                    'domain': 'kogyo.co.jp',
                    'url': 'https://www.kogyo.co.jp',
                    'category': 'media',
                    'country': 'JP',
                    'description': '工業専門新聞',
                    'keywords_found': ['製造業', '技術'],
                    'relevance_score': 0.75
                },
                {
                    'name': 'Tech-On!',
                    'domain': 'techon.nikkeibp.co.jp',
                    'url': 'https://techon.nikkeibp.co.jp',
                    'category': 'media',
                    'country': 'JP',
                    'description': '技術情報サイト',
                    'keywords_found': ['技術', '材料'],
                    'relevance_score': 0.80
                }
            ]
        
        # 中国の複合材料
        elif '复合材料' in search_term or ('China' in search_term and 'composites' in search_term):
            simulated_results = [
                {
                    'name': 'China Composite Materials',
                    'domain': 'composite.com.cn',
                    'url': 'https://www.composite.com.cn',
                    'category': 'media',
                    'country': 'CN',
                    'description': '中国复合材料专业网站',
                    'keywords_found': ['复合材料', '碳纤维'],
                    'relevance_score': 0.85
                },
                {
                    'name': 'Weihai Guangwei Composites',
                    'domain': 'gwcompos.com',
                    'url': 'https://www.gwcompos.com',
                    'category': 'manufacturer',
                    'country': 'CN',
                    'description': '威海光威复合材料',
                    'keywords_found': ['复合材料', '碳纤维'],
                    'relevance_score': 0.88
                }
            ]
        
        # 韓国の先進材料
        elif '탄소섬유' in search_term or ('Korea' in search_term and 'materials' in search_term):
            simulated_results = [
                {
                    'name': 'Kolon Industries',
                    'domain': 'kolon.com',
                    'url': 'https://www.kolon.com',
                    'category': 'manufacturer',
                    'country': 'KR',
                    'description': '코오롱 첨단소재',
                    'keywords_found': ['첨단소재', '복합재료'],
                    'relevance_score': 0.82
                },
                {
                    'name': 'Taekwang Industrial',
                    'domain': 'tkic.co.kr',
                    'url': 'https://www.tkic.co.kr',
                    'category': 'manufacturer',
                    'country': 'KR',
                    'description': '태광산업 탄소섬유',
                    'keywords_found': ['탄소섬유'],
                    'relevance_score': 0.80
                }
            ]
        
        return simulated_results
    
    def check_rss_availability(self, domain: str) -> str:
        """RSS/フィード可用性チェック"""
        common_rss_paths = [
            '/rss.xml', '/feed.xml', '/rss/', '/feed/', 
            '/news/rss.xml', '/press/rss.xml', '/blog/rss.xml'
        ]
        
        for path in common_rss_paths:
            try:
                url = f"https://{domain}{path}"
                response = requests.head(url, timeout=10)
                if response.status_code == 200:
                    return url
            except:
                continue
        
        return None
    
    def evaluate_source_quality(self, source: Dict) -> Dict:
        """情報源の品質評価"""
        score = 0
        reasons = []
        
        # 関連度スコア
        relevance = source.get('relevance_score', 0)
        if relevance >= 0.8:
            score += 30
            reasons.append(f"高い関連度 ({relevance:.2f})")
        elif relevance >= 0.6:
            score += 20
            reasons.append(f"中程度の関連度 ({relevance:.2f})")
        
        # ドメイン信頼性
        domain = source.get('domain', '')
        if domain.endswith(('.edu', '.org', '.gov')):
            score += 25
            reasons.append("信頼できるドメイン")
        elif domain.endswith('.co.jp'):
            score += 15
            reasons.append("日本企業ドメイン")
        elif domain.endswith('.com'):
            score += 10
            reasons.append("企業ドメイン")
        
        # カテゴリ価値
        category = source.get('category', '')
        if category == 'manufacturer':
            score += 20
            reasons.append("メーカー情報源")
        elif category == 'media':
            score += 15
            reasons.append("メディア情報源")
        
        # RSS可用性
        rss_url = self.check_rss_availability(source.get('domain', ''))
        if rss_url:
            score += 15
            reasons.append("RSSフィード利用可能")
            source['rss_url'] = rss_url
        
        # 国・地域の価値
        country = source.get('country', '')
        if country in ['JP', 'DE', 'FR', 'BE']:
            score += 10
            reasons.append(f"重要地域 ({country})")
        elif country in ['CN', 'KR']:
            score += 8
            reasons.append(f"アジア重要地域 ({country})")
        
        return {
            'score': score,
            'reasons': reasons,
            'approved': score >= 60,
            'review_required': 40 <= score < 60
        }
    
    def discover_all_categories(self) -> Dict:
        """全カテゴリの探索実行"""
        print("🚀 GPTカテゴリベース情報源探索開始")
        print("=" * 50)
        
        all_discovered = {}
        
        for category_name, category_data in self.categories.items():
            category_sources = self.search_category_sources(category_name, category_data)
            
            # 品質評価
            evaluated_sources = []
            for source in category_sources:
                evaluation = self.evaluate_source_quality(source)
                source['evaluation'] = evaluation
                evaluated_sources.append(source)
            
            all_discovered[category_name] = evaluated_sources
            print(f"  ✓ {category_name}: {len(evaluated_sources)} 個発見")
        
        return all_discovered
    
    def generate_report(self, discovered_sources: Dict):
        """探索結果レポート生成"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"gpt_category_discovery_report_{timestamp}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# GPTカテゴリベース情報源探索レポート\n\n")
            f.write(f"**実行日時:** {datetime.now().isoformat()}\n\n")
            
            total_sources = sum(len(sources) for sources in discovered_sources.values())
            f.write(f"## 📊 概要\n\n")
            f.write(f"- **探索カテゴリ数:** {len(discovered_sources)}\n")
            f.write(f"- **発見情報源総数:** {total_sources}\n\n")
            
            for category_name, sources in discovered_sources.items():
                f.write(f"## 📂 {category_name}\n\n")
                
                approved = [s for s in sources if s['evaluation']['approved']]
                review = [s for s in sources if s['evaluation']['review_required']]
                
                f.write(f"- ✅ 自動承認候補: {len(approved)}\n")
                f.write(f"- 🔍 手動レビュー候補: {len(review)}\n\n")
                
                if approved:
                    f.write("### ✅ 自動承認候補\n\n")
                    for source in approved:
                        f.write(f"#### {source['name']}\n")
                        f.write(f"- **ドメイン:** {source['domain']}\n")
                        f.write(f"- **国:** {source['country']}\n")
                        f.write(f"- **スコア:** {source['evaluation']['score']}\n")
                        f.write(f"- **RSS:** {source.get('rss_url', 'なし')}\n")
                        f.write(f"- **説明:** {source['description']}\n\n")
        
        print(f"📄 レポート生成: {report_file}")
        
        # 候補SQLファイルも生成
        self.generate_candidate_sql(discovered_sources, timestamp)
    
    def generate_candidate_sql(self, discovered_sources: Dict, timestamp: str):
        """候補情報源のSQL生成"""
        sql_file = f"gpt_discovered_sources_{timestamp}.sql"
        
        with open(sql_file, 'w', encoding='utf-8') as f:
            f.write("-- GPTカテゴリ探索で発見された情報源\n")
            f.write("-- 自動承認候補のみ\n\n")
            
            for category_name, sources in discovered_sources.items():
                approved = [s for s in sources if s['evaluation']['approved']]
                
                if approved:
                    f.write(f"-- {category_name} カテゴリ\n")
                    for source in approved:
                        rss_url = source.get('rss_url', f"https://{source['domain']}/rss.xml")
                        f.write(f"""
INSERT INTO sources (name, urls, parser, acquisition_mode, category, domain, country_code, relevance)
VALUES (
    '{source['name']}',
    ARRAY['{rss_url}'],
    'rss',
    'auto',
    '{source['category']}',
    '{source['domain']}',
    '{source['country']}',
    {min(10, max(1, source['evaluation']['score'] // 10))}
);
""")
        
        print(f"💾 SQL候補ファイル生成: {sql_file}")

def main():
    discoverer = GPTCategoryDiscoverer()
    
    print("🔍 GPTカテゴリベース情報源探索システム")
    print("新しく追加されたカテゴリの類似情報源を探索します")
    print()
    
    # 全カテゴリ探索実行
    discovered = discoverer.discover_all_categories()
    
    # レポート生成
    discoverer.generate_report(discovered)
    
    # 統計出力
    total_approved = sum(
        len([s for s in sources if s['evaluation']['approved']]) 
        for sources in discovered.values()
    )
    
    print(f"\n🎯 探索完了!")
    print(f"自動承認候補: {total_approved} 個")
    print("レポートとSQLファイルを確認してください。")

if __name__ == "__main__":
    main()