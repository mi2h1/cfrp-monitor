from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.parse
import jwt
import datetime
import sys
sys.path.append('/mnt/f/OneDrive - 株式会社羽生田鉄工所/Git/cfrp-monitor')
from utils.timezone_utils import now_jst_naive_iso, today_jst_iso

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
            
            # クエリパラメータを解析
            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            
            # count_onlyモードのチェック
            if query_params.get('count_only', ['false'])[0].lower() == 'true':
                count = self.get_articles_count(query_params)
                response = {
                    "success": True,
                    "count": count
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # 記事一覧を取得
            articles = self.get_articles(query_params)
            
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
            
            # リクエストボディを取得
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # 記事ID取得（クエリパラメータから）
            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            article_id = query_params.get('id', [None])[0]
            
            if not article_id:
                response = {
                    "success": False,
                    "error": "記事IDが指定されていません"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # 記事更新
            result = self.update_article(article_id, data, user_data)
            
            if result:
                response = {
                    "success": True,
                    "message": "記事を更新しました",
                    "article": result
                }
            else:
                response = {
                    "success": False,
                    "error": "記事の更新に失敗しました"
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
            
            # 記事ID取得（クエリパラメータから）
            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            article_id = query_params.get('id', [None])[0]
            
            if not article_id:
                response = {
                    "success": False,
                    "error": "記事IDが指定されていません"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # 記事削除
            result = self.delete_article(article_id, user_data)
            
            if result:
                response = {
                    "success": True,
                    "message": "記事を削除しました"
                }
            else:
                response = {
                    "success": False,
                    "error": "記事の削除に失敗しました"
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

    def get_articles(self, query_params=None):
        """記事一覧を取得（フィルタリング、ページネーション対応）"""
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return None
            
            if query_params is None:
                query_params = {}
            
            # パラメータを取得
            article_id = query_params.get('id', [None])[0]
            limit = int(query_params.get('limit', ['20'])[0])
            offset = int(query_params.get('offset', ['0'])[0])
            order = query_params.get('order', ['desc'])[0]
            status = query_params.get('status', [None])[0]
            flagged = query_params.get('flagged', [None])[0]
            source_id = query_params.get('source_id', [None])[0]
            has_comments = query_params.get('has_comments', [None])[0]
            
            # 単一記事取得の場合
            if article_id:
                return self.get_single_article(article_id)
            
            # コメントフィルタリングがある場合は、コメント数も含めて取得
            if has_comments:
                # すべての記事を取得してコメント数を計算し、フィルタリング後にページネーション適用
                temp_url = f"{supabase_url}/rest/v1/articles?select=*,sources(name,domain)"
                
                # 基本フィルターを適用
                filters = []
                if status:
                    filters.append(f"status=eq.{status}")
                if flagged is not None:
                    flag_value = 'true' if flagged.lower() == 'true' else 'false'
                    filters.append(f"flagged=eq.{flag_value}")
                if source_id:
                    filters.append(f"source_id=eq.{source_id}")
                
                if filters:
                    temp_url += "&" + "&".join(filters)
                
                # ソート順を適用（記事登録日の降順固定）
                temp_url += f"&order=added_at.desc"
                
                url = temp_url
            else:
                # 通常のページネーション処理
                url = f"{supabase_url}/rest/v1/articles?select=*,sources(name,domain)"
                
                # フィルタリングを追加
                filters = []
                if status:
                    filters.append(f"status=eq.{status}")
                if flagged is not None:
                    flag_value = 'true' if flagged.lower() == 'true' else 'false'
                    filters.append(f"flagged=eq.{flag_value}")
                if source_id:
                    filters.append(f"source_id=eq.{source_id}")
                
                if filters:
                    url += "&" + "&".join(filters)
                
                # ソートとページネーションを追加（記事登録日の降順固定）
                url += f"&order=added_at.desc&limit={limit}&offset={offset}"
            
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json'
            }
            
            print(f"DEBUG: Supabase URL: {url}")
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                # 記事IDのリストを作成
                article_ids = [article['id'] for article in data]
                
                # 一括でコメント数を取得
                if article_ids:
                    comment_counts = self.get_articles_comment_counts(article_ids)
                    # 各記事にコメント数を追加
                    for article in data:
                        article['comment_count'] = comment_counts.get(article['id'], 0)
                
                # コメントフィルタリングを適用
                if has_comments:
                    if has_comments == 'with_comments':
                        filtered_data = [article for article in data if article.get('comment_count', 0) > 0]
                    elif has_comments == 'no_comments':
                        filtered_data = [article for article in data if article.get('comment_count', 0) == 0]
                    else:
                        filtered_data = data
                    
                    # フィルタリング後にページネーションを適用
                    start_idx = offset
                    end_idx = offset + limit
                    data = filtered_data[start_idx:end_idx]
                
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

    def get_single_article(self, article_id):
        """単一記事を取得"""
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return None
            
            # 単一記事を取得（ai_summaryフィールドも含める）
            url = f"{supabase_url}/rest/v1/articles?select=*,sources(name,domain)&id=eq.{article_id}"
            
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json'
            }
            
            print(f"DEBUG: Single article URL: {url}")
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                if data:
                    # コメント数を取得
                    comment_counts = self.get_articles_comment_counts([article_id])
                    data[0]['comment_count'] = comment_counts.get(article_id, 0)
                    
                    print(f"DEBUG: Single article found: {data[0].get('title', 'No title')}")
                    return data
                else:
                    print(f"DEBUG: No article found with id: {article_id}")
                    return []
                
        except urllib.error.HTTPError as e:
            print(f"Get single article HTTP error: {e.code} - {e.reason}")
            error_body = e.read().decode('utf-8')
            print(f"Error body: {error_body}")
            return None
        except Exception as e:
            print(f"Get single article error: {e}")
            return None
    
    def get_articles_comment_counts(self, article_ids):
        """複数記事のコメント数を一括取得"""
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return {}
            
            # 記事IDのリストをカンマ区切りの文字列に変換
            ids_str = ','.join(f'"{id}"' for id in article_ids)
            
            # 一括でコメントデータを取得（削除されていないもののみ）
            url = f"{supabase_url}/rest/v1/article_comments?article_id=in.({ids_str})&is_deleted=eq.false&select=article_id"
            
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json'
            }
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                comments = json.loads(response.read().decode('utf-8'))
                
                # 記事IDごとのコメント数を集計
                comment_counts = {}
                for comment in comments:
                    article_id = comment['article_id']
                    comment_counts[article_id] = comment_counts.get(article_id, 0) + 1
                
                # 全ての記事IDに対して結果を返す（コメントがない記事は0）
                result = {}
                for article_id in article_ids:
                    result[article_id] = comment_counts.get(article_id, 0)
                
                return result
        
        except Exception as e:
            print(f"Get comments count error: {str(e)}")
            return {}
    
    def get_articles_count(self, query_params=None):
        """記事の総数を取得（フィルタリング対応）"""
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return 0
            
            if query_params is None:
                query_params = {}
            
            # パラメータを取得
            status = query_params.get('status', [None])[0]
            flagged = query_params.get('flagged', [None])[0]
            source_id = query_params.get('source_id', [None])[0]
            has_comments = query_params.get('has_comments', [None])[0]
            
            # ベースURLを構築（カウントのみ）
            url = f"{supabase_url}/rest/v1/articles?select=id"
            
            # フィルタリングを追加
            filters = []
            if status:
                filters.append(f"status=eq.{status}")
            if flagged is not None:
                flag_value = 'true' if flagged.lower() == 'true' else 'false'
                filters.append(f"flagged=eq.{flag_value}")
            if source_id:
                filters.append(f"source_id=eq.{source_id}")
            
            if filters:
                url += "&" + "&".join(filters)
            
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json',
                'Prefer': 'count=exact'
            }
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                # コメントフィルタリングがある場合は、データを取得してフィルタリング後にカウント
                if has_comments:
                    # 記事とコメント数を取得
                    articles_data = json.loads(response.read().decode('utf-8'))
                    article_ids = [article['id'] for article in articles_data]
                    
                    if article_ids:
                        comment_counts = self.get_articles_comment_counts(article_ids)
                        # フィルタリング適用
                        if has_comments == 'with_comments':
                            filtered_count = sum(1 for article_id in article_ids if comment_counts.get(article_id, 0) > 0)
                        elif has_comments == 'no_comments':
                            filtered_count = sum(1 for article_id in article_ids if comment_counts.get(article_id, 0) == 0)
                        else:
                            filtered_count = len(articles_data)
                        return filtered_count
                    else:
                        return 0
                else:
                    # Content-Rangeヘッダーからカウントを取得
                    content_range = response.headers.get('Content-Range', '')
                    if content_range and '/' in content_range:
                        count = int(content_range.split('/')[-1])
                        return count
                    else:
                        # フォールバック: データを取得してカウント
                        data = json.loads(response.read().decode('utf-8'))
                        return len(data)
                
        except Exception as e:
            print(f"Get articles count error: {e}")
            return 0

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
            
            # articlesテーブル用のデータを準備
            item_data = {
                'url': data['url'],
                'title': data['title'],
                'body': data.get('body', ''),
                'source_id': data.get('source_id'),
                'last_edited_by': user_data['user_id'],
                'src_type': data.get('src_type', 'manual'),
                'status': 'unread',
                'published_at': data.get('published_at', today_jst_iso())
            }
            
            print(f"DEBUG: Item data to insert: {item_data}")
            
            # データベースに追加
            url = f"{supabase_url}/rest/v1/articles"
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json',
                'Prefer': 'return=representation'
            }
            
            print(f"DEBUG: Supabase URL: {url}")
            
            req = urllib.request.Request(
                url, 
                data=json.dumps(item_data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req) as response:
                response_body = response.read().decode('utf-8')
                print(f"DEBUG: Response body: {response_body}")
                print(f"DEBUG: Response status: {response.getcode()}")
                
                if response_body.strip():
                    result = json.loads(response_body)
                    print(f"DEBUG: Insert result: {result}")
                    return result[0] if isinstance(result, list) and result else result
                else:
                    print("DEBUG: Empty response from Supabase")
                    return {"success": True, "message": "Item inserted successfully"}
                
        except urllib.error.HTTPError as e:
            print(f"Add article HTTP error: {e.code} - {e.reason}")
            error_body = e.read().decode('utf-8')
            print(f"Error body: {error_body}")
            return None
        except Exception as e:
            print(f"Add article error: {e}")
            return None

    def update_article(self, article_id, data, user_data):
        """記事を更新"""
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return None
            
            # 更新データを準備
            update_data = {}
            if data.get('title'):
                update_data['title'] = data['title']
            if data.get('body') is not None:
                update_data['body'] = data['body']
            if data.get('url'):
                update_data['url'] = data['url']
            if data.get('source_id'):
                update_data['source_id'] = data['source_id']
            if data.get('status'):
                update_data['status'] = data['status']
            if data.get('flagged') is not None:
                update_data['flagged'] = data['flagged']
            if 'comments' in data:
                update_data['comments'] = data['comments'] if data['comments'] else None
            
            # 更新者情報を追加
            update_data['last_edited_by'] = user_data['user_id']
            update_data['reviewed_at'] = now_jst_naive_iso()
            update_data['reviewer'] = user_data['user_id']
            
            # データベースを更新
            url = f"{supabase_url}/rest/v1/articles?id=eq.{article_id}"
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
                    return {"success": True, "message": "Item updated successfully"}
                    
        except urllib.error.HTTPError as e:
            print(f"Update article HTTP error: {e.code} - {e.reason}")
            error_body = e.read().decode('utf-8')
            print(f"Error body: {error_body}")
            return None
        except Exception as e:
            print(f"Update article error: {e}")
            return None

    def delete_article(self, article_id, user_data):
        """記事を削除"""
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return None
            
            # データベースから削除
            url = f"{supabase_url}/rest/v1/articles?id=eq.{article_id}"
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
            print(f"Delete article HTTP error: {e.code} - {e.reason}")
            error_body = e.read().decode('utf-8')
            print(f"Error body: {error_body}")
            return None
        except Exception as e:
            print(f"Delete article error: {e}")
            return None
    
    def update_ai_summary(self, article_id, ai_summary, user_data):
        """記事のAI要約を更新"""
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return None
            
            # AI要約データを準備
            update_data = {
                'ai_summary': ai_summary,
                'last_edited_by': user_data['user_id'],
                'reviewed_at': now_jst_naive_iso()
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
                print(f"DEBUG: AI summary updated for article {article_id}")
                return result[0] if isinstance(result, list) and result else result
                    
        except urllib.error.HTTPError as e:
            print(f"Update AI summary HTTP error: {e.code} - {e.reason}")
            error_body = e.read().decode('utf-8')
            print(f"Error body: {error_body}")
            return None
        except Exception as e:
            print(f"Update AI summary error: {e}")
            return None