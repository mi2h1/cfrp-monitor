// CFRP Monitor - ログインページJavaScript

// 既にログインしている場合はリダイレクト
if (localStorage.getItem('auth_token')) {
    window.location.href = '/';
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
        
        console.log('Login successful - stored data:');
        console.log('Token stored:', !!localStorage.getItem('auth_token'));
        console.log('User info stored:', !!localStorage.getItem('user_info'));
        console.log('User data:', data.user);
        
        showAlert('ログインしました！リダイレクト中...', 'success');
        setTimeout(() => {
            console.log('Redirecting to main page...');
            window.location.href = '/';
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
        // ユーザー登録APIを呼び出し
        const response = await fetch('/api/users', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: newUserId,
                password: newPassword,
                display_name: displayName || newUserId,
                role: 'viewer'
            })
        });
        
        const data = await response.json();

        if (!data.success) {
            if (data.error && data.error.includes('already exists')) {
                showAlert('そのユーザーIDは既に使用されています', 'danger', 'registerAlertContainer');
            } else {
                showAlert('登録に失敗しました: ' + (data.error || 'Unknown error'), 'danger', 'registerAlertContainer');
            }
            return;
        }

        // 登録成功後、自動ログイン
        // JWTトークンを保存（登録成功後にログイン処理を実行）
        const loginResponse = await fetch('/api/auth', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: newUserId,
                password: newPassword
            })
        });
        
        const loginData = await loginResponse.json();
        
        if (loginData.success) {
            // JWTトークンを保存
            localStorage.setItem('auth_token', loginData.token);
            localStorage.setItem('user_info', JSON.stringify(loginData.user));
            
            // 従来のlocalStorageキーも互換性のため保存
            localStorage.setItem('currentUser', newUserId);
            localStorage.setItem('currentUserData', JSON.stringify(loginData.user));
        }
        
        showAlert('登録完了！ログインしました。リダイレクト中...', 'success', 'registerAlertContainer');
        
        // モーダルを閉じる
        const modal = bootstrap.Modal.getInstance(document.getElementById('registerModal'));
        setTimeout(() => {
            modal.hide();
            window.location.href = '/';
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