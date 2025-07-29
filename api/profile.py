from http.server import BaseHTTPRequestHandler
import json
import os
import jwt
import urllib.request
import urllib.parse
import sys
sys.path.append('/mnt/f/OneDrive - 株式会社羽生田鉄工所/Git/cfrp-monitor')
from utils.timezone_utils import now_jst_naive_iso

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """現在のユーザーのプロフィール情報を取得"""
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
            
            # ユーザー情報を取得
            user_info = self.get_user_profile(user_data['user_id'])
            
            if user_info:
                response = {
                    "success": True,
                    "user": user_info
                }
            else:
                response = {
                    "success": False,
                    "error": "ユーザー情報の取得に失敗しました"
                }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            response = {
                "success": False,
                "error": f"サーバーエラー: {str(e)}"
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_PATCH(self):
        """ユーザーのプロフィール情報を更新（自分のみ）"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, PATCH, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
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
            data = json.loads(post_data.decode('utf-8'))
            
            # プロフィール更新
            result = self.update_profile(user_data['user_id'], data)
            
            if result:
                response = {
                    "success": True,
                    "message": "プロフィールを更新しました",
                    "user": result
                }
            else:
                response = {
                    "success": False,
                    "error": "プロフィールの更新に失敗しました"
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
        self.send_header('Access-Control-Allow-Methods', 'GET, PATCH, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def verify_token(self):
        """JWTトークンの検証"""
        try:
            auth_header = self.headers.get('Authorization')
            
            if not auth_header or not auth_header.startswith('Bearer '):
                return None
            
            token = auth_header.split(' ')[1]
            secret = os.environ.get('JWT_SECRET', 'default-secret-key')
            
            # トークンをデコード
            payload = jwt.decode(token, secret, algorithms=['HS256'])
            return payload
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception:
            return None

    def get_user_profile(self, user_id):
        """ユーザーのプロフィール情報を取得"""
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return None
            
            url = f"{supabase_url}/rest/v1/users?user_id=eq.{user_id}&select=user_id,display_name,role,created_at"
            
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json'
            }
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data[0] if data else None
                
        except Exception as e:
            print(f"Get user profile error: {str(e)}")
            return None

    def update_profile(self, user_id, data):
        """ユーザーのプロフィールを更新"""
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return None
            
            # 更新データを準備
            update_data = {}
            
            # 表示名更新
            if 'display_name' in data and data['display_name']:
                update_data['display_name'] = data['display_name']
            
            # パスワード更新
            if 'password' in data and data['password']:
                # パスワードバリデーション
                if len(data['password']) < 4:
                    return None
                
                # パスワードハッシュ化（既存のusers.pyと同じ方法）
                import hashlib
                import secrets
                
                salt = secrets.token_hex(16)
                salted_password = data['password'] + salt
                password_hash = hashlib.sha256(salted_password.encode('utf-8')).hexdigest()
                
                update_data['password_hash'] = password_hash
                update_data['password_salt'] = salt
            
            if not update_data:
                return None
            
            url = f"{supabase_url}/rest/v1/users?user_id=eq.{user_id}"
            
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json',
                'Prefer': 'return=representation'
            }
            
            req = urllib.request.Request(
                url, 
                data=json.dumps(update_data).encode('utf-8'),
                headers=headers,
                method='PATCH'
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                # パスワード情報を隠して返す
                safe_result = result[0] if isinstance(result, list) and result else result
                if safe_result:
                    safe_result.pop('password_hash', None)
                    safe_result.pop('password_salt', None)
                return safe_result
                
        except urllib.error.HTTPError as e:
            print(f"Update profile HTTP error: {e.code} - {e.reason}")
            error_body = e.read().decode('utf-8')
            print(f"Error body: {error_body}")
            return None
        except Exception as e:
            print(f"Update profile error: {str(e)}")
            return None