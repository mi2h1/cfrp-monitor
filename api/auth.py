from http.server import BaseHTTPRequestHandler
import json
import hashlib
import os
import urllib.request
import urllib.parse
import uuid
import jwt
import datetime

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            # リクエストボディを取得
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            user_id = data.get('user_id')
            password = data.get('password')
            
            if not user_id or not password:
                response = {
                    "success": False,
                    "error": "ユーザーIDとパスワードを入力してください"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # Supabaseからユーザー情報を取得
            user_data = self.get_user_from_supabase(user_id)
            
            if not user_data:
                response = {
                    "success": False,
                    "error": "ユーザーが見つかりません"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # パスワード検証
            if self.verify_password(password, user_data):
                # JWTトークン生成
                token = self.generate_jwt_token(user_data)
                
                response = {
                    "success": True,
                    "token": token,
                    "user": {
                        "user_id": user_data['user_id'],
                        "display_name": user_data['display_name'],
                        "role": user_data['role']
                    }
                }
            else:
                response = {
                    "success": False,
                    "error": "パスワードが間違っています"
                }
            
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
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
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def get_user_from_supabase(self, user_id):
        """Supabaseからユーザー情報を取得"""
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return None
            
            # Supabase API呼び出し
            url = f"{supabase_url}/rest/v1/users?user_id=eq.{user_id}"
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
            print(f"Supabase error: {e}")
            return None
    
    def verify_password(self, password, user_data):
        """パスワード検証"""
        try:
            # ハッシュ化されたパスワードがある場合
            if user_data.get('password_salt'):
                password_hash = hashlib.sha256(
                    (password + user_data['password_salt']).encode()
                ).hexdigest()
                return password_hash == user_data['password_hash']
            else:
                # 平文パスワードの場合（後方互換性）
                return password == user_data['password_hash']
        except Exception as e:
            print(f"Password verification error: {e}")
            return False
    
    def generate_jwt_token(self, user_data):
        """JWTトークン生成"""
        try:
            secret = os.environ.get('JWT_SECRET', 'default-secret-key')
            payload = {
                'user_id': user_data['user_id'],
                'role': user_data['role'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }
            return jwt.encode(payload, secret, algorithm='HS256')
        except Exception as e:
            print(f"JWT generation error: {e}")
            return str(uuid.uuid4())  # フォールバック用のランダムトークン