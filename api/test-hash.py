from http.server import BaseHTTPRequestHandler
import json
import hashlib

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # テスト用のsaltとpassword
        password = "password"
        salt = "bef30d515e159345a835adb59adaf255"
        stored_hash = "7fc133a72c74f300943ed52530892a65e4b9355601882df69fe8a917c985a6b1"
        
        # 様々なハッシュ化方法をテスト
        test_results = []
        
        # 1. password + salt
        hash1 = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
        test_results.append({
            "method": "password + salt",
            "input": f"'{password}' + '{salt}'",
            "result": hash1,
            "match": hash1 == stored_hash
        })
        
        # 2. salt + password
        hash2 = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
        test_results.append({
            "method": "salt + password", 
            "input": f"'{salt}' + '{password}'",
            "result": hash2,
            "match": hash2 == stored_hash
        })
        
        # 3. password (plain)
        hash3 = hashlib.sha256(password.encode('utf-8')).hexdigest()
        test_results.append({
            "method": "password only",
            "input": f"'{password}'",
            "result": hash3,
            "match": hash3 == stored_hash
        })
        
        # 4. JavaScript風のハッシュ化をシミュレート
        hash4 = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
        test_results.append({
            "method": "JavaScript style",
            "input": f"'{password}' + '{salt}' (UTF-8)",
            "result": hash4,
            "match": hash4 == stored_hash
        })
        
        response = {
            "stored_hash": stored_hash,
            "test_results": test_results,
            "matching_method": next((r["method"] for r in test_results if r["match"]), "None found")
        }
        
        self.wfile.write(json.dumps(response, indent=2).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()