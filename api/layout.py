from http.server import BaseHTTPRequestHandler
import json
import os
import jwt

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
            
            # ユーザー権限に基づいてナビゲーションを生成
            layout_config = self.generate_layout(user_data)
            
            response = {
                "success": True,
                "layout": layout_config,
                "user": {
                    "user_id": user_data.get('user_id'),
                    "display_name": user_data.get('display_name'),
                    "role": user_data.get('role')
                }
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
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
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

    def generate_layout(self, user_data):
        """ユーザー権限に基づいてレイアウト設定を生成"""
        role = user_data.get('role', 'viewer')
        
        # 基本ナビゲーション（全ユーザー共通）
        navigation = [
            {
                "id": "articles",
                "label": "📰 記事管理",
                "href": "/",
                "active": False,
                "roles": ["admin", "editor", "viewer"]
            }
        ]
        
        # 編集者以上の権限
        if role in ['admin', 'editor']:
            navigation.extend([
                {
                    "id": "sources",
                    "label": "📡 情報源管理", 
                    "href": "/sources",
                    "active": False,
                    "roles": ["admin", "editor"]
                },
                {
                    "id": "candidates",
                    "label": "🔍 候補管理",
                    "href": "/candidates",
                    "active": False,
                    "roles": ["admin", "editor"]
                }
            ])
        
        # 管理者のみの権限
        if role == 'admin':
            navigation.append({
                "id": "users",
                "label": "👥 ユーザー管理",
                "href": "/users", 
                "active": False,
                "roles": ["admin"]
            })
        
        # 機能アクセス権限
        features = {
            "can_create_articles": role in ['admin', 'editor'],
            "can_edit_articles": role in ['admin', 'editor'],
            "can_delete_articles": role in ['admin', 'editor'],
            "can_manage_sources": role in ['admin', 'editor'],
            "can_manage_users": role == 'admin',
            "can_manage_candidates": role in ['admin', 'editor'],
            "can_view_analytics": role in ['admin', 'editor']
        }
        
        # テストページへのアクセス（開発環境用）
        test_pages = []
        if role in ['admin', 'editor']:
            test_pages = [
                {"label": "記事API テスト", "href": "/articles-test"},
                {"label": "情報源API テスト", "href": "/sources-test"},
                {"label": "候補API テスト", "href": "/candidates-test"}
            ]
        if role == 'admin':
            test_pages.append({"label": "ユーザーAPI テスト", "href": "/users-test"})
        
        return {
            "navigation": navigation,
            "features": features,
            "test_pages": test_pages,
            "user_menu": {
                "display_name": user_data.get('display_name') or user_data.get('user_id'),
                "role": role,
                "role_display": {
                    "admin": "管理者",
                    "editor": "編集者", 
                    "viewer": "閲覧者"
                }.get(role, role)
            }
        }