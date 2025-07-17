// CFRP Monitor - ログインページJavaScript

// 既にログインしている場合はリダイレクト
if (localStorage.getItem('currentUser')) {
    window.location.href = 'index.html';
}

// アラート表示関数
function showAlert(message, type = 'danger', containerId = 'alertContainer') {
    const alertContainer = document.getElementById(containerId);
    alertContainer.innerHTML = `
        <div class="alert alert-${type}" role="alert">
            ${message}
        </div>
    `;
    setTimeout(() => {
        alertContainer.innerHTML = '';
    }, 5000);
}

// DOMが読み込まれてからイベントリスナーを設定
document.addEventListener('DOMContentLoaded', () => {
    // モーダル表示
    document.getElementById('showRegisterModal').addEventListener('click', (e) => {
        e.preventDefault();
        const modal = new bootstrap.Modal(document.getElementById('registerModal'));
        modal.show();
    });

    // モーダルが閉じられたときにフォームをリセット
    document.getElementById('registerModal').addEventListener('hidden.bs.modal', () => {
        document.getElementById('registerForm').reset();
        document.getElementById('registerAlertContainer').innerHTML = '';
    });
});

// ログインフォーム処理
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const userId = document.getElementById('userId').value.trim();
    const password = document.getElementById('password').value.trim();
    
    if (!userId) {
        showAlert('ユーザーIDを入力してください');
        return;
    }
    
    if (!password) {
        showAlert('パスワードを入力してください');
        return;
    }

    try {
        // ユーザーの存在確認とパスワード認証
        const { data, error } = await supabase
            .from('users')
            .select('*')
            .eq('user_id', userId)
            .eq('password_hash', password)
            .single();

        if (error || !data) {
            showAlert('ユーザーIDまたはパスワードが間違っています');
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
    const newPassword = document.getElementById('newPassword').value.trim();
    const displayName = document.getElementById('displayName').value.trim();
    
    if (!newUserId) {
        showAlert('ユーザーIDを入力してください', 'danger', 'registerAlertContainer');
        return;
    }

    if (newUserId.length < 3) {
        showAlert('ユーザーIDは3文字以上で入力してください', 'danger', 'registerAlertContainer');
        return;
    }
    
    if (!newPassword) {
        showAlert('パスワードを入力してください', 'danger', 'registerAlertContainer');
        return;
    }
    
    if (newPassword.length < 4) {
        showAlert('パスワードは4文字以上で入力してください', 'danger', 'registerAlertContainer');
        return;
    }

    try {
        // 新規ユーザー作成
        const { data, error } = await supabase
            .from('users')
            .insert([{
                user_id: newUserId,
                password_hash: newPassword,
                display_name: displayName || newUserId,
                role: 'viewer'
            }])
            .select()
            .single();

        if (error) {
            if (error.code === '23505') { // unique constraint violation
                showAlert('そのユーザーIDは既に使用されています', 'danger', 'registerAlertContainer');
            } else {
                showAlert('登録に失敗しました: ' + error.message, 'danger', 'registerAlertContainer');
            }
            return;
        }

        // 登録成功後、自動ログイン
        localStorage.setItem('currentUser', newUserId);
        localStorage.setItem('currentUserData', JSON.stringify(data));
        
        showAlert('登録完了！ログインしました。リダイレクト中...', 'success', 'registerAlertContainer');
        
        // モーダルを閉じる
        const modal = bootstrap.Modal.getInstance(document.getElementById('registerModal'));
        setTimeout(() => {
            modal.hide();
            window.location.href = 'index.html';
        }, 1000);

    } catch (error) {
        console.error('登録エラー:', error);
        showAlert('登録に失敗しました', 'danger', 'registerAlertContainer');
    }
});

// Enterキーでフォーム送信（ログインフォーム）
document.getElementById('userId').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        document.getElementById('loginForm').querySelector('button[type="submit"]').click();
    }
});

document.getElementById('password').addEventListener('keydown', (e) => {
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

document.getElementById('newPassword').addEventListener('keydown', (e) => {
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