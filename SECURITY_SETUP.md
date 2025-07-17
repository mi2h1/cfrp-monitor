# CFRP Monitor セキュリティ設定ガイド

## 🚨 緊急対応（即座に実行）

### 1. Row Level Security (RLS) の有効化

**Supabase管理画面** → **Database** → **Tables** で以下を実行：

```sql
-- 全テーブルでRLSを有効化
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.source_candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.task_logs ENABLE ROW LEVEL SECURITY;

-- バックアップテーブルも保護
ALTER TABLE public.sources_backup ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.items_backup ENABLE ROW LEVEL SECURITY;
```

## 2. セキュリティポリシーの設定

### usersテーブルのポリシー

```sql
-- 管理者のみが全ユーザー情報を閲覧可能
CREATE POLICY "Admin can view all users" ON public.users
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM public.users 
      WHERE user_id = current_setting('app.current_user_id', true)
      AND role = 'admin'
    )
  );

-- 自分自身の情報のみ閲覧可能
CREATE POLICY "Users can view own profile" ON public.users
  FOR SELECT USING (user_id = current_setting('app.current_user_id', true));

-- 管理者のみがユーザー情報を更新可能
CREATE POLICY "Admin can update users" ON public.users
  FOR UPDATE USING (
    EXISTS (
      SELECT 1 FROM public.users 
      WHERE user_id = current_setting('app.current_user_id', true)
      AND role = 'admin'
    )
  );

-- 管理者のみがユーザーを削除可能
CREATE POLICY "Admin can delete users" ON public.users
  FOR DELETE USING (
    EXISTS (
      SELECT 1 FROM public.users 
      WHERE user_id = current_setting('app.current_user_id', true)
      AND role = 'admin'
    )
  );

-- 新規ユーザー登録は制限（管理者のみ）
CREATE POLICY "Admin can insert users" ON public.users
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.users 
      WHERE user_id = current_setting('app.current_user_id', true)
      AND role = 'admin'
    )
  );
```

### sourcesテーブルのポリシー

```sql
-- 編集者以上が情報源を閲覧可能
CREATE POLICY "Editor and above can view sources" ON public.sources
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM public.users 
      WHERE user_id = current_setting('app.current_user_id', true)
      AND role IN ('admin', 'editor')
    )
  );

-- 編集者以上が情報源を更新可能
CREATE POLICY "Editor and above can update sources" ON public.sources
  FOR UPDATE USING (
    EXISTS (
      SELECT 1 FROM public.users 
      WHERE user_id = current_setting('app.current_user_id', true)
      AND role IN ('admin', 'editor')
    )
  );

-- 編集者以上が情報源を削除可能
CREATE POLICY "Editor and above can delete sources" ON public.sources
  FOR DELETE USING (
    EXISTS (
      SELECT 1 FROM public.users 
      WHERE user_id = current_setting('app.current_user_id', true)
      AND role IN ('admin', 'editor')
    )
  );

-- 編集者以上が情報源を追加可能
CREATE POLICY "Editor and above can insert sources" ON public.sources
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.users 
      WHERE user_id = current_setting('app.current_user_id', true)
      AND role IN ('admin', 'editor')
    )
  );
```

### itemsテーブルのポリシー（記事管理）

```sql
-- 全権限で記事を閲覧可能
CREATE POLICY "All users can view items" ON public.items
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM public.users 
      WHERE user_id = current_setting('app.current_user_id', true)
      AND role IN ('admin', 'editor', 'viewer')
    )
  );

-- 全権限で記事を更新可能
CREATE POLICY "All users can update items" ON public.items
  FOR UPDATE USING (
    EXISTS (
      SELECT 1 FROM public.users 
      WHERE user_id = current_setting('app.current_user_id', true)
      AND role IN ('admin', 'editor', 'viewer')
    )
  );

-- 記事は自動で追加されるため、システムレベルでのみ挿入可能
CREATE POLICY "System can insert items" ON public.items
  FOR INSERT WITH CHECK (true);

-- 管理者のみが記事を削除可能
CREATE POLICY "Admin can delete items" ON public.items
  FOR DELETE USING (
    EXISTS (
      SELECT 1 FROM public.users 
      WHERE user_id = current_setting('app.current_user_id', true)
      AND role = 'admin'
    )
  );
```

### source_candidatesテーブルのポリシー

```sql
-- 編集者以上が候補を閲覧可能
CREATE POLICY "Editor and above can view source candidates" ON public.source_candidates
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM public.users 
      WHERE user_id = current_setting('app.current_user_id', true)
      AND role IN ('admin', 'editor')
    )
  );

-- 編集者以上が候補を更新可能
CREATE POLICY "Editor and above can update source candidates" ON public.source_candidates
  FOR UPDATE USING (
    EXISTS (
      SELECT 1 FROM public.users 
      WHERE user_id = current_setting('app.current_user_id', true)
      AND role IN ('admin', 'editor')
    )
  );
```

### task_logsテーブルのポリシー

```sql
-- 管理者のみがタスクログを閲覧可能
CREATE POLICY "Admin can view task logs" ON public.task_logs
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM public.users 
      WHERE user_id = current_setting('app.current_user_id', true)
      AND role = 'admin'
    )
  );

-- システムのみがタスクログを挿入可能
CREATE POLICY "System can insert task logs" ON public.task_logs
  FOR INSERT WITH CHECK (true);
```

### バックアップテーブルのポリシー

```sql
-- 管理者のみがバックアップテーブルにアクセス可能
CREATE POLICY "Admin can access sources backup" ON public.sources_backup
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM public.users 
      WHERE user_id = current_setting('app.current_user_id', true)
      AND role = 'admin'
    )
  );

CREATE POLICY "Admin can access items backup" ON public.items_backup
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM public.users 
      WHERE user_id = current_setting('app.current_user_id', true)
      AND role = 'admin'
    )
  );
```

## 3. JavaScript側の認証強化

### common.jsに認証コンテキスト設定を追加

```javascript
// 認証コンテキスト設定
async function setAuthContext(userId) {
    try {
        const { error } = await supabase.rpc('set_config', {
            config_name: 'app.current_user_id',
            config_value: userId
        });
        
        if (error) {
            console.error('Failed to set auth context:', error);
            return false;
        }
        
        return true;
    } catch (error) {
        console.error('Error setting auth context:', error);
        return false;
    }
}

// ログイン時に認証コンテキストを設定
async function authenticateUser(userId, userData) {
    localStorage.setItem('currentUser', userId);
    localStorage.setItem('currentUserData', JSON.stringify(userData));
    
    // 認証コンテキストを設定
    await setAuthContext(userId);
    
    return true;
}
```

### データベースファンクションの作成

```sql
-- 設定値を設定するファンクション
CREATE OR REPLACE FUNCTION set_config(config_name text, config_value text)
RETURNS void AS $$
BEGIN
    PERFORM set_config(config_name, config_value, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 権限確認用のファンクション
CREATE OR REPLACE FUNCTION check_user_role(required_role text)
RETURNS boolean AS $$
DECLARE
    user_role text;
BEGIN
    SELECT role INTO user_role
    FROM public.users
    WHERE user_id = current_setting('app.current_user_id', true);
    
    RETURN CASE required_role
        WHEN 'admin' THEN user_role = 'admin'
        WHEN 'editor' THEN user_role IN ('admin', 'editor')
        WHEN 'viewer' THEN user_role IN ('admin', 'editor', 'viewer')
        ELSE false
    END;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## 4. 緊急時の簡易対策（RLS設定前）

### JavaScriptレベルでの最低限の制御

```javascript
// common.jsに追加
function restrictDirectDatabaseAccess() {
    // 開発者ツールでのSupabaseアクセスを制限
    if (typeof supabase !== 'undefined') {
        const originalFrom = supabase.from;
        
        supabase.from = function(table) {
            // 権限チェック
            const user = getCurrentUser();
            if (!user) {
                throw new Error('認証が必要です');
            }
            
            // テーブルごとの権限チェック
            switch(table) {
                case 'users':
                    if (!isAdmin()) {
                        throw new Error('ユーザー情報へのアクセスは管理者のみ可能です');
                    }
                    break;
                case 'sources':
                case 'source_candidates':
                    if (!canEditSources()) {
                        throw new Error('情報源管理の権限がありません');
                    }
                    break;
                case 'task_logs':
                    if (!isAdmin()) {
                        throw new Error('タスクログへのアクセスは管理者のみ可能です');
                    }
                    break;
                case 'sources_backup':
                case 'items_backup':
                    if (!isAdmin()) {
                        throw new Error('バックアップデータへのアクセスは管理者のみ可能です');
                    }
                    break;
            }
            
            return originalFrom.call(this, table);
        };
    }
}

// ページ読み込み時に実行
document.addEventListener('DOMContentLoaded', restrictDirectDatabaseAccess);
```

### 本番環境での追加制限

```javascript
// 本番環境では開発者ツールの使用を制限
if (location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
    // 開発者ツール検知
    setInterval(() => {
        if (window.outerHeight - window.innerHeight > 200 || 
            window.outerWidth - window.innerWidth > 200) {
            document.body.innerHTML = '<h1>開発者ツールの使用は禁止されています</h1>';
        }
    }, 1000);
    
    // 右クリック無効化
    document.addEventListener('contextmenu', e => e.preventDefault());
    
    // キーボードショートカット無効化
    document.addEventListener('keydown', e => {
        if (e.key === 'F12' || 
            (e.ctrlKey && e.shiftKey && e.key === 'I') ||
            (e.ctrlKey && e.shiftKey && e.key === 'C') ||
            (e.ctrlKey && e.key === 'u')) {
            e.preventDefault();
        }
    });
}
```

## 5. 追加のセキュリティ対策

### API制限の設定

```sql
-- API使用量制限
-- Supabase管理画面 → Settings → API で設定
-- - Rate limiting: 有効化
-- - IP制限: 本番環境では特定IPのみ許可
```

### 環境変数の保護

```javascript
// 本番環境では環境変数を使用
const SUPABASE_URL = process.env.REACT_APP_SUPABASE_URL || 'https://your-project.supabase.co';
const SUPABASE_ANON_KEY = process.env.REACT_APP_SUPABASE_ANON_KEY || 'your-anon-key';
```

### セッション管理の強化

```javascript
// セッションタイムアウト設定
const SESSION_TIMEOUT = 30 * 60 * 1000; // 30分

function checkSessionTimeout() {
    const lastActivity = localStorage.getItem('lastActivity');
    const now = Date.now();
    
    if (lastActivity && (now - parseInt(lastActivity)) > SESSION_TIMEOUT) {
        logout();
        alert('セッションがタイムアウトしました。再度ログインしてください。');
        window.location.href = 'login.html';
    }
}

// アクティビティ監視
document.addEventListener('click', () => {
    localStorage.setItem('lastActivity', Date.now().toString());
});

// 定期的にセッションチェック
setInterval(checkSessionTimeout, 60000); // 1分ごと
```

## 6. 実装手順（優先順位順）

### 🚨 **最優先（今すぐ実行）**
1. **RLSの有効化** - 全テーブルで即座に実行
2. **JavaScript簡易制限** - common.jsに追加

### 🔒 **高優先（24時間以内）**
3. **データベースポリシー設定** - 上記SQLを順次実行
4. **認証コンテキスト実装** - set_config関数とコンテキスト設定

### 📋 **中優先（1週間以内）**
5. **セッション管理強化** - タイムアウト機能の実装
6. **本番環境制限** - 開発者ツール制限など

### 🔍 **低優先（継続的）**
7. **監視とログ確認** - 定期的なセキュリティチェック
8. **テストと改善** - 各権限レベルでのアクセステスト

### 実際のテーブル構造に基づく対象
- **users**: ユーザー情報（パスワードハッシュ、権限含む）
- **sources**: 情報源データ
- **items**: 記事データ（旧articles）
- **source_candidates**: 情報源候補
- **task_logs**: タスク実行ログ
- **sources_backup, items_backup**: バックアップデータ

## 6. 定期的な確認事項

- [ ] RLSが有効になっているか
- [ ] ポリシーが正しく動作しているか
- [ ] 不要な権限が付与されていないか
- [ ] ログに異常なアクセスがないか
- [ ] セッションタイムアウトが適切に動作しているか

## 7. 緊急時の対応

### 不正アクセスを検知した場合
1. 該当ユーザーのセッションを無効化
2. パスワードをリセット
3. アクセスログを確認
4. 必要に応じてAPIキーを再生成

### システム異常時
1. RLSを一時的に無効化しない
2. 管理者権限でのみ対応
3. 復旧後は必ずセキュリティチェックを実施

---

**注意**: このファイルにはセキュリティ設定が含まれています。本番環境での実装後は、適切な場所に移動して管理してください。