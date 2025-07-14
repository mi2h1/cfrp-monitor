// CFRP Monitor - ログインページJavaScript

// 既にログインしている場合はリダイレクト
if (localStorage.getItem('currentUser')) {
    window.location.href = 'index.html';
}

// アラート表示関数
function showAlert(message, type = 'danger') {
    const alertContainer = document.getElementById('alertContainer');
    alertContainer.innerHTML = `
        <div class="alert alert-${type}" role="alert">
            ${message}
        </div>
    `;
    setTimeout(() => {
        alertContainer.innerHTML = '';
    }, 5000);
}

// ログインフォーム処理
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const userId = document.getElementById('userId').value.trim();
    
    if (!userId) {
        showAlert('ユーザーIDを入力してください');
        return;
    }

    try {
        // ユーザーの存在確認
        const { data, error } = await supabase
            .from('users')
            .select('*')
            .eq('user_id', userId)
            .single();

        if (error || !data) {
            showAlert('ユーザーIDが見つかりません');
            return;
        }

        // ログイン成功
        localStorage.setItem('currentUser', userId);
        localStorage.setItem('currentUserData', JSON.stringify(data));
        
        // 最終ログイン時刻を更新
        await supabase
            .from('users')
            .update({ last_login: new Date().toISOString() })
            .eq('user_id', userId);

        showAlert('ログインしました！リダイレクト中...', 'success');
        setTimeout(() => {
            window.location.href = 'index.html';
        }, 1000);

    } catch (error) {
        console.error('ログインエラー:', error);
        showAlert('ログインに失敗しました');
    }
});

// 新規登録フォーム処理
document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const newUserId = document.getElementById('newUserId').value.trim();
    const displayName = document.getElementById('displayName').value.trim();
    
    if (!newUserId) {
        showAlert('ユーザーIDを入力してください');
        return;
    }

    if (newUserId.length < 3) {
        showAlert('ユーザーIDは3文字以上で入力してください');
        return;
    }

    try {
        // 新規ユーザー作成
        const { data, error } = await supabase
            .from('users')
            .insert([{
                user_id: newUserId,
                display_name: displayName || newUserId
            }])
            .select()
            .single();

        if (error) {
            if (error.code === '23505') { // unique constraint violation
                showAlert('そのユーザーIDは既に使用されています');
            } else {
                showAlert('登録に失敗しました: ' + error.message);
            }
            return;
        }

        // 登録成功後、自動ログイン
        localStorage.setItem('currentUser', newUserId);
        localStorage.setItem('currentUserData', JSON.stringify(data));
        
        showAlert('登録完了！ログインしました。リダイレクト中...', 'success');
        setTimeout(() => {
            window.location.href = 'index.html';
        }, 1000);

    } catch (error) {
        console.error('登録エラー:', error);
        showAlert('登録に失敗しました');
    }
});

// Enterキーでフォーム送信（ログインフォーム）
document.getElementById('userId').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        document.getElementById('loginForm').querySelector('button[type="submit"]').click();
    }
});

// Enterキーでフォーム送信（新規登録フォーム）
document.getElementById('newUserId').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        document.getElementById('registerForm').querySelector('button[type="submit"]').click();
    }
});

document.getElementById('displayName').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        document.getElementById('registerForm').querySelector('button[type="submit"]').click();
    }
});