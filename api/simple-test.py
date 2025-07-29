from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """シンプルなテスト"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json'
            }
            
            # 記事IDを固定
            article_id = 'ba410f40-5d6c-470c-afc4-671be711b6c0'
            
            # 複数のクエリパターンを試す
            queries = []
            
            # 1. シンプルなクエリ
            url1 = f'{supabase_url}/rest/v1/article_comments?article_id=eq.{article_id}'
            queries.append(('Simple query', url1))
            
            # 2. select付き
            url2 = f'{supabase_url}/rest/v1/article_comments?select=*&article_id=eq.{article_id}'
            queries.append(('With select', url2))
            
            # 3. JOINなし、削除フラグ付き
            url3 = f'{supabase_url}/rest/v1/article_comments?select=*&article_id=eq.{article_id}&is_deleted=eq.false'
            queries.append(('With is_deleted', url3))
            
            # 4. JOINあり
            url4 = f'{supabase_url}/rest/v1/article_comments?select=*,users(display_name)&article_id=eq.{article_id}'
            queries.append(('With JOIN', url4))
            
            # 5. 完全なクエリ（現在使用中）
            url5 = f'{supabase_url}/rest/v1/article_comments?select=*,users(display_name)&article_id=eq.{article_id}&is_deleted=eq.false&order=created_at.asc'
            queries.append(('Full query', url5))
            
            results = []
            
            for name, url in queries:
                try:
                    req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req) as response:
                        data = json.loads(response.read().decode('utf-8'))
                        results.append({
                            'name': name,
                            'url': url,
                            'status': 'success',
                            'count': len(data) if isinstance(data, list) else 0,
                            'sample': data[0] if data and isinstance(data, list) else None
                        })
                except Exception as e:
                    results.append({
                        'name': name,
                        'url': url,
                        'status': 'error',
                        'error': str(e)
                    })
            
            response_data = {
                'success': True,
                'results': results
            }
            
            self.wfile.write(json.dumps(response_data, ensure_ascii=False, indent=2).encode('utf-8'))
        
        except Exception as e:
            response = {
                'success': False,
                'error': str(e)
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()