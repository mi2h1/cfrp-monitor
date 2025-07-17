from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            # 環境変数を確認
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            response = {
                "environment_variables": {
                    "SUPABASE_URL": supabase_url[:30] + "..." if supabase_url else "NOT SET",
                    "SUPABASE_KEY": supabase_key[:20] + "..." if supabase_key else "NOT SET"
                }
            }
            
            if not supabase_url or not supabase_key:
                response["error"] = "Environment variables not set properly"
                self.wfile.write(json.dumps(response, indent=2).encode('utf-8'))
                return
            
            # Supabaseに接続テスト
            try:
                url = f"{supabase_url}/rest/v1/users?select=user_id,display_name,role&limit=5"
                headers = {
                    'apikey': supabase_key,
                    'Authorization': f'Bearer {supabase_key}',
                    'Content-Type': 'application/json'
                }
                
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req) as supabase_response:
                    data = json.loads(supabase_response.read().decode('utf-8'))
                    
                    response["supabase_connection"] = "SUCCESS"
                    response["users_found"] = len(data)
                    response["users"] = data
                    
            except urllib.error.HTTPError as e:
                response["supabase_connection"] = "HTTP_ERROR"
                response["error_code"] = e.code
                response["error_message"] = e.reason
                
            except Exception as e:
                response["supabase_connection"] = "CONNECTION_ERROR"
                response["error_message"] = str(e)
                
            # 特定のadminユーザーをテスト
            try:
                url = f"{supabase_url}/rest/v1/users?user_id=eq.admin"
                headers = {
                    'apikey': supabase_key,
                    'Authorization': f'Bearer {supabase_key}',
                    'Content-Type': 'application/json'
                }
                
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req) as supabase_response:
                    admin_data = json.loads(supabase_response.read().decode('utf-8'))
                    
                    response["admin_user"] = {
                        "found": len(admin_data) > 0,
                        "data": admin_data[0] if admin_data else None
                    }
                    
            except Exception as e:
                response["admin_user"] = {
                    "found": False,
                    "error": str(e)
                }
                
        except Exception as e:
            response = {
                "error": "General error",
                "message": str(e)
            }
            
        self.wfile.write(json.dumps(response, indent=2).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()