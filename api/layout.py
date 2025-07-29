from http.server import BaseHTTPRequestHandler
import json
import os
import jwt
import urllib.request
import datetime
import sys
sys.path.append('/mnt/f/OneDrive - 株式会社羽生田鉄工所/Git/cfrp-monitor')
from utils.timezone_utils import format_jst_display

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
            
            # 最終更新時刻を取得
            last_updated_stats = self.get_last_updated_stats()
            
            response = {
                "success": True,
                "layout": layout_config,
                "last_updated": last_updated_stats,
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
                "label": "記事管理",
                "icon": "fa-newspaper",
                "href": "/articles",
                "active": False,
                "roles": ["admin", "editor", "viewer"]
            }
        ]
        
        # 編集者以上の権限
        if role in ['admin', 'editor']:
            navigation.append({
                "id": "sources",
                "label": "情報源管理",
                "icon": "fa-rss",
                "href": "/sources",
                "active": False,
                "roles": ["admin", "editor"]
            })
        
        # 管理者のみの権限
        if role == 'admin':
            navigation.append({
                "id": "users",
                "label": "ユーザー管理",
                "icon": "fa-users",
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
                "display_name": user_data.get('display_name') if user_data.get('display_name') else None,
                "role": role,
                "role_display": {
                    "admin": "管理者",
                    "editor": "編集者", 
                    "viewer": "閲覧者"
                }.get(role, role)
            }
        }

    def get_last_updated_stats(self):
        """記事管理と情報源管理の最終更新時刻を取得"""
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return None
            
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json'
            }
            
            stats = {}
            
            # 記事の最終更新を取得（追加日時または確認日時の新しい方）
            try:
                articles_url = f"{supabase_url}/rest/v1/articles?select=added_at,reviewed_at&order=added_at.desc&limit=1"
                req = urllib.request.Request(articles_url, headers=headers)
                with urllib.request.urlopen(req) as response:
                    articles_data = json.loads(response.read().decode('utf-8'))
                    if articles_data:
                        latest_article = articles_data[0]
                        # reviewed_atがあればそれを、なければadded_atを使用
                        article_updated = latest_article.get('reviewed_at') or latest_article.get('added_at')
                        if article_updated:
                            # ユーティリティ関数でJST表示形式に変換
                            stats['articles'] = format_jst_display(article_updated)
                        else:
                            stats['articles'] = None
                    else:
                        stats['articles'] = None
            except Exception as e:
                print(f"Articles last updated error: {e}")
                stats['articles'] = None
            
            # 情報源の最終更新を取得（収集日時または更新日時の新しい方）
            try:
                sources_url = f"{supabase_url}/rest/v1/sources?select=updated_at,last_collected_at&order=updated_at.desc&limit=1"
                req = urllib.request.Request(sources_url, headers=headers)
                with urllib.request.urlopen(req) as response:
                    sources_data = json.loads(response.read().decode('utf-8'))
                    if sources_data:
                        latest_source = sources_data[0]
                        # last_collected_atがあればそれを、なければupdated_atを使用
                        source_updated = latest_source.get('last_collected_at') or latest_source.get('updated_at')
                        if source_updated:
                            # ユーティリティ関数でJST表示形式に変換
                            stats['sources'] = format_jst_display(source_updated)
                        else:
                            stats['sources'] = None
                    else:
                        stats['sources'] = None
            except Exception as e:
                print(f"Sources last updated error: {e}")
                stats['sources'] = None
            
            return stats
                
        except Exception as e:
            print(f"Get last updated stats error: {e}")
            return None