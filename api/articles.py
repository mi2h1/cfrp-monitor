from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.parse
import jwt
import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            # 認証チェック
            user_data = self.verify_token()
            if not user_data:
                response = {
                    "success": False,
                    "error": "認証が必要です"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # 記事一覧を取得
            articles = self.get_articles()
            
            if articles is not None:
                response = {
                    "success": True,
                    "articles": articles,
                    "count": len(articles)
                }
            else:
                response = {
                    "success": False,
                    "error": "記事の取得に失敗しました"
                }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            response = {
                "success": False,
                "error": f"サーバーエラー: {str(e)}"
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            # 認証チェック
            user_data = self.verify_token()
            if not user_data:
                response = {
                    "success": False,
                    "error": "認証が必要です"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # リクエストボディを取得
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            print(f"DEBUG: Raw POST data: {post_data}")
            
            data = json.loads(post_data.decode('utf-8'))
            print(f"DEBUG: Parsed JSON data: {data}")
            
            # 記事追加
            result = self.add_article(data, user_data)
            
            if result:
                response = {
                    "success": True,
                    "message": "記事を追加しました",
                    "article": result
                }
            else:
                response = {
                    "success": False,
                    "error": "記事の追加に失敗しました"
                }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            response = {
                "success": False,
                "error": f"サーバーエラー: {str(e)}"
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def verify_token(self):
        """JWTトークンの検証"""
        try:
            auth_header = self.headers.get('Authorization')
            print(f"DEBUG: Authorization header: {auth_header}")
            
            if not auth_header or not auth_header.startswith('Bearer '):
                print("DEBUG: No valid Authorization header")
                return None
            
            token = auth_header.split(' ')[1]
            print(f"DEBUG: Token: {token[:20]}...")
            
            secret = os.environ.get('JWT_SECRET', 'default-secret-key')
            print(f"DEBUG: JWT Secret exists: {bool(secret)}")
            
            # トークンをデコード
            payload = jwt.decode(token, secret, algorithms=['HS256'])
            print(f"DEBUG: Token payload: {payload}")
            return payload
            
        except jwt.ExpiredSignatureError:
            print("DEBUG: Token expired")
            return None
        except jwt.InvalidTokenError as e:
            print(f"DEBUG: Invalid token: {e}")
            return None
        except Exception as e:
            print(f"Token verification error: {e}")
            return None

    def get_articles(self):
        """記事一覧を取得"""
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return None
            
            # itemsテーブルから記事を取得
            url = f"{supabase_url}/rest/v1/items?select=*&order=added_at.desc&limit=100"
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json'
            }
            
            print(f"DEBUG: Supabase URL: {url}")
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                print(f"DEBUG: Articles count: {len(data)}")
                return data
                
        except urllib.error.HTTPError as e:
            print(f"Get articles HTTP error: {e.code} - {e.reason}")
            error_body = e.read().decode('utf-8')
            print(f"Error body: {error_body}")
            return None
        except Exception as e:
            print(f"Get articles error: {e}")
            return None

    def add_article(self, data, user_data):
        """記事を追加"""
        try:
            print(f"DEBUG: Add article called with data: {data}")
            print(f"DEBUG: User data: {user_data}")
            
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                print("DEBUG: Missing environment variables")
                return None
            
            # 必須フィールドの確認
            if not data.get('url') or not data.get('title'):
                print("DEBUG: Missing required fields (url or title)")
                return None
            
            # itemsテーブル用のデータを準備
            item_data = {
                'url': data['url'],
                'title': data['title'],
                'body': data.get('body', ''),
                'source_id': data.get('source_id'),
                'last_edited_by': user_data['user_id'],
                'src_type': data.get('src_type', 'manual'),
                'status': 'unread',
                'published_at': data.get('published_at', datetime.datetime.now().date().isoformat())
            }
            
            print(f"DEBUG: Item data to insert: {item_data}")
            
            # データベースに追加
            url = f"{supabase_url}/rest/v1/items"
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json'
            }
            
            print(f"DEBUG: Supabase URL: {url}")
            
            req = urllib.request.Request(
                url, 
                data=json.dumps(item_data).encode('utf-8'),
                headers=headers
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                print(f"DEBUG: Insert result: {result}")
                return result[0] if result else None
                
        except urllib.error.HTTPError as e:
            print(f"Add article HTTP error: {e.code} - {e.reason}")
            error_body = e.read().decode('utf-8')
            print(f"Error body: {error_body}")
            return None
        except Exception as e:
            print(f"Add article error: {e}")
            return None