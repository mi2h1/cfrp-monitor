from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.parse
import jwt
import datetime
import hashlib
import secrets
import sys
sys.path.append('/mnt/f/OneDrive - 株式会社羽生田鉄工所/Git/cfrp-monitor')
from utils.timezone_utils import now_jst_naive_iso

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
            
            # 管理者権限チェック
            if user_data.get('role') != 'admin':
                response = {
                    "success": False,
                    "error": "管理者権限が必要です"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # ユーザー一覧を取得
            users = self.get_users()
            
            if users is not None:
                # パスワード情報を隠す
                safe_users = []
                for user in users:
                    safe_user = {
                        'id': user.get('id'),
                        'user_id': user.get('user_id'),
                        'display_name': user.get('display_name'),
                        'role': user.get('role'),
                        'created_at': user.get('created_at'),
                        'last_login': user.get('last_login')
                    }
                    safe_users.append(safe_user)
                
                response = {
                    "success": True,
                    "users": safe_users,
                    "count": len(safe_users)
                }
            else:
                response = {
                    "success": False,
                    "error": "ユーザーの取得に失敗しました"
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
            
            # 管理者権限チェック
            if user_data.get('role') != 'admin':
                response = {
                    "success": False,
                    "error": "管理者権限が必要です"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # リクエストボディを取得
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # ユーザー追加
            result = self.add_user(data, user_data)
            
            if result:
                response = {
                    "success": True,
                    "message": "ユーザーを追加しました",
                    "user": result
                }
            else:
                response = {
                    "success": False,
                    "error": "ユーザーの追加に失敗しました"
                }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            response = {
                "success": False,
                "error": f"サーバーエラー: {str(e)}"
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_PATCH(self):
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
            
            # 管理者権限チェック
            if user_data.get('role') != 'admin':
                response = {
                    "success": False,
                    "error": "管理者権限が必要です"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # リクエストボディを取得
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # ユーザーID取得（クエリパラメータから）
            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            target_user_id = query_params.get('id', [None])[0]
            
            if not target_user_id:
                response = {
                    "success": False,
                    "error": "ユーザーIDが指定されていません"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # ユーザー更新
            result = self.update_user(target_user_id, data, user_data)
            
            if result:
                response = {
                    "success": True,
                    "message": "ユーザーを更新しました",
                    "user": result
                }
            else:
                response = {
                    "success": False,
                    "error": "ユーザーの更新に失敗しました"
                }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            response = {
                "success": False,
                "error": f"サーバーエラー: {str(e)}"
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_DELETE(self):
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
            
            # 管理者権限チェック
            if user_data.get('role') != 'admin':
                response = {
                    "success": False,
                    "error": "管理者権限が必要です"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # ユーザーID取得（クエリパラメータから）
            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            target_user_id = query_params.get('id', [None])[0]
            
            if not target_user_id:
                response = {
                    "success": False,
                    "error": "ユーザーIDが指定されていません"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # 自分自身は削除できない
            if target_user_id == user_data.get('user_id'):
                response = {
                    "success": False,
                    "error": "自分自身は削除できません"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # ユーザー削除
            result = self.delete_user(target_user_id, user_data)
            
            if result:
                response = {
                    "success": True,
                    "message": "ユーザーを削除しました"
                }
            else:
                response = {
                    "success": False,
                    "error": "ユーザーの削除に失敗しました"
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
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
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

    def get_users(self):
        """ユーザー一覧を取得"""
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return None
            
            # usersテーブルからユーザーを取得
            url = f"{supabase_url}/rest/v1/users?select=*&order=created_at.desc"
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json'
            }
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data
                
        except urllib.error.HTTPError as e:
            print(f"Get users HTTP error: {e.code} - {e.reason}")
            error_body = e.read().decode('utf-8')
            print(f"Error body: {error_body}")
            return None
        except Exception as e:
            print(f"Get users error: {e}")
            return None

    def add_user(self, data, admin_user):
        """ユーザーを追加"""
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return None
            
            # 必須フィールドの確認
            if not data.get('user_id') or not data.get('password'):
                return None
            
            # パスワードバリデーション
            if len(data['password']) < 4:
                return None
            
            # パスワードハッシュ化
            salt = secrets.token_hex(16)
            salted_password = data['password'] + salt
            password_hash = hashlib.sha256(salted_password.encode('utf-8')).hexdigest()
            
            # usersテーブル用のデータを準備
            user_data = {
                'user_id': data['user_id'],
                'display_name': data.get('display_name', data['user_id']),
                'password_hash': password_hash,
                'password_salt': salt,
                'role': data.get('role', 'viewer'),
                'created_at': now_jst_naive_iso(),
                'last_login': now_jst_naive_iso()
            }
            
            # データベースに追加
            url = f"{supabase_url}/rest/v1/users"
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json',
                'Prefer': 'return=representation'
            }
            
            req = urllib.request.Request(
                url, 
                data=json.dumps(user_data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req) as response:
                response_body = response.read().decode('utf-8')
                if response_body.strip():
                    result = json.loads(response_body)
                    # パスワード情報を隠して返す
                    safe_result = result[0] if isinstance(result, list) and result else result
                    if safe_result:
                        safe_result.pop('password_hash', None)
                        safe_result.pop('password_salt', None)
                    return safe_result
                else:
                    return {"success": True, "message": "User inserted successfully"}
                
        except urllib.error.HTTPError as e:
            print(f"Add user HTTP error: {e.code} - {e.reason}")
            error_body = e.read().decode('utf-8')
            print(f"Error body: {error_body}")
            return None
        except Exception as e:
            print(f"Add user error: {e}")
            return None

    def update_user(self, user_id, data, admin_user):
        """ユーザーを更新"""
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return None
            
            # 更新データを準備
            update_data = {}
            if data.get('display_name'):
                update_data['display_name'] = data['display_name']
            if data.get('role'):
                update_data['role'] = data['role']
            
            # パスワード更新の場合
            if data.get('password'):
                # パスワードバリデーション
                if len(data['password']) < 4:
                    return None
                salt = secrets.token_hex(16)
                salted_password = data['password'] + salt
                password_hash = hashlib.sha256(salted_password.encode('utf-8')).hexdigest()
                update_data['password_hash'] = password_hash
                update_data['password_salt'] = salt
            
            # データベースを更新
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
                response_body = response.read().decode('utf-8')
                if response_body.strip():
                    result = json.loads(response_body)
                    safe_result = result[0] if isinstance(result, list) and result else result
                    if safe_result:
                        safe_result.pop('password_hash', None)
                        safe_result.pop('password_salt', None)
                    return safe_result
                else:
                    return {"success": True, "message": "User updated successfully"}
                    
        except urllib.error.HTTPError as e:
            print(f"Update user HTTP error: {e.code} - {e.reason}")
            error_body = e.read().decode('utf-8')
            print(f"Error body: {error_body}")
            return None
        except Exception as e:
            print(f"Update user error: {e}")
            return None

    def delete_user(self, user_id, admin_user):
        """ユーザーを削除"""
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return None
            
            # データベースから削除
            url = f"{supabase_url}/rest/v1/users?user_id=eq.{user_id}"
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json'
            }
            
            req = urllib.request.Request(
                url,
                headers=headers,
                method='DELETE'
            )
            
            with urllib.request.urlopen(req) as response:
                return True
                    
        except urllib.error.HTTPError as e:
            print(f"Delete user HTTP error: {e.code} - {e.reason}")
            error_body = e.read().decode('utf-8')
            print(f"Error body: {error_body}")
            return None
        except Exception as e:
            print(f"Delete user error: {e}")
            return None