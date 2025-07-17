# Vercel セットアップガイド（CFRPモニター用）

## 1. Vercelで最初にやること

### GitHub連携
1. Vercelダッシュボード（https://vercel.com/dashboard）にアクセス
2. 「Add New...」→「Project」をクリック
3. 「Import Git Repository」で GitHubアカウントを連携
4. `cfrp-monitor` リポジトリを選択

## 2. 最小限の動作確認から始める

まず、シンプルなAPIを1つ作って動作確認しましょう。

### ステップ1: テスト用APIファイルを作成

**api/hello.py**
```python
from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "message": "Hello from Python on Vercel!",
            "status": "working"
        }
        
        self.wfile.write(json.dumps(response).encode())
```

### ステップ2: Vercel設定ファイル

**vercel.json**
```json
{
  "functions": {
    "api/*.py": {
      "runtime": "python3.9"
    }
  }
}
```

### ステップ3: ディレクトリ構造
```
cfrp-monitor/
├── api/
│   └── hello.py      # ここに作成
├── docs/             # 既存のファイル
│   ├── index.html
│   └── ...
└── vercel.json       # ここに作成
```

## 3. デプロイ方法

### 方法A: Git Push（推奨）
```bash
git add api/hello.py vercel.json
git commit -m "Add Vercel API test"
git push
```

Vercelが自動的にデプロイを開始します。

### 方法B: Vercel CLI
```bash
# インストール
npm i -g vercel

# デプロイ
vercel --prod
```

## 4. 動作確認

デプロイ後、以下のURLでアクセスできます：
- `https://あなたのプロジェクト名.vercel.app/api/hello`

## 5. 本格的な実装に向けて

### 認証API の例

**api/auth.py**
```python
from http.server import BaseHTTPRequestHandler
import json
import os
from urllib.parse import parse_qs

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # CORSヘッダー
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # リクエストボディを取得
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        # ここに認証ロジックを実装
        # 今は仮実装
        if data.get('user_id') == 'admin' and data.get('password') == 'password':
            response = {
                "success": True,
                "token": "dummy-token-12345",
                "user": {
                    "user_id": "admin",
                    "display_name": "管理者",
                    "role": "admin"
                }
            }
        else:
            response = {
                "success": False,
                "error": "認証に失敗しました"
            }
        
        self.wfile.write(json.dumps(response).encode())
    
    def do_OPTIONS(self):
        # CORS プリフライト対応
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
```

### フロントエンドからの呼び出し

**docs/assets/js/login.js を修正**
```javascript
async function login() {
    const userId = document.getElementById('userId').value;
    const password = document.getElementById('password').value;
    
    try {
        const response = await fetch('/api/auth', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            localStorage.setItem('token', data.token);
            localStorage.setItem('user', JSON.stringify(data.user));
            window.location.href = '/articles.html';
        } else {
            alert(data.error);
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('ログインエラーが発生しました');
    }
}
```

## 6. 環境変数の設定

1. Vercelダッシュボード → プロジェクト → Settings → Environment Variables
2. 以下を追加：
   - `SUPABASE_URL`: あなたのSupabase URL
   - `SUPABASE_KEY`: あなたのSupabase Service Role Key
   - `SECRET_KEY`: ランダムな文字列

## 7. トラブルシューティング

### よくある問題

**Q: 404 Not Found**
A: `vercel.json` の設定を確認。`api/` ディレクトリ内にファイルがあるか確認。

**Q: 500 Internal Server Error**
A: Vercelダッシュボードの Functions タブでエラーログを確認。

**Q: CORS エラー**
A: API側で適切なCORSヘッダーを返しているか確認。

## 次のステップ

1. まず `hello.py` で動作確認
2. `auth.py` で認証APIを実装
3. 徐々に他のAPIも移行

この手順で進めれば、少しずつVercelに慣れていけます！