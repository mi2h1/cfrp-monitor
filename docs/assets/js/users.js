// CFRP Monitor - ユーザー管理ページJavaScript

let users = [];
let currentEditingUserId = null;

// 管理者権限チェック
function isAdmin() {
    const currentUser = getCurrentUser();
    return currentUser && currentUser.userId === 'admin';
}

// 初期化
document.addEventListener('DOMContentLoaded', async () => {
    // 管理者権限チェック
    if (!isAdmin()) {
        document.body.innerHTML = `
            <div class="container-fluid py-4">
                <div class="alert alert-danger text-center">
                    <h4>アクセス拒否</h4>
                    <p>このページにアクセスする権限がありません。</p>
                    <a href="index.html" class="btn btn-primary">記事管理に戻る</a>
                </div>
            </div>
        `;
        return;
    }

    await loadUsers();
    setupEventListeners();
});

// ユーザー一覧を読み込み
async function loadUsers() {
    try {
        const { data, error } = await supabase
            .from('users')
            .select('*')
            .order('created_at', { ascending: false });
        
        if (error) throw error;
        
        users = data || [];
        renderUsers();
        updateStats();
        
        document.getElementById('loading').style.display = 'none';
        document.getElementById('usersContainer').style.display = 'block';
        document.getElementById('statsContainer').style.display = 'block';
        
    } catch (error) {
        console.error('ユーザー読み込みエラー:', error);
        document.getElementById('loading').innerHTML = 
            '<div class="alert alert-danger">ユーザー情報の読み込みに失敗しました</div>';
    }
}

// ユーザー一覧表示
function renderUsers() {
    const container = document.getElementById('usersContainer');
    
    if (users.length === 0) {
        container.innerHTML = '<div class="alert alert-info">登録されているユーザーがありません</div>';
        return;
    }

    const userCards = users.map(user => createUserCard(user)).join('');
    container.innerHTML = `
        <div class="row">
            ${userCards}
        </div>
    `;
}

// ユーザーカード作成
function createUserCard(user) {
    const isAdminUser = user.user_id === 'admin';
    const lastLogin = user.last_login ? new Date(user.last_login).toLocaleString('ja-JP') : '未ログイン';
    const createdAt = new Date(user.created_at).toLocaleString('ja-JP');
    const role = user.role || 'viewer';
    const roleColor = getRoleColor(role);
    const roleLabel = getRoleLabel(role);
    
    return `
        <div class="col-md-6 col-lg-4 mb-3">
            <div class="card ${isAdminUser ? 'border-warning' : ''}">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">
                        ${getRoleIcon(role)} ${escapeHtml(user.display_name || user.user_id)}
                    </h6>
                    <div class="d-flex align-items-center gap-2">
                        <span class="badge bg-${roleColor}">${roleLabel}</span>
                        ${!isAdminUser || getCurrentUser()?.userId === 'admin' ? `
                            <div class="dropdown">
                                <button class="btn btn-outline-secondary btn-sm dropdown-toggle" type="button" data-bs-toggle="dropdown">
                                    ⚙️
                                </button>
                                <ul class="dropdown-menu">
                                    <li><a class="dropdown-item" href="#" onclick="editUser('${user.user_id}')">編集</a></li>
                                    ${user.user_id !== 'admin' ? `<li><a class="dropdown-item text-danger" href="#" onclick="deleteUser('${user.user_id}')">削除</a></li>` : ''}
                                </ul>
                            </div>
                        ` : ''}
                    </div>
                </div>
                <div class="card-body">
                    <p class="card-text">
                        <strong>ユーザーID:</strong> ${escapeHtml(user.user_id)}<br>
                        <strong>権限:</strong> ${roleLabel}<br>
                        <strong>作成日:</strong> ${createdAt}<br>
                        <strong>最終ログイン:</strong> ${lastLogin}
                    </p>
                </div>
            </div>
        </div>
    `;
}

// 統計情報更新
function updateStats() {
    const totalUsers = users.length;
    const adminUsers = users.filter(user => user.role === 'admin').length;
    const editorUsers = users.filter(user => user.role === 'editor').length;
    const viewerUsers = users.filter(user => user.role === 'viewer').length;
    
    document.getElementById('totalUsers').textContent = totalUsers;
    document.getElementById('adminUsers').textContent = adminUsers;
    document.getElementById('editorUsers').textContent = editorUsers;
    document.getElementById('viewerUsers').textContent = viewerUsers;
}

// アラート表示
function showAlert(message, type = 'danger', containerId = 'addUserAlertContainer') {
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

// 新規ユーザー追加
async function addUser(userId, password, displayName, role) {
    try {
        if (!userId || userId.length < 3) {
            showAlert('ユーザーIDは3文字以上で入力してください');
            return false;
        }
        
        if (!password || password.length < 4) {
            showAlert('パスワードは4文字以上で入力してください');
            return false;
        }
        
        if (!role) {
            showAlert('権限を選択してください');
            return false;
        }
        
        // 緊急: 一時的に平文保存（後で修正）
        const { data, error } = await supabase
            .from('users')
            .insert([{
                user_id: userId,
                password_hash: password,
                password_salt: null,
                display_name: displayName || userId,
                role: role
            }])
            .select()
            .single();
        
        if (error) {
            if (error.code === '23505') {
                showAlert('そのユーザーIDは既に使用されています');
            } else {
                showAlert('ユーザー追加に失敗しました: ' + error.message);
            }
            return false;
        }
        
        showAlert('ユーザーを追加しました', 'success');
        await loadUsers();
        return true;
        
    } catch (error) {
        console.error('ユーザー追加エラー:', error);
        showAlert('ユーザー追加に失敗しました');
        return false;
    }
}

// ユーザー編集
function editUser(userId) {
    const user = users.find(u => u.user_id === userId);
    if (!user) return;
    
    currentEditingUserId = userId;
    document.getElementById('editUserId').value = userId;
    document.getElementById('editDisplayName').value = user.display_name || '';
    document.getElementById('editUserPassword').value = '';
    document.getElementById('editUserRole').value = user.role || 'viewer';
    
    const modal = new bootstrap.Modal(document.getElementById('editUserModal'));
    modal.show();
}

// ユーザー更新
async function updateUser(userId, displayName, newPassword, role) {
    try {
        const updateData = {};
        
        if (displayName) {
            updateData.display_name = displayName;
        }
        
        if (newPassword && newPassword.length >= 4) {
            // 緊急: 一時的に平文保存（後で修正）
            updateData.password_hash = newPassword;
            updateData.password_salt = null;
        } else if (newPassword && newPassword.length < 4) {
            showAlert('パスワードは4文字以上で入力してください', 'danger', 'editUserAlertContainer');
            return false;
        }
        
        if (role) {
            updateData.role = role;
        }
        
        const { error } = await supabase
            .from('users')
            .update(updateData)
            .eq('user_id', userId);
        
        if (error) throw error;
        
        showAlert('ユーザー情報を更新しました', 'success', 'editUserAlertContainer');
        await loadUsers();
        return true;
        
    } catch (error) {
        console.error('ユーザー更新エラー:', error);
        showAlert('ユーザー更新に失敗しました', 'danger', 'editUserAlertContainer');
        return false;
    }
}

// ユーザー削除
async function deleteUser(userId) {
    if (userId === 'admin') {
        alert('管理者ユーザーは削除できません');
        return;
    }
    
    if (!confirm(`ユーザー "${userId}" を削除しますか？\n\nこの操作は取り消せません。`)) {
        return;
    }
    
    try {
        const { error } = await supabase
            .from('users')
            .delete()
            .eq('user_id', userId);
        
        if (error) throw error;
        
        alert('ユーザーを削除しました');
        await loadUsers();
        
    } catch (error) {
        console.error('ユーザー削除エラー:', error);
        alert('ユーザー削除に失敗しました');
    }
}

// イベントリスナー設定
function setupEventListeners() {
    // 新規ユーザー追加ボタン
    document.getElementById('addUserBtn').addEventListener('click', () => {
        document.getElementById('addUserForm').reset();
        document.getElementById('addUserAlertContainer').innerHTML = '';
        const modal = new bootstrap.Modal(document.getElementById('addUserModal'));
        modal.show();
    });
    
    // 更新ボタン
    document.getElementById('refreshUsersBtn').addEventListener('click', loadUsers);
    
    // 新規ユーザー追加フォーム
    document.getElementById('addUserForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const userId = document.getElementById('newUserId').value.trim();
        const password = document.getElementById('newUserPassword').value.trim();
        const displayName = document.getElementById('newDisplayName').value.trim();
        const role = document.getElementById('newUserRole').value;
        
        if (await addUser(userId, password, displayName, role)) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('addUserModal'));
            setTimeout(() => {
                modal.hide();
            }, 1500);
        }
    });
    
    // ユーザー編集フォーム
    document.getElementById('editUserForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const userId = document.getElementById('editUserId').value;
        const displayName = document.getElementById('editDisplayName').value.trim();
        const newPassword = document.getElementById('editUserPassword').value.trim();
        const role = document.getElementById('editUserRole').value;
        
        if (await updateUser(userId, displayName, newPassword, role)) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('editUserModal'));
            setTimeout(() => {
                modal.hide();
            }, 1500);
        }
    });
    
    // ユーザー削除ボタン
    document.getElementById('deleteUserBtn').addEventListener('click', () => {
        const userId = document.getElementById('editUserId').value;
        const modal = bootstrap.Modal.getInstance(document.getElementById('editUserModal'));
        modal.hide();
        
        setTimeout(() => {
            deleteUser(userId);
        }, 300);
    });
    
    // モーダルが閉じられたときにフォームをリセット
    document.getElementById('addUserModal').addEventListener('hidden.bs.modal', () => {
        document.getElementById('addUserForm').reset();
        document.getElementById('addUserAlertContainer').innerHTML = '';
    });
    
    document.getElementById('editUserModal').addEventListener('hidden.bs.modal', () => {
        document.getElementById('editUserForm').reset();
        document.getElementById('editUserAlertContainer').innerHTML = '';
        currentEditingUserId = null;
    });
}

// 権限関連のユーティリティ関数
function getRoleColor(role) {
    const colors = {
        'admin': 'danger',
        'editor': 'warning',
        'viewer': 'info'
    };
    return colors[role] || 'secondary';
}

function getRoleLabel(role) {
    const labels = {
        'admin': '管理者',
        'editor': '編集者',
        'viewer': '閲覧者'
    };
    return labels[role] || '不明';
}

function getRoleIcon(role) {
    const icons = {
        'admin': '👑',
        'editor': '✏️',
        'viewer': '👤'
    };
    return icons[role] || '👤';
}