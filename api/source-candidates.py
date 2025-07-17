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
            
            # 編集者以上の権限チェック
            if user_data.get('role') not in ['admin', 'editor']:
                response = {
                    "success": False,
                    "error": "編集者以上の権限が必要です"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # 情報源候補一覧を取得
            candidates = self.get_source_candidates()
            
            if candidates is not None:
                response = {
                    "success": True,
                    "candidates": candidates,
                    "count": len(candidates)
                }
            else:
                response = {
                    "success": False,
                    "error": "情報源候補の取得に失敗しました"
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
            
            # 情報源候補追加
            result = self.add_source_candidate(data, user_data)
            
            if result:
                response = {
                    "success": True,
                    "message": "情報源候補を追加しました",
                    "candidate": result
                }
            else:
                response = {
                    "success": False,
                    "error": "情報源候補の追加に失敗しました"
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
            
            # 候補ID取得（クエリパラメータから）
            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            candidate_id = query_params.get('id', [None])[0]
            
            if not candidate_id:
                response = {
                    "success": False,
                    "error": "候補IDが指定されていません"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # 情報源候補更新
            result = self.update_source_candidate(candidate_id, data, user_data)
            
            if result:
                response = {
                    "success": True,
                    "message": "情報源候補を更新しました",
                    "candidate": result
                }
            else:
                response = {
                    "success": False,
                    "error": "情報源候補の更新に失敗しました"
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
            
            # 候補ID取得（クエリパラメータから）
            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            candidate_id = query_params.get('id', [None])[0]
            
            if not candidate_id:
                response = {
                    "success": False,
                    "error": "候補IDが指定されていません"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # 情報源候補削除
            result = self.delete_source_candidate(candidate_id, user_data)
            
            if result:
                response = {
                    "success": True,
                    "message": "情報源候補を削除しました"
                }
            else:
                response = {
                    "success": False,
                    "error": "情報源候補の削除に失敗しました"
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

    def get_source_candidates(self):
        """情報源候補一覧を取得"""
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return None
            
            # source_candidatesテーブルから候補を取得
            url = f"{supabase_url}/rest/v1/source_candidates?select=*&order=discovered_at.desc&limit=100"
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
            print(f"Get source candidates HTTP error: {e.code} - {e.reason}")
            error_body = e.read().decode('utf-8')
            print(f"Error body: {error_body}")
            return None
        except Exception as e:
            print(f"Get source candidates error: {e}")
            return None

    def add_source_candidate(self, data, user_data):
        """情報源候補を追加"""
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return None
            
            # 必須フィールドの確認
            if not data.get('name') or not data.get('domain') or not data.get('urls'):
                return None
            
            # source_candidatesテーブル用のデータを準備
            candidate_data = {
                'name': data['name'],
                'domain': data['domain'],
                'urls': data['urls'] if isinstance(data['urls'], list) else [data['urls']],
                'site_url': data.get('site_url', ''),
                'category': data.get('category', 'unknown'),
                'language': data.get('language', 'unknown'),
                'country_code': data.get('country_code', 'unknown'),
                'relevance_score': min(max(float(data.get('relevance_score', 0.0)), 0.0), 1.0),
                'discovery_method': data.get('discovery_method', 'manual'),
                'status': data.get('status', 'pending'),
                'reviewer_notes': data.get('reviewer_notes', ''),
                'discovered_at': datetime.datetime.now().isoformat(),
                'metadata': data.get('metadata', {})
            }
            
            # データベースに追加
            url = f"{supabase_url}/rest/v1/source_candidates"
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json',
                'Prefer': 'return=representation'
            }
            
            req = urllib.request.Request(
                url, 
                data=json.dumps(candidate_data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req) as response:
                response_body = response.read().decode('utf-8')
                if response_body.strip():
                    result = json.loads(response_body)
                    return result[0] if isinstance(result, list) and result else result
                else:
                    return {"success": True, "message": "Source candidate inserted successfully"}
                
        except urllib.error.HTTPError as e:
            print(f"Add source candidate HTTP error: {e.code} - {e.reason}")
            error_body = e.read().decode('utf-8')
            print(f"Error body: {error_body}")
            return None
        except Exception as e:
            print(f"Add source candidate error: {e}")
            return None

    def update_source_candidate(self, candidate_id, data, user_data):
        """情報源候補を更新"""
        try:
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
            if data.get('urls'):
                update_data['urls'] = data['urls'] if isinstance(data['urls'], list) else [data['urls']]
            if data.get('site_url') is not None:
                update_data['site_url'] = data['site_url']
            if data.get('category'):
                update_data['category'] = data['category']
            if data.get('language'):
                update_data['language'] = data['language']
            if data.get('country_code'):
                update_data['country_code'] = data['country_code']
            if data.get('relevance_score') is not None:
                update_data['relevance_score'] = min(max(float(data['relevance_score']), 0.0), 1.0)
            if data.get('discovery_method'):
                update_data['discovery_method'] = data['discovery_method']
            if data.get('status'):
                update_data['status'] = data['status']
                # ステータス変更時にレビュー日時を記録
                if data['status'] in ['approved', 'rejected']:
                    update_data['reviewed_at'] = datetime.datetime.now().isoformat()
            if data.get('reviewer_notes') is not None:
                update_data['reviewer_notes'] = data['reviewer_notes']
            if data.get('metadata') is not None:
                update_data['metadata'] = data['metadata']
            
            # データベースを更新
            url = f"{supabase_url}/rest/v1/source_candidates?id=eq.{candidate_id}"
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
                    return result[0] if isinstance(result, list) and result else result
                else:
                    return {"success": True, "message": "Source candidate updated successfully"}
                    
        except urllib.error.HTTPError as e:
            print(f"Update source candidate HTTP error: {e.code} - {e.reason}")
            error_body = e.read().decode('utf-8')
            print(f"Error body: {error_body}")
            return None
        except Exception as e:
            print(f"Update source candidate error: {e}")
            return None

    def delete_source_candidate(self, candidate_id, user_data):
        """情報源候補を削除"""
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return None
            
            # データベースから物理削除
            url = f"{supabase_url}/rest/v1/source_candidates?id=eq.{candidate_id}"
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
            print(f"Delete source candidate HTTP error: {e.code} - {e.reason}")
            error_body = e.read().decode('utf-8')
            print(f"Error body: {error_body}")
            return None
        except Exception as e:
            print(f"Delete source candidate error: {e}")
            return None