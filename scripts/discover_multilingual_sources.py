#!/usr/bin/env python3
"""
多言語対応の複合材料情報源発見スクリプト
日本語、ドイツ語、フランス語、中国語などの情報源を検索
"""
import os
import json
import time
import requests
import feedparser
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
from supabase import create_client, Client

# Supabase接続
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

class MultilingualSourceDiscoverer:
    def __init__(self):
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_cx = os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; MultilingualCompositeDiscoverer/1.0)'
        })
        
        # 言語別キーワード定義
        self.multilingual_keywords = {
            'japanese': {
                'basic': ['複合材料', '複合素材', 'コンポジット', '炭素繊維', 'カーボンファイバー', 'ガラス繊維', 'CFRP', 'GFRP'],
                'technical': ['プリプレグ', 'オートクレーブ', '樹脂移注成形', 'RTM', '引抜成形', 'フィラメントワインディング'],
                'applications': ['航空宇宙', '自動車', '風力発電', '船舶', '建設'],
                'organizations': ['学会', '協会', '研究所', '技術センター'],
                'media': ['ニュース', '雑誌', '業界誌', '技術誌', '工業新聞']
            },
            'german': {
                'basic': ['Verbundwerkstoff', 'Komposit', 'Faserverbund', 'Kohlenstofffaser', 'Glasfaser', 'CFK', 'GFK'],
                'technical': ['Prepreg', 'Autoklav', 'RTM', 'Pultrudieren', 'Wickeltechnik'],
                'applications': ['Luftfahrt', 'Automobil', 'Windenergie', 'Schiffbau', 'Bauwesen'],
                'organizations': ['Forschung', 'Institut', 'Verein', 'Gesellschaft'],
                'media': ['Nachrichten', 'Zeitschrift', 'Fachmagazin', 'Industrie']
            },
            'french': {
                'basic': ['matériaux composites', 'composite', 'fibre de carbone', 'fibre de verre', 'CFRP', 'GFRP'],
                'technical': ['préimprégné', 'autoclave', 'RTM', 'pultrusion', 'bobinage'],
                'applications': ['aéronautique', 'automobile', 'éolienne', 'naval', 'construction'],
                'organizations': ['recherche', 'institut', 'association', 'société'],
                'media': ['actualités', 'magazine', 'revue', 'industrie']
            },
            'chinese': {
                'basic': ['复合材料', '碳纤维', '玻璃纤维', '复合材', '碳纤', '纤维增强'],
                'technical': ['预浸料', '高压釜', '树脂传递模塑', 'RTM', '拉挤成型', '缠绕成型'],
                'applications': ['航空航天', '汽车', '风力发电', '船舶', '建筑'],
                'organizations': ['学会', '协会', '研究所', '技术中心'],
                'media': ['新闻', '杂志', '期刊', '工业']
            },
            'korean': {
                'basic': ['복합재료', '탄소섬유', '유리섬유', '복합소재', 'CFRP', 'GFRP'],
                'technical': ['프리프레그', '오토클레이브', 'RTM', '인발성형', '필라멘트와인딩'],
                'applications': ['항공우주', '자동차', '풍력발전', '조선', '건설'],
                'organizations': ['학회', '협회', '연구소', '기술센터'],
                'media': ['뉴스', '잡지', '기술지', '산업']
            }
        }
        
        # 言語別ドメイン傾向
        self.language_domains = {
            'japanese': ['.jp', '.co.jp', '.or.jp', '.ac.jp'],
            'german': ['.de', '.at', '.ch'],
            'french': ['.fr', '.be', '.ch'],
            'chinese': ['.cn', '.com.cn', '.edu.cn'],
            'korean': ['.kr', '.co.kr'],
            'italian': ['.it'],
            'spanish': ['.es'],
            'russian': ['.ru']
        }
        
    def search_multilingual(self, language: str, query_type: str = 'basic') -> List[Dict]:
        """指定言語での複合材料情報源を検索"""
        if language not in self.multilingual_keywords:
            print(f"サポートされていない言語: {language}")
            return []
            
        keywords = self.multilingual_keywords[language].get(query_type, [])
        if not keywords:
            return []
            
        # 検索クエリ構築
        queries = []
        
        if language == 'japanese':
            queries = [
                f'"{keywords[0]}" OR "{keywords[1]}" ニュース RSS site:.jp',
                f'"{keywords[2]}" OR "{keywords[3]}" 学会 RSS',
                f'"炭素繊維" OR "カーボンファイバー" 業界 RSS',
                f'複合材料 協会 OR 学会 RSS'
            ]
        elif language == 'german':
            queries = [
                f'"{keywords[0]}" OR "{keywords[1]}" Nachrichten RSS site:.de',
                f'"Faserverbund" Forschung RSS',
                f'"Kohlenstofffaser" Industrie RSS'
            ]
        elif language == 'french':
            queries = [
                f'"{keywords[0]}" actualités RSS site:.fr',
                f'"fibre de carbone" industrie RSS',
                f'composite aéronautique RSS'
            ]
        elif language == 'chinese':
            queries = [
                f'"{keywords[0]}" 新闻 RSS site:.cn',
                f'"碳纤维" 行业 RSS',
                f'复合材料 学会 RSS'
            ]
        elif language == 'korean':
            queries = [
                f'"{keywords[0]}" 뉴스 RSS site:.kr',
                f'"탄소섬유" 산업 RSS',
                f'복합재료 학회 RSS'
            ]
        
        all_results = []
        for query in queries:
            print(f"\n検索中 ({language}): {query}")
            results = self.search_google(query, num_results=5)
            all_results.extend(results)
            time.sleep(2)  # API制限対策
            
        return all_results
    
    def search_google(self, query: str, num_results: int = 5) -> List[Dict]:
        """Google検索実行"""
        if not self.google_api_key or not self.google_cx:
            return []
            
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': self.google_api_key,
            'cx': self.google_cx,
            'q': query,
            'num': num_results
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('items', [])
        except Exception as e:
            print(f"Google検索エラー: {e}")
            return []
    
    def detect_language_from_domain(self, url: str) -> str:
        """ドメインから言語を推定"""
        domain = urlparse(url).netloc.lower()
        
        for language, domains in self.language_domains.items():
            if any(domain.endswith(d) for d in domains):
                return language
                
        return 'english'  # デフォルト
    
    def evaluate_multilingual_relevance(self, url: str, title: str, snippet: str, language: str) -> float:
        """言語別の関連度評価"""
        score = 0.0
        text = f"{title} {snippet} {url}".lower()
        
        if language not in self.multilingual_keywords:
            return 0.0
            
        # 各カテゴリのキーワードでスコアリング
        for category, keywords in self.multilingual_keywords[language].items():
            category_score = 0.2 if category == 'basic' else 0.1
            for keyword in keywords:
                if keyword.lower() in text:
                    score += category_score
                    
        # ドメインの言語一致ボーナス
        detected_lang = self.detect_language_from_domain(url)
        if detected_lang == language:
            score += 0.3
            
        return min(score, 1.0)
    
    def find_rss_feeds(self, url: str) -> List[str]:
        """RSSフィード検出（多言語対応）"""
        feeds = []
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # エンコーディング自動検出
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # RSSリンク検出
            rss_links = soup.find_all('link', type=['application/rss+xml', 'application/atom+xml'])
            for link in rss_links:
                href = link.get('href')
                if href:
                    feed_url = urljoin(url, href)
                    feeds.append(feed_url)
            
            # 言語別の一般的なRSSパス
            common_paths = ['/rss', '/feed', '/rss.xml', '/feed.xml', '/atom.xml']
            
            # 日本語サイト特有のパス
            if self.detect_language_from_domain(url) == 'japanese':
                common_paths.extend(['/news/rss', '/info/rss', '/topics/rss'])
            
            for path in common_paths:
                feed_url = urljoin(url, path)
                if self.validate_feed(feed_url):
                    feeds.append(feed_url)
                    
        except Exception as e:
            print(f"RSS検出エラー ({url}): {e}")
            
        return list(set(feeds))
    
    def validate_feed(self, feed_url: str) -> bool:
        """フィード有効性確認"""
        try:
            response = self.session.get(feed_url, timeout=10)
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                return len(feed.entries) > 0
        except:
            pass
        return False
    
    def discover_multilingual_sources(self):
        """多言語の複合材料情報源を発見"""
        target_languages = ['japanese', 'german', 'chinese', 'korean']  # 優先言語
        
        all_discovered = {}
        
        for language in target_languages:
            print(f"\n{'='*50}")
            print(f"🌍 {language.upper()} 情報源の検索開始")
            print(f"{'='*50}")
            
            # 基本検索
            results = self.search_multilingual(language, 'basic')
            
            language_sources = []
            for result in results:
                site_url = result.get('link', '')
                title = result.get('title', '')
                snippet = result.get('snippet', '')
                
                # 関連度評価
                relevance = self.evaluate_multilingual_relevance(site_url, title, snippet, language)
                if relevance < 0.3:
                    continue
                    
                print(f"\n調査中: {title}")
                print(f"URL: {site_url}")
                print(f"関連度: {relevance:.2f}")
                
                # RSSフィード検出
                feeds = self.find_rss_feeds(site_url)
                
                for feed_url in feeds:
                    source = {
                        'name': title or urlparse(site_url).netloc,
                        'urls': [feed_url],
                        'site_url': site_url,
                        'language': language,
                        'relevance_score': relevance,
                        'discovered_at': datetime.now().isoformat()
                    }
                    language_sources.append(source)
                    print(f"  → RSSフィード発見: {feed_url}")
            
            all_discovered[language] = language_sources
            print(f"\n{language}: {len(language_sources)} 件の情報源を発見")
        
        return all_discovered
    
    def save_multilingual_candidates(self, sources_by_language: Dict[str, List[Dict]]):
        """多言語候補をDBに保存"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        total_db_saved = 0
        
        for language, sources in sources_by_language.items():
            if not sources:
                continue
                
            # JSONファイルへの保存（バックアップ用）
            filename = f"multilingual_sources_{language}_{timestamp}.json"
            filepath = os.path.join(os.path.dirname(__file__), '..', filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(sources, f, ensure_ascii=False, indent=2)
                
            # データベースへの保存
            db_saved = 0
            for source in sources:
                try:
                    # 候補データを変換
                    candidate_data = {
                        'name': source.get('name', 'Unknown'),
                        'domain': self.extract_domain(source.get('site_url', '')),
                        'urls': source.get('urls', []),
                        'site_url': source.get('site_url', ''),
                        'category': 'unknown',
                        'language': language,
                        'country_code': self.detect_country_from_language(language),
                        'relevance_score': source.get('relevance_score', 0.5),
                        'discovery_method': 'weekly_multilingual_discovery',
                        'metadata': {
                            'discovered_at': source.get('discovered_at', ''),
                            'source_type': 'multilingual_search',
                            'search_language': language,
                            'feeds_found': len(source.get('urls', []))
                        }
                    }
                    
                    # 重複チェック（ドメインでUPSERT）
                    existing = supabase.table('source_candidates').select('id').eq('domain', candidate_data['domain']).execute()
                    
                    if existing.data:
                        # 既存候補を更新
                        result = supabase.table('source_candidates').update({
                            'relevance_score': candidate_data['relevance_score'],
                            'metadata': candidate_data['metadata']
                        }).eq('domain', candidate_data['domain']).execute()
                        print(f"  更新: {candidate_data['name']} ({candidate_data['domain']})")
                    else:
                        # 新規候補を挿入
                        result = supabase.table('source_candidates').insert(candidate_data).execute()
                        print(f"  追加: {candidate_data['name']} ({candidate_data['domain']})")
                        db_saved += 1
                        
                except Exception as e:
                    print(f"  エラー: {source.get('name', 'Unknown')} - {str(e)}")
                    
            print(f"\n{language}: {len(sources)} 件の候補を発見 → {filename}")
            print(f"  - データベース保存: {db_saved} 件")
            total_db_saved += db_saved
        
        # 統計情報
        total_sources = sum(len(sources) for sources in sources_by_language.values())
        print(f"\n総計: {total_sources} 件の多言語情報源候補を発見")
        print(f"  - データベース保存: {total_db_saved} 件")
        print(f"  - 管理画面で確認・承認してください")
        
        print("\n言語別内訳:")
        for language, sources in sources_by_language.items():
            if sources:
                print(f"  {language}: {len(sources)} 件")
                
    def extract_domain(self, url: str) -> str:
        """URLからドメインを抽出"""
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            return parsed.netloc or url
        except:
            return url
            
    def detect_country_from_language(self, language: str) -> str:
        """言語から国コードを推定"""
        mapping = {
            'japanese': 'JP',
            'german': 'DE',
            'french': 'FR',
            'chinese': 'CN',
            'korean': 'KR',
            'italian': 'IT',
            'spanish': 'ES',
            'russian': 'RU'
        }
        return mapping.get(language, 'unknown')

def main():
    # ログ記録用の変数初期化
    start_time = time.time()
    log_data = {
        "task_name": "Weekly Multilingual Source Discovery",
        "task_type": "weekly_multilingual_discovery",
        "sources_processed": 0,
        "articles_found": 0,
        "articles_added": 0,
        "errors_count": 0,
        "details": {
            "languages_searched": [],
            "search_queries": 0,
            "api_calls": 0,
            "relevant_sites": 0,
            "sites_with_rss": 0,
            "candidates_by_language": {},
            "errors": []
        }
    }
    
    try:
        discoverer = MultilingualSourceDiscoverer()
        
        if not discoverer.google_api_key:
            error_msg = "Google API認証情報が設定されていません"
            log_data["errors_count"] += 1
            log_data["details"]["errors"].append(error_msg)
            print(f"警告: {error_msg}")
            print("多言語検索にはGoogle Custom Search APIが必要です")
            return
        
        print("多言語複合材料情報源の検索を開始します...")
        print("対象言語: 日本語、ドイツ語、中国語、韓国語")
        
        sources = discoverer.discover_multilingual_sources()
        discoverer.save_multilingual_candidates(sources)
        
        # ログデータを更新
        total_candidates = sum(len(lang_sources) for lang_sources in sources.values())
        log_data["articles_added"] = total_candidates
        log_data["details"]["languages_searched"] = list(sources.keys())
        log_data["details"]["candidates_by_language"] = {lang: len(sources_list) for lang, sources_list in sources.items()}
        
    except Exception as e:
        log_data["errors_count"] += 1
        log_data["details"]["errors"].append(str(e))
        print(f"エラー: {e}")
        
    finally:
        # 実行時間を計算
        end_time = time.time()
        log_data["duration_seconds"] = int(end_time - start_time)
        log_data["status"] = "failed" if log_data["errors_count"] > 0 else "success"
        
        # detailsをJSON文字列に変換
        log_data["details"] = json.dumps(log_data["details"], ensure_ascii=False)
        
        # task_logsテーブルに記録
        try:
            log_result = supabase.table("task_logs").insert(log_data).execute()
            if hasattr(log_result, "error") and log_result.error:
                print(f"ログ記録エラー: {log_result.error}")
            else:
                print(f"実行ログ記録完了: {log_data['task_name']}")
                print(f"  - 発見候補数: {log_data['articles_added']}")
                print(f"  - 実行時間: {log_data['duration_seconds']}秒")
                print(f"  - ステータス: {log_data['status']}")
        except Exception as e:
            print(f"ログ記録エラー: {e}")

if __name__ == "__main__":
    main()