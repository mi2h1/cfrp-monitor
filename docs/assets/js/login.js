// CFRP Monitor - ログインページJavaScript

// 既にログインしている場合はリダイレクト
if (localStorage.getItem('auth_token')) {
    window.location.href = '/articles';
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
    // ログインページ初期化（新規登録機能は削除済み）
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
        // 認証APIを呼び出し
        const response = await fetch('/api/auth', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            showAlert(data.error || 'ログインに失敗しました');
            return;
        }
        
        // JWTトークンを保存
        localStorage.setItem('auth_token', data.token);
        localStorage.setItem('user_info', JSON.stringify(data.user));
        
        // 従来のlocalStorageキーも互換性のため保存
        localStorage.setItem('currentUser', userId);
        localStorage.setItem('currentUserData', JSON.stringify(data.user));
        
        showAlert('ログインしました！リダイレクト中...', 'success');
        setTimeout(() => {
            window.location.href = '/articles';
        }, 1000);

    } catch (error) {
        console.error('ログインエラー:', error);
        showAlert('ログインに失敗しました');
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

