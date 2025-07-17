from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                response = {"error": "Environment variables not set"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # 利用可能なテーブルを確認
            tables_info = {}
            
            # 既知のテーブル名を試す
            test_tables = ['articles', 'users', 'sources', 'task_logs', 'article_candidates']
            
            for table in test_tables:
                try:
                    url = f"{supabase_url}/rest/v1/{table}?select=*&limit=1"
                    headers = {
                        'apikey': supabase_key,
                        'Authorization': f'Bearer {supabase_key}',
                        'Content-Type': 'application/json'
                    }
                    
                    req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req) as response_obj:
                        data = json.loads(response_obj.read().decode('utf-8'))
                        tables_info[table] = {
                            "exists": True,
                            "sample_count": len(data),
                            "sample_data": data[:1] if data else []
                        }
                        
                except urllib.error.HTTPError as e:
                    error_body = e.read().decode('utf-8')
                    tables_info[table] = {
                        "exists": False,
                        "error": f"{e.code} - {e.reason}",
                        "details": error_body
                    }
                except Exception as e:
                    tables_info[table] = {
                        "exists": False,
                        "error": str(e)
                    }
            
            response = {
                "supabase_url": supabase_url,
                "tables": tables_info
            }
            
            self.wfile.write(json.dumps(response, indent=2).encode('utf-8'))
            
        except Exception as e:
            response = {"error": str(e)}
            self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()