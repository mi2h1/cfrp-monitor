from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """テスト用：記事のコメントを直接取得"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            # 全コメントを取得（削除フラグ関係なく）
            url = f"{supabase_url}/rest/v1/article_comments?select=*"
            
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json'
            }
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                response_data = {
                    "success": True,
                    "total_comments": len(data),
                    "comments": data,
                    "comment_summary": {}
                }
                
                # article_id毎のコメント数を集計
                for comment in data:
                    article_id = comment.get('article_id', 'unknown')
                    if article_id not in response_data["comment_summary"]:
                        response_data["comment_summary"][article_id] = {
                            "total": 0,
                            "deleted": 0,
                            "active": 0
                        }
                    
                    response_data["comment_summary"][article_id]["total"] += 1
                    if comment.get('is_deleted'):
                        response_data["comment_summary"][article_id]["deleted"] += 1
                    else:
                        response_data["comment_summary"][article_id]["active"] += 1
                
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
        
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