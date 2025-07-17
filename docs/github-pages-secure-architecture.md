# GitHub Pages + バックエンドAPI構成提案

## 概要
GitHub Pagesの制約を考慮し、静的サイトとバックエンドAPIを組み合わせた構成を提案します。

## アーキテクチャ

```
[GitHub Pages] <-- API通信 --> [バックエンドAPI] <--> [Supabase DB]
（静的HTML/JS）                 （Python/Ruby）
```

## 実装パターン

### パターン1: GitHub Pages + 無料APIホスティング

**フロントエンド（GitHub Pages）**
- 静的HTML
- 最小限のJavaScript（API呼び出しのみ）
- ビルド済みのCSS/画像

**バックエンドAPI（別ホスティング）**
- **Vercel Functions**（Node.js/Python、無料枠あり）
- **Netlify Functions**（Node.js、無料枠あり）
- **Cloudflare Workers**（JavaScript、無料枠あり）
- **Deno Deploy**（TypeScript/JavaScript、無料）

### パターン2: Supabase Edge Functions活用

GitHub PagesとSupabase Edge Functionsの組み合わせ：

```typescript
// Supabase Edge Function例
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': 'https://yourusername.github.io',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // CORS対応
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  const { action, data } = await req.json()

  switch (action) {
    case 'login':
      // 認証処理
      return handleLogin(data)
    case 'getArticles':
      // 記事取得（認証チェック付き）
      return handleGetArticles(req.headers.get('Authorization'))
    case 'addArticle':
      // 記事追加
      return handleAddArticle(data, req.headers.get('Authorization'))
  }
})
```

### パターン3: 静的サイトジェネレーター + 認証

**Jekyll（GitHub Pages標準）でのプライベートコンテンツ実装：**

```javascript
// _includes/auth.js
class SecureApp {
  constructor() {
    this.apiUrl = 'https://your-api.supabase.co/functions/v1/';
    this.token = localStorage.getItem('auth_token');
  }

  async login(userId, password) {
    const response = await fetch(this.apiUrl + 'auth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'login', userId, password })
    });
    
    if (response.ok) {
      const { token } = await response.json();
      this.token = token;
      localStorage.setItem('auth_token', token);
      this.showSecureContent();
    }
  }

  async showSecureContent() {
    // トークン検証後にコンテンツ表示
    const content = await this.fetchSecureData();
    document.getElementById('secure-content').innerHTML = content;
  }

  async fetchSecureData() {
    const response = await fetch(this.apiUrl + 'data', {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    return response.json();
  }
}
```

### パターン4: GitHub Actions + プライベートビルド

GitHub Actionsでビルド時にデータを取得し、静的ファイルを生成：

```yaml
# .github/workflows/build.yml
name: Build Secure Site
on:
  schedule:
    - cron: '0 */6 * * *'  # 6時間ごと
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Fetch Data from Supabase
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
        run: |
          python scripts/fetch_data.py
          
      - name: Build Static Site
        run: |
          python scripts/build_site.py
          
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./dist
```

## セキュリティ対策

### 1. 最小限のクライアントコード
```javascript
// public/app.js - 公開されるコード
const API_URL = 'https://your-backend.com/api';

async function callAPI(endpoint, data) {
  const token = localStorage.getItem('token');
  return fetch(`${API_URL}/${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    },
    body: JSON.stringify(data)
  });
}

// ビジネスロジックは一切含まない
document.getElementById('loginForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const response = await callAPI('login', {
    userId: e.target.userId.value,
    password: e.target.password.value
  });
  if (response.ok) {
    const { token } = await response.json();
    localStorage.setItem('token', token);
    window.location.href = '/dashboard';
  }
});
```

### 2. バックエンドでの処理
すべての重要な処理はバックエンドで実行：
- 認証・認可
- データ検証
- ビジネスロジック
- データベースアクセス

### 3. CORS設定
特定のGitHub Pagesドメインからのみアクセス許可

## 推奨構成

**GitHub Pages（無料） + Supabase Edge Functions（無料枠）**

メリット：
- 完全無料で運用可能
- 既存のSupabaseアカウントで完結
- セキュリティ向上
- スケーラビリティ確保

デメリット：
- 若干のレイテンシ
- Edge Functionsの学習コスト

この構成なら、GitHub Pagesの制約内で、セキュアなシステムを実現できます。