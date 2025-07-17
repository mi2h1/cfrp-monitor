# CFRPモニターシステム フルバックエンド化提案書

## 概要
現在のJavaScriptベースのシステムをPython/Rubyベースのバックエンドに移行し、クライアント側のコード露出を最小限にする実装方法を提案します。

## アーキテクチャ概要

```
[ブラウザ] <-- HTML/最小限のJS --> [バックエンドサーバー] <--> [Supabase DB]
```

## 実装方法

### 1. Python (Flask/FastAPI) を使用した実装

#### 構成
```
cfrp-monitor-backend/
├── app.py                 # メインアプリケーション
├── requirements.txt       # 依存関係
├── config.py             # 設定（環境変数）
├── models/               # データモデル
│   ├── __init__.py
│   ├── user.py
│   ├── article.py
│   └── source.py
├── routes/               # ルーティング
│   ├── __init__.py
│   ├── auth.py          # 認証関連
│   ├── articles.py      # 記事管理
│   ├── sources.py       # 情報源管理
│   └── users.py         # ユーザー管理
├── templates/            # HTMLテンプレート
│   ├── base.html
│   ├── login.html
│   ├── articles.html
│   └── sources.html
└── static/               # 静的ファイル
    ├── css/
    └── js/              # 最小限のJavaScript
```

#### 実装例（Flask）

**app.py**
```python
from flask import Flask, render_template, request, redirect, session, jsonify
from functools import wraps
import os
from supabase import create_client, Client
import hashlib
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Supabase初期化
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_KEY")  # Service keyを使用
supabase: Client = create_client(url, key)

# 認証デコレータ
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session:
                return redirect('/login')
            
            role_hierarchy = {'viewer': 1, 'editor': 2, 'admin': 3}
            if role_hierarchy.get(session.get('role', 'viewer')) < role_hierarchy.get(role, 0):
                return "権限がありません", 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ログイン
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')
        
        # データベースからユーザー取得
        response = supabase.table('users').select("*").eq('user_id', user_id).single().execute()
        
        if response.data:
            user = response.data
            # パスワード検証
            if verify_password(password, user['password_hash'], user['password_salt']):
                session['user_id'] = user['user_id']
                session['display_name'] = user['display_name']
                session['role'] = user['role']
                return redirect('/articles')
        
        return render_template('login.html', error="ログインに失敗しました")
    
    return render_template('login.html')

# 記事一覧
@app.route('/articles')
@login_required
def articles():
    # サーバー側でデータ取得
    response = supabase.table('articles').select("*, sources(*)").order('created_at', desc=True).execute()
    return render_template('articles.html', articles=response.data, user=session)

# 記事追加（AJAX対応）
@app.route('/api/articles', methods=['POST'])
@login_required
def add_article():
    data = request.json
    
    # サーバー側でバリデーション
    if not data.get('url') or not data.get('title'):
        return jsonify({'error': '必須項目が入力されていません'}), 400
    
    # データベースに追加
    article_data = {
        'url': data['url'],
        'title': data['title'],
        'summary': data.get('summary', ''),
        'source_id': data['source_id'],
        'user_id': session['user_id']
    }
    
    response = supabase.table('articles').insert(article_data).execute()
    
    if response.data:
        return jsonify({'success': True, 'data': response.data})
    else:
        return jsonify({'error': '記事の追加に失敗しました'}), 500

# ユーザー管理（管理者のみ）
@app.route('/users')
@login_required
@role_required('admin')
def users():
    response = supabase.table('users').select("*").execute()
    return render_template('users.html', users=response.data, user=session)

def verify_password(password, stored_hash, salt):
    """パスワード検証"""
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return password_hash == stored_hash

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
```

**templates/articles.html**
```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>記事管理</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="container">
        <h1>記事管理</h1>
        <p>ようこそ、{{ user.display_name }}さん</p>
        
        <!-- 記事追加フォーム -->
        <form id="addArticleForm">
            <input type="url" name="url" placeholder="URL" required>
            <input type="text" name="title" placeholder="タイトル" required>
            <textarea name="summary" placeholder="要約"></textarea>
            <select name="source_id">
                {% for source in sources %}
                <option value="{{ source.id }}">{{ source.name }}</option>
                {% endfor %}
            </select>
            <button type="submit">追加</button>
        </form>
        
        <!-- 記事一覧 -->
        <div id="articlesList">
            {% for article in articles %}
            <div class="article">
                <h3>{{ article.title }}</h3>
                <p>{{ article.summary }}</p>
                <a href="{{ article.url }}" target="_blank">記事を読む</a>
            </div>
            {% endfor %}
        </div>
    </div>
    
    <!-- 最小限のJavaScript -->
    <script>
    document.getElementById('addArticleForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData);
        
        const response = await fetch('/api/articles', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            location.reload();
        } else {
            alert('エラーが発生しました');
        }
    });
    </script>
</body>
</html>
```

### 2. Ruby (Sinatra/Rails) を使用した実装

**app.rb (Sinatra)**
```ruby
require 'sinatra'
require 'sinatra/reloader' if development?
require 'json'
require 'net/http'
require 'digest'

enable :sessions
set :session_secret, ENV['SESSION_SECRET'] || SecureRandom.hex(64)

# Supabase設定
SUPABASE_URL = ENV['SUPABASE_URL']
SUPABASE_KEY = ENV['SUPABASE_SERVICE_KEY']

helpers do
  def logged_in?
    !session[:user_id].nil?
  end
  
  def current_user
    session[:user_id]
  end
  
  def require_login
    redirect '/login' unless logged_in?
  end
  
  def require_role(role)
    redirect '/login' unless logged_in?
    
    role_hierarchy = {'viewer' => 1, 'editor' => 2, 'admin' => 3}
    if role_hierarchy[session[:role]] < role_hierarchy[role]
      halt 403, "権限がありません"
    end
  end
  
  def supabase_request(table, method = :get, data = nil, query = {})
    uri = URI("#{SUPABASE_URL}/rest/v1/#{table}")
    uri.query = URI.encode_www_form(query) if query.any?
    
    http = Net::HTTP.new(uri.host, uri.port)
    http.use_ssl = true
    
    request = case method
              when :get then Net::HTTP::Get.new(uri)
              when :post then Net::HTTP::Post.new(uri)
              when :patch then Net::HTTP::Patch.new(uri)
              when :delete then Net::HTTP::Delete.new(uri)
              end
    
    request['apikey'] = SUPABASE_KEY
    request['Authorization'] = "Bearer #{SUPABASE_KEY}"
    request['Content-Type'] = 'application/json'
    request.body = data.to_json if data
    
    response = http.request(request)
    JSON.parse(response.body)
  end
end

# ログイン
get '/login' do
  erb :login
end

post '/login' do
  user_id = params[:user_id]
  password = params[:password]
  
  users = supabase_request('users', :get, nil, {'user_id' => "eq.#{user_id}"})
  
  if users.any?
    user = users.first
    if verify_password(password, user['password_hash'], user['password_salt'])
      session[:user_id] = user['user_id']
      session[:display_name] = user['display_name']
      session[:role] = user['role']
      redirect '/articles'
    end
  end
  
  @error = "ログインに失敗しました"
  erb :login
end

# 記事管理
get '/articles' do
  require_login
  @articles = supabase_request('articles', :get, nil, {
    'select' => '*,sources(*)',
    'order' => 'created_at.desc'
  })
  erb :articles
end

# API: 記事追加
post '/api/articles' do
  require_login
  content_type :json
  
  data = JSON.parse(request.body.read)
  
  article = {
    'url' => data['url'],
    'title' => data['title'],
    'summary' => data['summary'],
    'source_id' => data['source_id'],
    'user_id' => session[:user_id]
  }
  
  result = supabase_request('articles', :post, article)
  
  { success: true, data: result }.to_json
end

def verify_password(password, stored_hash, salt)
  password_hash = Digest::SHA256.hexdigest(password + salt)
  password_hash == stored_hash
end
```

## デプロイ方法

### 1. 無料のホスティングサービス
- **Render** (Python/Ruby対応、無料プランあり)
- **Railway** (簡単デプロイ、無料枠あり)
- **Fly.io** (グローバルデプロイ、無料枠あり)

### 2. VPS/クラウド
- DigitalOcean ($4/月〜)
- Linode ($5/月〜)
- AWS EC2 (t3.micro無料枠)

### 3. GitHub Pagesとの併用
- 静的コンテンツはGitHub Pages
- APIのみバックエンドサーバー

## セキュリティ向上のポイント

1. **コード非公開**
   - ビジネスロジックはすべてサーバー側
   - クライアントには最小限のJavaScriptのみ

2. **データベース接続**
   - Service Role Keyはサーバー側のみ
   - 環境変数で管理

3. **セッション管理**
   - サーバー側セッション
   - CSRF対策
   - セキュアクッキー

4. **API保護**
   - 認証必須
   - レート制限
   - 入力検証

## 移行手順

1. **Phase 1: バックエンドサーバー構築**
   - 基本的な認証機能
   - 記事一覧表示

2. **Phase 2: 機能移行**
   - 記事管理機能
   - 情報源管理機能
   - ユーザー管理機能

3. **Phase 3: フロントエンド最小化**
   - JavaScriptコードの削減
   - サーバーサイドレンダリング

4. **Phase 4: 本番デプロイ**
   - ホスティング環境セットアップ
   - ドメイン設定
   - HTTPS設定

## コスト見積もり
- 開発環境: 無料
- 本番環境: 月額$0〜$5（トラフィック次第）
- ドメイン: 既存のものを使用

この方法なら、現在の使用感を維持しながら、コードの露出を最小限に抑えることができます。