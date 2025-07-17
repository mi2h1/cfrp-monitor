# CFRP Monitor セキュリティ設定ガイド

## 🚨 緊急対応（即座に実行）

### 1. Row Level Security (RLS) の有効化

**Supabase管理画面** → **Database** → **Tables** で以下を実行：

```sql
-- 全テーブルでRLSを有効化
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.source_candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.task_logs ENABLE ROW LEVEL SECURITY;
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

### articlesテーブルのポリシー

```sql
-- 全権限で記事を閲覧可能
CREATE POLICY "All users can view articles" ON public.articles
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM public.users 
      WHERE user_id = current_setting('app.current_user_id', true)
      AND role IN ('admin', 'editor', 'viewer')
    )
  );

-- 全権限で記事を更新可能
CREATE POLICY "All users can update articles" ON public.articles
  FOR UPDATE USING (
    EXISTS (
      SELECT 1 FROM public.users 
      WHERE user_id = current_setting('app.current_user_id', true)
      AND role IN ('admin', 'editor', 'viewer')
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

## 4. 追加のセキュリティ対策

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

## 5. 実装手順

1. **即座に実行**: RLSの有効化
2. **ポリシー設定**: 上記SQLを順次実行
3. **JavaScript更新**: 認証コンテキストの実装
4. **テスト**: 各権限レベルでのアクセステスト
5. **監視**: ログの確認とセキュリティ監視

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