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
            article_text = data.get('article_text', '').strip()
            
            if not article_id:
                response = {"success": False, "error": "記事IDが必要です"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
                
            if not article_text:
                response = {"success": False, "error": "記事本文が必要です"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # 記事本文の長さチェック（長すぎる場合は先頭部分のみ使用）
            max_length = 8000  # Gemini APIの制限を考慮
            if len(article_text) > max_length:
                article_text = article_text[:max_length] + "..."
            
            # Google Gemini APIで要約生成
            summary = self.generate_summary(article_text)
            
            if summary:
                # 要約をデータベースに保存
                try:
                    save_result = update_ai_summary_direct(article_id, summary, user_data)
                    
                    if save_result:
                        response = {
                            "success": True,
                            "summary": summary
                        }
                    else:
                        # 要約生成は成功したが保存に失敗した場合でも、要約は返す
                        response = {
                            "success": True,
                            "summary": summary,
                            "warning": "要約の保存に失敗しましたが、要約は生成されました"
                        }
                except Exception as save_error:
                    print(f"Save error: {save_error}")
                    response = {
                        "success": True,
                        "summary": summary,
                        "warning": f"要約の保存に失敗しました: {str(save_error)}"
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
    
    def generate_summary(self, article_text):
        """Google Gemini APIを使用して記事を要約"""
        try:
            gemini_api_key = os.environ.get('GEMINI_API_KEY')
            if not gemini_api_key:
                print("GEMINI_API_KEY環境変数が設定されていません")
                return None
            
            # Gemini API endpoint
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={gemini_api_key}"
            
            # プロンプト作成（日本語で要約指示）
            prompt = f"""以下のCFRP（炭素繊維強化プラスチック）関連の記事を、重要なポイントを押さえて200字程度で要約してください。技術的な内容や業界への影響も含めて簡潔にまとめてください。

記事本文:
{article_text}

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