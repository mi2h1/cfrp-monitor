from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.parse
import jwt
import sys
import importlib.util

# ArticlesHandlerを直接定義（インポート問題を回避）
def update_ai_summary_direct(article_id, ai_summary, user_data):
    """記事のAI要約を直接データベースに保存"""
    try:
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            print("Supabase credentials not found")
            return None
        
        # 現在時刻（JST）を取得
        from datetime import datetime, timezone, timedelta
        jst = timezone(timedelta(hours=9))
        now_jst = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')
        
        # AI要約データを準備
        update_data = {
            'ai_summary': ai_summary,
            'last_edited_by': user_data['user_id'],
            'reviewed_at': now_jst
        }
        
        # データベースを更新
        url = f"{supabase_url}/rest/v1/articles?id=eq.{article_id}"
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
        
        data = json.dumps(update_data).encode('utf-8')
        
        req = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method='PATCH'
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"AI summary saved for article {article_id}")
            return result[0] if isinstance(result, list) and result else result
                
    except urllib.error.HTTPError as e:
        print(f"Update AI summary HTTP error: {e.code} - {e.reason}")
        error_body = e.read().decode('utf-8')
        print(f"Error body: {error_body}")
        return None
    except Exception as e:
        print(f"Update AI summary error: {e}")
        return None

print("Direct AI summary update function ready")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            # JWT認証チェック
            auth_header = self.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                response = {"success": False, "error": "認証が必要です"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            token = auth_header.split(' ')[1]
            try:
                jwt_secret = os.environ.get('JWT_SECRET', 'default-secret-key')
                decoded = jwt.decode(token, jwt_secret, algorithms=['HS256'])
                user_data = decoded  # ユーザー情報を保持
            except jwt.InvalidTokenError:
                response = {"success": False, "error": "無効なトークンです"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # リクエストボディを取得
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            article_id = data.get('article_id', '').strip()
            article_url = data.get('article_url', '').strip()
            
            if not article_id:
                response = {"success": False, "error": "記事IDが必要です"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
                
            if not article_url:
                response = {"success": False, "error": "記事URLが必要です"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # URLから記事内容を取得
            article_content = self.fetch_article_content(article_url)
            
            if not article_content:
                response = {"success": False, "error": "記事の内容を取得できませんでした"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # 記事本文の長さチェック（長すぎる場合は先頭部分のみ使用）
            max_length = 8000  # Gemini APIの制限を考慮
            if len(article_content) > max_length:
                article_content = article_content[:max_length] + "..."
            
            # Google Gemini APIで要約生成
            summary = self.generate_summary(article_content)
            
            if summary:
                # 要約をデータベースに保存
                try:
                    save_result = update_ai_summary_direct(article_id, summary, user_data)
                    
                    if save_result:
                        response = {
                            "success": True,
                            "summary": summary,
                            "debug_info": {
                                "extracted_content_length": len(article_content),
                                "extracted_content_preview": article_content[:500] + "..." if len(article_content) > 500 else article_content,
                                "extraction_method": "structured_html_parsing"
                            }
                        }
                    else:
                        # 要約生成は成功したが保存に失敗した場合でも、要約は返す
                        response = {
                            "success": True,
                            "summary": summary,
                            "warning": "要約の保存に失敗しましたが、要約は生成されました",
                            "debug_info": {
                                "extracted_content_length": len(article_content),
                                "extracted_content_preview": article_content[:500] + "..." if len(article_content) > 500 else article_content,
                                "extraction_method": "structured_html_parsing"
                            }
                        }
                except Exception as save_error:
                    print(f"Save error: {save_error}")
                    response = {
                        "success": True,
                        "summary": summary,
                        "warning": f"要約の保存に失敗しました: {str(save_error)}",
                        "debug_info": {
                            "extracted_content_length": len(article_content),
                            "extracted_content_preview": article_content[:500] + "..." if len(article_content) > 500 else article_content
                        }
                    }
            else:
                response = {
                    "success": False,
                    "error": "要約の生成に失敗しました"
                }
                
        except Exception as e:
            response = {
                "success": False,
                "error": f"サーバーエラー: {str(e)}"
            }
        
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def fetch_article_content(self, url):
        """URLから記事内容を取得"""
        try:
            print(f"Fetching content from URL: {url}")
            
            # User-Agentを設定してWebページを取得
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                html_content = response.read().decode('utf-8')
                
                # 構造化されたHTMLパースで記事内容を抽出
                import re
                
                # scriptタグとstyleタグを除去
                html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
                html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
                
                # 記事本文を含む可能性の高い要素を優先的に抽出
                article_selectors = [
                    # 一般的な記事コンテナのID/クラス
                    r'<div[^>]*(?:id|class)[^>]*["\'](?:[^"\']*)?content[-_]?body(?:[^"\']*)?["\'][^>]*>(.*?)</div>',
                    r'<div[^>]*(?:id|class)[^>]*["\'](?:[^"\']*)?article[-_]?content(?:[^"\']*)?["\'][^>]*>(.*?)</div>',
                    r'<div[^>]*(?:id|class)[^>]*["\'](?:[^"\']*)?post[-_]?content(?:[^"\']*)?["\'][^>]*>(.*?)</div>',
                    r'<div[^>]*(?:id|class)[^>]*["\'](?:[^"\']*)?entry[-_]?content(?:[^"\']*)?["\'][^>]*>(.*?)</div>',
                    r'<div[^>]*(?:id|class)[^>]*["\'](?:[^"\']*)?main[-_]?content(?:[^"\']*)?["\'][^>]*>(.*?)</div>',
                    r'<article[^>]*>(.*?)</article>',
                    r'<main[^>]*>(.*?)</main>',
                    # より具体的なパターン
                    r'<div[^>]*(?:id|class)[^>]*["\']content["\'][^>]*>(.*?)</div>',
                    r'<div[^>]*(?:id|class)[^>]*["\']article["\'][^>]*>(.*?)</div>',
                    r'<div[^>]*(?:id|class)[^>]*["\']post["\'][^>]*>(.*?)</div>',
                ]
                
                article_html = None
                used_selector = None
                
                # 各セレクターを試行して記事部分を抽出
                for selector in article_selectors:
                    matches = re.findall(selector, html_content, flags=re.DOTALL | re.IGNORECASE)
                    if matches:
                        # 最も長いマッチを選択（最も内容が豊富と想定）
                        article_html = max(matches, key=len)
                        used_selector = selector
                        print(f"Article content found using selector: {selector}")
                        break
                
                # 構造化された記事部分が見つからない場合は全体から抽出
                if not article_html:
                    print("No structured article content found, using full HTML")
                    article_html = html_content
                    used_selector = "full_html"
                
                # 記事HTML内のp要素を優先的に抽出
                paragraph_pattern = r'<p[^>]*>(.*?)</p>'
                paragraphs = re.findall(paragraph_pattern, article_html, flags=re.DOTALL | re.IGNORECASE)
                
                if paragraphs:
                    print(f"Found {len(paragraphs)} paragraph elements")
                    # p要素からテキストを抽出してクリーニング
                    cleaned_paragraphs = []
                    for p in paragraphs:
                        # HTMLタグを除去
                        clean_p = re.sub(r'<[^>]+>', '', p)
                        # HTMLエンティティをデコード
                        import html
                        clean_p = html.unescape(clean_p)
                        # 空白を整理
                        clean_p = re.sub(r'\s+', ' ', clean_p).strip()
                        # 意味のある長さの段落のみ保持（30文字以上）
                        if len(clean_p) > 30:
                            cleaned_paragraphs.append(clean_p)
                    
                    if cleaned_paragraphs:
                        text_content = '\n'.join(cleaned_paragraphs)
                        print(f"Extracted {len(cleaned_paragraphs)} meaningful paragraphs from p elements")
                    else:
                        # p要素に意味のある内容がない場合はフォールバック
                        text_content = re.sub(r'<[^>]+>', '', article_html)
                        import html
                        text_content = html.unescape(text_content)
                        text_content = re.sub(r'\s+', ' ', text_content).strip()
                        print("No meaningful paragraphs found in p elements, using article content")
                else:
                    print("No p elements found, extracting text from article content")
                    # HTMLタグを除去
                    text_content = re.sub(r'<[^>]+>', '', article_html)
                    # HTMLエンティティをデコード
                    import html
                    text_content = html.unescape(text_content)
                    # 複数の空白・改行を整理
                    text_content = re.sub(r'\s+', ' ', text_content).strip()
                    
                    # より良い記事抽出：長い段落を優先的に取得
                    paragraphs = text_content.split('。')  # 日本語の文で分割
                    # 50文字以上の段落のみを抽出
                    meaningful_paragraphs = [p.strip() for p in paragraphs if len(p.strip()) > 50]
                    
                    if meaningful_paragraphs:
                        # 意味のある段落を結合
                        text_content = '。'.join(meaningful_paragraphs[:20])  # 最初の20段落まで
                        if not text_content.endswith('。'):
                            text_content += '。'
                
                # 記事らしい部分を抽出（最低500文字以上あることを確認）
                if len(text_content) < 500:
                    print(f"Content too short: {len(text_content)} characters")
                    return None
                
                print(f"Successfully extracted {len(text_content)} characters using {used_selector}")
                
                # デバッグ用：最初の500文字を表示
                print(f"Content preview: {text_content[:500]}...")
                
                # デバッグ用：抽出した全文をログ出力（長い場合は分割）
                print("=== EXTRACTED ARTICLE CONTENT START ===")
                print(f"Extraction method: {used_selector}")
                if len(text_content) > 2000:
                    # 長い場合は最初と最後を表示
                    print(f"First 1000 chars: {text_content[:1000]}")
                    print("...")
                    print(f"Last 1000 chars: {text_content[-1000:]}")
                else:
                    print(text_content)
                print("=== EXTRACTED ARTICLE CONTENT END ===")
                
                return text_content
                
        except urllib.error.HTTPError as e:
            print(f"HTTP error fetching {url}: {e.code}")
            return None
        except urllib.error.URLError as e:
            print(f"URL error fetching {url}: {e}")
            return None
        except Exception as e:
            print(f"Error fetching article content: {e}")
            return None
    
    def generate_summary(self, article_text):
        """Google Gemini APIを使用して記事を要約"""
        try:
            gemini_api_key = os.environ.get('GEMINI_API_KEY')
            if not gemini_api_key:
                print("GEMINI_API_KEY環境変数が設定されていません")
                return None
            
            # Gemini API endpoint
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={gemini_api_key}"
            
            # 元のプロンプト（バックアップ）
            """
            旧プロンプト:
            以下のCFRP（炭素繊維強化プラスチック）関連の記事を、重要なポイントを押さえて200字程度で要約してください。技術的な内容や業界への影響も含めて簡潔にまとめてください。
            
            記事本文:
            {article_text}
            
            要約:
            """
            
            # YAML形式のプロンプト（実験版）
            prompt = f"""# ペルソナ設定
persona: "あなたは、炭素繊維複合材料（CFRP）を専門とする技術アナリストです。"

# タスク定義
task: "以下の記事を分析し、指定された要件に従って『要約』を生成してください。"

# 入力記事
input_article: |
  {article_text}

# 出力要件
output_requirements:
  summary:
    length: "200字程度"
    content: "技術的な新規性、応用分野、業界への影響を網羅した要点。具体的な数値や企業名、製品名があれば含める。"
    style: "簡潔で読みやすく、専門知識のない読者にも理解できる表現。"

# 出力フォーマット
output_format: "要約のみをプレーンテキストで出力してください。前置きや説明は不要です。"

# 実行
要約:"""
            
            # リクエストデータ作成
            request_data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 300,
                    "topP": 0.8,
                    "topK": 10
                }
            }
            
            # API呼び出し
            headers = {
                'Content-Type': 'application/json'
            }
            
            req_data = json.dumps(request_data).encode('utf-8')
            req = urllib.request.Request(url, data=req_data, headers=headers)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                # レスポンスから要約テキストを抽出
                if 'candidates' in result and len(result['candidates']) > 0:
                    candidate = result['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        parts = candidate['content']['parts']
                        if len(parts) > 0 and 'text' in parts[0]:
                            summary_text = parts[0]['text'].strip()
                            
                            # 「要約:」プレフィックスを削除
                            if summary_text.startswith('要約:'):
                                summary_text = summary_text[3:].strip()
                            
                            return summary_text
                
                print(f"Unexpected API response: {result}")
                return None
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"Gemini API HTTPError: {e.code} - {error_body}")
            return None
        except urllib.error.URLError as e:
            print(f"Gemini API URLError: {e}")
            return None
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return None