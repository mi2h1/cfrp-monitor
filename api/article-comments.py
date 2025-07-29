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
        """記事のコメント一覧を取得"""
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
            
            # クエリパラメータを取得
            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            article_id = query_params.get('article_id', [None])[0]
            
            if not article_id:
                response = {
                    "success": False,
                    "error": "記事IDが指定されていません"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # コメント一覧を取得
            comments = self.get_article_comments(article_id)
            
            response = {
                "success": True,
                "comments": comments
            }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            response = {
                "success": False,
                "error": f"サーバーエラー: {str(e)}"
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_POST(self):
        """コメントを投稿"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
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
            
            # 必須フィールドをチェック
            required_fields = ['article_id', 'comment']
            for field in required_fields:
                if field not in data or not data[field]:
                    response = {
                        "success": False,
                        "error": f"{field}が指定されていません"
                    }
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return
            
            # 1階層のみの制限を適用
            parent_comment_id = data.get('parent_comment_id')
            if parent_comment_id:
                # 親コメントを取得して、それがルートコメントかチェック
                parent_comment = self.get_comment_by_id(parent_comment_id)
                if parent_comment and parent_comment.get('parent_comment_id'):
                    # 親コメントが既に返信の場合、その親（ルートコメント）を参照する
                    parent_comment_id = parent_comment['parent_comment_id']
            
            # コメントを保存
            comment_data = {
                'article_id': data['article_id'],
                'parent_comment_id': parent_comment_id,
                'user_id': user_data['user_id'],
                'comment': data['comment'],
                'created_at': now_jst_naive_iso(),
                'updated_at': now_jst_naive_iso(),
                'is_deleted': False
            }
            
            result = self.create_comment(comment_data)
            
            if result:
                response = {
                    "success": True,
                    "message": "コメントを投稿しました",
                    "comment": result
                }
            else:
                response = {
                    "success": False,
                    "error": "コメントの投稿に失敗しました"
                }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            response = {
                "success": False,
                "error": f"サーバーエラー: {str(e)}"
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_PUT(self):
        """コメントを編集"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, OPTIONS')
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
            
            # 必須フィールドをチェック
            required_fields = ['comment_id', 'comment']
            for field in required_fields:
                if field not in data or not data[field]:
                    response = {
                        "success": False,
                        "error": f"{field}が指定されていません"
                    }
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return
            
            # コメントの所有者チェック
            comment = self.get_comment_by_id(data['comment_id'])
            if not comment:
                response = {
                    "success": False,
                    "error": "コメントが見つかりません"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            if comment['user_id'] != user_data['user_id']:
                response = {
                    "success": False,
                    "error": "自分のコメントのみ編集できます"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # コメントを更新
            result = self.update_comment(data['comment_id'], data['comment'])
            
            if result:
                response = {
                    "success": True,
                    "message": "コメントを編集しました",
                    "comment": result
                }
            else:
                response = {
                    "success": False,
                    "error": "コメントの編集に失敗しました"
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
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, OPTIONS')
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

    def get_article_comments(self, article_id):
        """記事のコメント一覧を取得"""
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return []
            
            # コメント一覧を取得（削除されていないもののみ、作成日時順）
            # JOINは300エラーになるため、まずはJOINなしで取得
            url = f'{supabase_url}/rest/v1/article_comments?select=*&article_id=eq.{article_id}&is_deleted=eq.false&order=created_at.asc'
            
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json'
            }
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                comments = json.loads(response.read().decode('utf-8'))
                
                # ユーザーIDのリストを作成
                user_ids = list(set([comment['user_id'] for comment in comments if comment.get('user_id')]))
                
                if user_ids:
                    # ユーザー情報を一括取得
                    user_ids_str = ','.join(user_ids)
                    users_url = f'{supabase_url}/rest/v1/users?select=user_id,display_name&user_id=in.({user_ids_str})'
                    
                    try:
                        users_req = urllib.request.Request(users_url, headers=headers)
                        with urllib.request.urlopen(users_req) as users_response:
                            users_data = json.loads(users_response.read().decode('utf-8'))
                            
                            # ユーザーIDをキーとした辞書を作成
                            users_dict = {user['user_id']: user for user in users_data}
                            
                            # コメントにユーザー情報を追加
                            for comment in comments:
                                user_id = comment.get('user_id')
                                if user_id and user_id in users_dict:
                                    comment['users'] = {'display_name': users_dict[user_id].get('display_name')}
                    except Exception as e:
                        print(f"Failed to fetch user info: {e}")
                        # ユーザー情報取得に失敗してもコメントは返す
                
                return comments
        
        except Exception as e:
            print(f"Get comments error: {str(e)}")
            return []

    def get_comment_by_id(self, comment_id):
        """コメントIDでコメントを取得"""
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return None
            
            url = f"{supabase_url}/rest/v1/article_comments?id=eq.{comment_id}&limit=1"
            
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
            print(f"Get comment by ID error: {str(e)}")
            return None
    
    def create_comment(self, comment_data):
        """コメントを作成"""
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return None
            
            url = f"{supabase_url}/rest/v1/article_comments"
            
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json',
                'Prefer': 'return=representation'
            }
            
            # parent_comment_idがNullの場合は除外
            if comment_data['parent_comment_id'] is None:
                del comment_data['parent_comment_id']
            
            post_data = json.dumps(comment_data).encode('utf-8')
            
            req = urllib.request.Request(url, data=post_data, headers=headers, method='POST')
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result[0] if result else None
        
        except Exception as e:
            print(f"Create comment error: {str(e)}")
            return None
    
    def update_comment(self, comment_id, new_comment):
        """コメントを更新"""
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return None
            
            url = f"{supabase_url}/rest/v1/article_comments?id=eq.{comment_id}"
            
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json',
                'Prefer': 'return=representation'
            }
            
            update_data = {
                'comment': new_comment,
                'updated_at': now_jst_naive_iso()
            }
            
            req = urllib.request.Request(
                url, 
                data=json.dumps(update_data).encode('utf-8'),
                headers=headers,
                method='PATCH'
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result[0] if result else None
        
        except Exception as e:
            print(f"Update comment error: {str(e)}")
            return None