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
            
            # 情報源一覧を取得
            sources = self.get_sources()
            
            if sources is not None:
                response = {
                    "success": True,
                    "sources": sources,
                    "count": len(sources)
                }
            else:
                response = {
                    "success": False,
                    "error": "情報源の取得に失敗しました"
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
            
            # 編集者以上の権限チェック
            if user_data.get('role') not in ['admin', 'editor']:
                response = {
                    "success": False,
                    "error": "編集者以上の権限が必要です"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # リクエストボディを取得
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # 情報源追加
            result = self.add_source(data, user_data)
            
            if result:
                response = {
                    "success": True,
                    "message": "情報源を追加しました",
                    "source": result
                }
            else:
                response = {
                    "success": False,
                    "error": "情報源の追加に失敗しました"
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
            
            # 編集者以上の権限チェック
            if user_data.get('role') not in ['admin', 'editor']:
                response = {
                    "success": False,
                    "error": "編集者以上の権限が必要です"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # リクエストボディを取得
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # 情報源ID取得（クエリパラメータから）
            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            source_id = query_params.get('id', [None])[0]
            
            if not source_id:
                response = {
                    "success": False,
                    "error": "情報源IDが指定されていません"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # 情報源更新
            result = self.update_source(source_id, data, user_data)
            
            if result:
                response = {
                    "success": True,
                    "message": "情報源を更新しました",
                    "source": result
                }
            else:
                response = {
                    "success": False,
                    "error": "情報源の更新に失敗しました"
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
            
            # 編集者以上の権限チェック
            if user_data.get('role') not in ['admin', 'editor']:
                response = {
                    "success": False,
                    "error": "編集者以上の権限が必要です"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # 情報源ID取得（クエリパラメータから）
            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            source_id = query_params.get('id', [None])[0]
            
            if not source_id:
                response = {
                    "success": False,
                    "error": "情報源IDが指定されていません"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # 情報源削除
            result = self.delete_source(source_id, user_data)
            
            if result:
                response = {
                    "success": True,
                    "message": "情報源を削除しました"
                }
            else:
                response = {
                    "success": False,
                    "error": "情報源の削除に失敗しました"
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

    def get_sources(self):
        """情報源一覧を取得"""
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return None
            
            # sourcesテーブルから情報源を取得
            url = f"{supabase_url}/rest/v1/sources?select=*&order=updated_at.desc&limit=100"
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
            print(f"Get sources HTTP error: {e.code} - {e.reason}")
            error_body = e.read().decode('utf-8')
            print(f"Error body: {error_body}")
            return None
        except Exception as e:
            print(f"Get sources error: {e}")
            return None

    def add_source(self, data, user_data):
        """情報源を追加"""
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return None
            
            # 必須フィールドの確認
            if not data.get('name') or not data.get('domain'):
                return None
            
            # sourcesテーブル用のデータを準備
            source_data = {
                'name': data['name'],
                'domain': data['domain'],
                'category': data.get('category', 'unknown'),
                'country_code': data.get('country_code', 'JP'),
                'relevance': data.get('relevance', 5),
                'description': data.get('description', ''),
                'urls': data.get('urls', []),
                'policy_url': data.get('policy_url', ''),
                'parser': data.get('parser', 'rss'),
                'ua': data.get('ua', ''),
                'acquisition_mode': data.get('acquisition_mode', 'auto'),
                'access_level': data.get('access_level', 1),
                'restrict_lvl': data.get('restrict_lvl', 0),
                'http_fallback': data.get('http_fallback', False),
                'retry_count': data.get('retry_count', 3),
                'backoff_factor': data.get('backoff_factor', 1.0),
                'deleted': False,
                'updated_at': datetime.datetime.now().isoformat(),
                'last_edited_by': user_data['user_id']
            }
            
            # データベースに追加
            url = f"{supabase_url}/rest/v1/sources"
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json',
                'Prefer': 'return=representation'
            }
            
            req = urllib.request.Request(
                url, 
                data=json.dumps(source_data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req) as response:
                response_body = response.read().decode('utf-8')
                if response_body.strip():
                    result = json.loads(response_body)
                    return result[0] if isinstance(result, list) and result else result
                else:
                    return {"success": True, "message": "Source inserted successfully"}
                
        except urllib.error.HTTPError as e:
            print(f"Add source HTTP error: {e.code} - {e.reason}")
            error_body = e.read().decode('utf-8')
            print(f"Error body: {error_body}")
            return None
        except Exception as e:
            print(f"Add source error: {e}")
            return None

    def update_source(self, source_id, data, user_data):
        """情報源を更新"""
        try:
            print(f"DEBUG: Update source called with source_id: {source_id}")
            print(f"DEBUG: Input data: {json.dumps(data, ensure_ascii=False)}")
            print(f"DEBUG: User data: {user_data}")
            
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return None
            
            # 更新データを準備
            update_data = {}
            if data.get('name'):
                update_data['name'] = data['name']
            if data.get('domain'):
                update_data['domain'] = data['domain']
            if data.get('category'):
                update_data['category'] = data['category']
            if data.get('country_code'):
                update_data['country_code'] = data['country_code']
            if data.get('relevance') is not None:
                update_data['relevance'] = data['relevance']
            if data.get('description') is not None:
                print(f"DEBUG: Description in data: '{data.get('description')}' (type: {type(data.get('description'))})")
                update_data['description'] = data['description']
            if data.get('urls') is not None:
                update_data['urls'] = data['urls']
            if data.get('policy_url') is not None:
                update_data['policy_url'] = data['policy_url']
            if data.get('parser'):
                update_data['parser'] = data['parser']
            if data.get('ua') is not None:
                update_data['ua'] = data['ua']
            if data.get('acquisition_mode'):
                update_data['acquisition_mode'] = data['acquisition_mode']
            if data.get('access_level') is not None:
                update_data['access_level'] = data['access_level']
            if data.get('restrict_lvl') is not None:
                update_data['restrict_lvl'] = data['restrict_lvl']
            if data.get('http_fallback') is not None:
                update_data['http_fallback'] = data['http_fallback']
            if data.get('retry_count') is not None:
                update_data['retry_count'] = data['retry_count']
            if data.get('backoff_factor') is not None:
                update_data['backoff_factor'] = data['backoff_factor']
            if data.get('deleted') is not None:
                update_data['deleted'] = data['deleted']
            
            # 更新者情報を追加
            update_data['last_edited_by'] = user_data['user_id']
            update_data['updated_at'] = datetime.datetime.now().isoformat()
            
            # データベースを更新
            print(f"DEBUG: Final update_data: {json.dumps(update_data, ensure_ascii=False)}")
            
            url = f"{supabase_url}/rest/v1/sources?id=eq.{source_id}"
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json',
                'Prefer': 'return=representation'
            }
            
            print(f"DEBUG: Updating URL: {url}")
            print(f"DEBUG: Request body: {json.dumps(update_data, ensure_ascii=False)}")
            
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
                    return result[0] if isinstance(result, list) and result else result
                else:
                    return {"success": True, "message": "Source updated successfully"}
                    
        except urllib.error.HTTPError as e:
            print(f"Update source HTTP error: {e.code} - {e.reason}")
            error_body = e.read().decode('utf-8')
            print(f"Error body: {error_body}")
            return None
        except Exception as e:
            print(f"Update source error: {e}")
            return None

    def delete_source(self, source_id, user_data):
        """情報源を削除（論理削除）"""
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return None
            
            # 論理削除（deletedフラグを立てる）
            update_data = {
                'deleted': True,
                'last_edited_by': user_data['user_id'],
                'updated_at': datetime.datetime.now().isoformat()
            }
            
            url = f"{supabase_url}/rest/v1/sources?id=eq.{source_id}"
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json'
            }
            
            req = urllib.request.Request(
                url,
                data=json.dumps(update_data).encode('utf-8'),
                headers=headers,
                method='PATCH'
            )
            
            with urllib.request.urlopen(req) as response:
                return True
                    
        except urllib.error.HTTPError as e:
            print(f"Delete source HTTP error: {e.code} - {e.reason}")
            error_body = e.read().decode('utf-8')
            print(f"Error body: {error_body}")
            return None
        except Exception as e:
            print(f"Delete source error: {e}")
            return None