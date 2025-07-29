from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """デバッグ用：クエリのテスト"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            # クエリパラメータを取得
            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            article_id = query_params.get('article_id', ['ba410f40-5d6c-470c-afc4-671be711b6c0'])[0]
            
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json'
            }
            
            # いくつかのクエリパターンをテスト
            queries = [
                # 1. 基本的なクエリ（全コメント）
                f"{supabase_url}/rest/v1/article_comments",
                
                # 2. article_idフィルタ（引用符なし）
                f"{supabase_url}/rest/v1/article_comments?article_id=eq.{article_id}",
                
                # 3. article_idフィルタ（引用符あり）
                f'{supabase_url}/rest/v1/article_comments?article_id=eq."{article_id}"',
                
                # 4. selectとフィルタ
                f'{supabase_url}/rest/v1/article_comments?select=*&article_id=eq."{article_id}"',
                
                # 5. 完全なクエリ（現在使用中）
                f'{supabase_url}/rest/v1/article_comments?select=*,users(display_name)&article_id=eq."{article_id}"&is_deleted=eq.false&order=created_at.asc'
            ]
            
            results = {}
            
            for i, url in enumerate(queries):
                try:
                    req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req) as response:
                        data = json.loads(response.read().decode('utf-8'))
                        results[f"query_{i+1}"] = {
                            "url": url,
                            "count": len(data) if isinstance(data, list) else 0,
                            "data": data[:2] if isinstance(data, list) else data  # 最初の2件のみ
                        }
                except Exception as e:
                    results[f"query_{i+1}"] = {
                        "url": url,
                        "error": str(e)
                    }
            
            response_data = {
                "success": True,
                "article_id": article_id,
                "results": results
            }
            
            self.wfile.write(json.dumps(response_data, ensure_ascii=False, indent=2).encode('utf-8'))
        
        except Exception as e:
            response = {
                "success": False,
                "error": str(e)
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()