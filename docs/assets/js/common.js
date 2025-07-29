// CFRP Monitor - 共通JavaScript

// DOM読み込み完了後にイベントハンドラを設定
document.addEventListener('DOMContentLoaded', function() {
    // サイドバートグルボタンのイベントハンドラを設定
    const mobileToggle = document.getElementById('mobileToggle');
    if (mobileToggle) {
        mobileToggle.addEventListener('click', toggleSidebar);
    }

    // ログアウトリンクのイベントハンドラを設定
    const logoutLinks = document.querySelectorAll('a[href="#"]');
    logoutLinks.forEach(link => {
        if (link.textContent.trim() === 'ログアウト') {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                logout();
            });
        }
    });
});

// パスワードハッシュ化関数
async function hashPassword(password, salt = null) {
    // ソルトが指定されていない場合は新しいソルトを生成
    if (!salt) {
        salt = crypto.getRandomValues(new Uint8Array(16));
        salt = Array.from(salt, byte => byte.toString(16).padStart(2, '0')).join('');
    }
    
    // パスワードとソルトを結合
    const saltedPassword = password + salt;
    
    // SHA-256でハッシュ化
    const encoder = new TextEncoder();
    const data = encoder.encode(saltedPassword);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    
    // ハッシュを16進数文字列に変換
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    
    return { hash: hashHex, salt: salt };
}

// パスワード検証関数
async function verifyPassword(password, storedHash, salt) {
    const { hash } = await hashPassword(password, salt);
    return hash === storedHash;
}

// APIベースのシステムに移行済み - Supabaseクライアントは不要

// ===========================================
// 統一ナビゲーションシステム
// ===========================================

// 統一されたナビゲーション初期化システム
async function initializeNavigation(activePageId) {
    const authToken = localStorage.getItem('auth_token');
    
    if (!authToken) {
        window.location.href = '/login';
        return null;
    }
    
    try {
        const response = await fetch('/api/layout', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        
        if (data.success) {
            generateNavigation(data.layout.navigation, activePageId, data.last_updated);
            displayUserInfo(data.user, data.layout.user_menu);
            window.userFeatures = data.layout.features;
            window.currentUser = data.user; // ユーザー情報をグローバルに保存
            setupUnifiedLogout();
            return data.layout;
        } else {
            throw new Error(data.error || 'レイアウト取得に失敗');
        }
        
    } catch (error) {
        console.error('Layout loading error:', error);
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_info');
        localStorage.removeItem('currentUser');
        localStorage.removeItem('currentUserData');
        window.location.href = '/login';
        return null;
    }
}

// 統一されたナビゲーション生成関数（サイドバー用）
function generateNavigation(navItems, activePageId, lastUpdated = null) {
    const navContainer = document.getElementById('sidebarNav');
    if (!navContainer) return;
    
    navContainer.innerHTML = navItems.map(item => {
        let lastUpdatedHtml = '';
        
        // 最終更新時刻を表示（記事管理と情報源管理のみ）
        if (lastUpdated) {
            if (item.id === 'articles' && lastUpdated.articles) {
                lastUpdatedHtml = `<div class="nav-last-updated">最終更新：${lastUpdated.articles}</div>`;
            } else if (item.id === 'sources' && lastUpdated.sources) {
                lastUpdatedHtml = `<div class="nav-last-updated">最終更新：${lastUpdated.sources}</div>`;
            }
        }
        
        return `<div class="nav-item">
            <a class="nav-link ${(activePageId === item.id) ? 'active' : ''}" href="${item.href}">
                <span class="nav-icon"><i class="fas ${item.icon || 'fa-circle'}"></i></span>
                <span class="nav-label">
                    <span>${item.label}</span>
                    ${lastUpdatedHtml}
                </span>
            </a>
        </div>`;
    }).join('');
}

// 統一されたユーザー情報表示関数（サイドバー用）
function displayUserInfo(user, userMenu) {
    const userNameElement = document.getElementById('userName');
    const userRoleElement = document.getElementById('userRole');
    
    
    if (userNameElement) {
        // ユーザー名と設定アイコンを表示
        if (userMenu.display_name) {
            // 表示名が設定されている場合：表示名 + 小さなID表示
            userNameElement.innerHTML = `
                <span>
                    ${userMenu.display_name}
                    <small class="text-muted ms-1" style="font-style: italic; font-size: 0.7rem;">ID: ${user.user_id}</small>
                </span>
                <button class="user-settings-btn" id="userSettingsBtn" title="ユーザー設定">
                    <i class="fas fa-cog"></i>
                </button>
            `;
        } else {
            // 表示名が設定されていない場合：IDのみ表示
            userNameElement.innerHTML = `
                <span>${user.user_id}</span>
                <button class="user-settings-btn" id="userSettingsBtn" title="ユーザー設定">
                    <i class="fas fa-cog"></i>
                </button>
            `;
        }
        
        // 設定ボタンのイベントハンドラを設定
        const settingsBtn = document.getElementById('userSettingsBtn');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', openUserSettingsModal);
        }
    }
    if (userRoleElement) {
        userRoleElement.textContent = userMenu.role_display;
    }
}

// 統一されたログアウト処理（サイドバー用）
function setupUnifiedLogout() {
    const logoutBtn = document.getElementById('logoutBtn');
    if (!logoutBtn) return;
    
    logoutBtn.replaceWith(logoutBtn.cloneNode(true));
    const newLogoutBtn = document.getElementById('logoutBtn');
    
    newLogoutBtn.addEventListener('click', function() {
        if (confirm('ログアウトしますか？')) {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user_info');
            localStorage.removeItem('currentUser');
            localStorage.removeItem('currentUserData');
            window.location.href = '/login';
        }
    });
}


// 権限チェック用ヘルパー関数
function checkPagePermission(requiredFeature) {
    if (!window.userFeatures || !window.userFeatures[requiredFeature]) {
        alert('このページにアクセスする権限がありません');
        window.location.href = '/articles';
        return false;
    }
    return true;
}

// モバイル用サイドバートグル（全ページ共通）
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.toggle('show');
    }
}

// ===========================================
// 従来の認証システム（互換性のため残存）
// ==========================================

// 認証管理
function getCurrentUser() {
    const userId = localStorage.getItem('currentUser');
    const userData = localStorage.getItem('currentUserData');
    
    if (userId && userData) {
        return {
            userId: userId,
            data: JSON.parse(userData)
        };
    }
    return null;
}

function isLoggedIn() {
    return getCurrentUser() !== null;
}

// 権限チェック関数
function hasRole(requiredRole) {
    const user = getCurrentUser();
    if (!user || !user.data || !user.data.role) return false;
    
    const roleHierarchy = {
        'admin': 3,
        'editor': 2,
        'viewer': 1
    };
    
    const userLevel = roleHierarchy[user.data.role] || 0;
    const requiredLevel = roleHierarchy[requiredRole] || 0;
    
    return userLevel >= requiredLevel;
}

// 特定の権限チェック
function isAdmin() {
    return hasRole('admin');
}

function canEditSources() {
    return hasRole('editor');
}

function canViewArticles() {
    return hasRole('viewer');
}

function logout() {
    localStorage.removeItem('currentUser');
    localStorage.removeItem('currentUserData');
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
    window.location.href = '/login';
}

// ユーザー設定モーダルを開く
function openUserSettingsModal() {
    // モーダルが既に存在する場合は削除
    const existingModal = document.getElementById('userSettingsModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // モーダルHTML生成
    const modalHTML = `
        <div class="modal fade" id="userSettingsModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-user-cog me-2"></i>ユーザー設定
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="userSettingsForm">
                            <div class="mb-3">
                                <label for="displayName" class="form-label">表示名</label>
                                <input type="text" class="form-control" id="displayName" placeholder="表示名を入力" autocomplete="off">
                            </div>
                            <div class="mb-3">
                                <label for="newPassword" class="form-label">新しいパスワード</label>
                                <input type="password" class="form-control" id="newPassword" placeholder="新しいパスワード（4文字以上）" autocomplete="new-password">
                                <div class="form-text">パスワードを変更しない場合は空のままにしてください</div>
                            </div>
                            <div id="settingsError" class="alert alert-danger d-none"></div>
                            <div id="settingsSuccess" class="alert alert-success d-none"></div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">キャンセル</button>
                        <button type="button" class="btn btn-primary" id="saveSettingsBtn">
                            <i class="fas fa-save me-1"></i>保存
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // モーダルをDOMに追加
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Bootstrapモーダルを初期化して表示
    const modal = new bootstrap.Modal(document.getElementById('userSettingsModal'));
    modal.show();
    
    // 現在のユーザー情報を取得してフォームに設定
    loadCurrentUserSettings();
    
    // 保存ボタンのイベントハンドラを設定
    document.getElementById('saveSettingsBtn').addEventListener('click', saveUserSettings);
}

// 現在のユーザー設定を読み込む
async function loadCurrentUserSettings() {
    try {
        const authToken = localStorage.getItem('auth_token');
        const response = await fetch('/api/profile', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success && data.user) {
            document.getElementById('displayName').value = data.user.display_name || '';
        }
    } catch (error) {
        console.error('ユーザー設定の読み込みエラー:', error);
    }
}

// ユーザー設定を保存
async function saveUserSettings() {
    const saveBtn = document.getElementById('saveSettingsBtn');
    const errorDiv = document.getElementById('settingsError');
    const successDiv = document.getElementById('settingsSuccess');
    const displayName = document.getElementById('displayName').value;
    const newPassword = document.getElementById('newPassword').value;
    
    // エラー・成功メッセージをクリア
    errorDiv.classList.add('d-none');
    successDiv.classList.add('d-none');
    
    // バリデーション（表示名は任意、空文字列も許可）
    
    if (newPassword && newPassword.length < 4) {
        errorDiv.textContent = 'パスワードは4文字以上で入力してください';
        errorDiv.classList.remove('d-none');
        return;
    }
    
    // 保存中の状態に変更
    const originalBtnContent = saveBtn.innerHTML;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>保存中...';
    saveBtn.disabled = true;
    
    try {
        const authToken = localStorage.getItem('auth_token');
        const updateData = { display_name: displayName };
        
        if (newPassword) {
            updateData.password = newPassword;
        }
        
        const response = await fetch('/api/profile', {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updateData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 成功メッセージを表示
            successDiv.textContent = 'ユーザー設定を更新しました';
            successDiv.classList.remove('d-none');
            
            // サイドバーの表示名を更新
            const userNameElement = document.getElementById('userName');
            if (userNameElement) {
                // 現在のユーザーIDを取得（JWTトークンから）
                const authToken = localStorage.getItem('auth_token');
                let currentUserId = 'unknown';
                try {
                    const payload = JSON.parse(atob(authToken.split('.')[1]));
                    currentUserId = payload.user_id;
                } catch (e) {
                    console.error('Failed to decode user ID from token');
                }
                
                if (displayName) {
                    // 表示名が設定されている場合：表示名 + 小さなID表示
                    userNameElement.innerHTML = `
                        <span>
                            ${displayName}
                            <small class="text-muted ms-1" style="font-style: italic; font-size: 0.7rem;">ID: ${currentUserId}</small>
                        </span>
                        <button class="user-settings-btn" id="userSettingsBtn" title="ユーザー設定">
                            <i class="fas fa-cog"></i>
                        </button>
                    `;
                } else {
                    // 表示名が設定されていない場合：IDのみ表示
                    userNameElement.innerHTML = `
                        <span>${currentUserId}</span>
                        <button class="user-settings-btn" id="userSettingsBtn" title="ユーザー設定">
                            <i class="fas fa-cog"></i>
                        </button>
                    `;
                }
                
                // イベントハンドラを再設定
                const newSettingsBtn = document.getElementById('userSettingsBtn');
                if (newSettingsBtn) {
                    newSettingsBtn.addEventListener('click', openUserSettingsModal);
                }
            }
            
            // 1秒後にモーダルを閉じる
            setTimeout(() => {
                const modal = bootstrap.Modal.getInstance(document.getElementById('userSettingsModal'));
                if (modal) {
                    modal.hide();
                }
            }, 1000);
        } else {
            errorDiv.textContent = data.error || '設定の更新に失敗しました';
            errorDiv.classList.remove('d-none');
        }
    } catch (error) {
        console.error('設定保存エラー:', error);
        errorDiv.textContent = '設定の保存中にエラーが発生しました';
        errorDiv.classList.remove('d-none');
    } finally {
        // ボタンを元の状態に戻す
        saveBtn.innerHTML = originalBtnContent;
        saveBtn.disabled = false;
    }
}

// ログイン状態の表示とログアウト機能を設定
function setupAuthUI() {
    const userInfo = document.getElementById('userInfo');
    const logoutBtn = document.getElementById('logoutBtn');
    
    if (!userInfo || !logoutBtn) {
        return;
    }
    
    const user = getCurrentUser();
    if (user) {
        userInfo.textContent = `👤 ${user.data.display_name || user.userId}`;
        logoutBtn.style.display = 'block';
        
        // 権限に応じてナビゲーションリンクを表示
        const userManagementLink = document.getElementById('userManagementLink');
        const sourcesLink = document.getElementById('sourcesLink');
        
        if (userManagementLink && isAdmin()) {
            userManagementLink.classList.remove('hidden');
        }
        
        if (sourcesLink && !canEditSources()) {
            sourcesLink.classList.add('hidden');
        }
        
        logoutBtn.addEventListener('click', () => {
            if (confirm('ログアウトしますか？')) {
                logout();
            }
        });
    } else {
        // 未ログインの場合はログインページにリダイレクト
        if (!window.location.pathname.includes('/login')) {
            window.location.href = '/login';
        }
    }
}

// データベース直接アクセス制限は削除（APIベースに移行のため）
function restrictDirectDatabaseAccess() {
    // API移行に伴い、Supabaseクライアント制限は無効化
}

// セッションタイムアウト機能
const SESSION_TIMEOUT = 30 * 60 * 1000; // 30分

function checkSessionTimeout() {
    const lastActivity = localStorage.getItem('lastActivity');
    const now = Date.now();
    
    if (lastActivity && (now - parseInt(lastActivity)) > SESSION_TIMEOUT) {
        logout();
        alert('セッションがタイムアウトしました。再度ログインしてください。');
        window.location.href = '/login';
    }
}

// アクティビティ監視
function trackActivity() {
    localStorage.setItem('lastActivity', Date.now().toString());
}

// ページ読み込み時に認証状態をチェック
document.addEventListener('DOMContentLoaded', async () => {
    setupAuthUI();
    restrictDirectDatabaseAccess();
    
    // アクティビティ監視開始
    trackActivity();
    document.addEventListener('click', trackActivity);
    document.addEventListener('keydown', trackActivity);
    
    // セッションタイムアウトチェック開始
    setInterval(checkSessionTimeout, 60000); // 1分ごと
});

// ユーティリティ関数
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 共通のフィルター・ソート機能
function setupFilterListeners(filterIds, renderFunction) {
    filterIds.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('change', () => {
                if (window.currentPage !== undefined) {
                    window.currentPage = 1; // ページをリセット
                }
                renderFunction();
            });
        }
    });
}

// 共通の更新ボタン機能
function setupRefreshButton(loadFunction) {
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
            refreshBtn.disabled = true;
            await loadFunction();
            refreshBtn.disabled = false;
        });
    }
}

// ページネーション用のユーティリティ
function setupPagination(containerSelector, renderFunction) {
    const paginationList = document.getElementById('paginationList');
    if (paginationList) {
        paginationList.addEventListener('click', (e) => {
            e.preventDefault();
            if (e.target.classList.contains('page-link') && !e.target.closest('.disabled')) {
                const page = parseInt(e.target.dataset.page);
                if (page && page !== window.currentPage) {
                    window.currentPage = page;
                    renderFunction();
                    // ページトップにスクロール
                    const container = document.querySelector(containerSelector);
                    if (container) {
                        container.scrollIntoView({ behavior: 'smooth' });
                    }
                }
            }
        });
    }
}

// ページネーション表示の共通関数
function renderPagination(totalItems, itemsPerPage, currentPage) {
    const pageInfo = document.getElementById('pageInfo');
    const paginationList = document.getElementById('paginationList');
    const paginationListTop = document.getElementById('paginationListTop');
    
    if (!pageInfo || !paginationList) return;
    
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    
    // ページ情報表示
    const startItem = (currentPage - 1) * itemsPerPage + 1;
    const endItem = Math.min(currentPage * itemsPerPage, totalItems);
    pageInfo.textContent = `${startItem}-${endItem} / ${totalItems}件 (ページ ${currentPage}/${totalPages})`;
    
    // ページネーションボタンを生成する関数
    const createPaginationButtons = (container) => {
        container.innerHTML = '';
    
        // 前へボタン
        const prevLi = document.createElement('li');
        prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
        prevLi.innerHTML = `<a class="page-link" href="#" data-page="${currentPage - 1}">前へ</a>`;
        container.appendChild(prevLi);
        
        // ページ番号ボタン
        const maxVisiblePages = 5;
        let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
        let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
        
        // 調整
        if (endPage - startPage + 1 < maxVisiblePages) {
            startPage = Math.max(1, endPage - maxVisiblePages + 1);
        }
        
        // 最初のページが見えない場合
        if (startPage > 1) {
            const firstLi = document.createElement('li');
            firstLi.className = 'page-item';
            firstLi.innerHTML = '<a class="page-link" href="#" data-page="1">1</a>';
            container.appendChild(firstLi);
            
            if (startPage > 2) {
                const ellipsisLi = document.createElement('li');
                ellipsisLi.className = 'page-item disabled';
                ellipsisLi.innerHTML = '<span class="page-link">...</span>';
                container.appendChild(ellipsisLi);
            }
        }
        
        // ページ番号
        for (let i = startPage; i <= endPage; i++) {
            const li = document.createElement('li');
            li.className = `page-item ${i === currentPage ? 'active' : ''}`;
            li.innerHTML = `<a class="page-link" href="#" data-page="${i}">${i}</a>`;
            container.appendChild(li);
        }
        
        // 最後のページが見えない場合
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                const ellipsisLi = document.createElement('li');
                ellipsisLi.className = 'page-item disabled';
                ellipsisLi.innerHTML = '<span class="page-link">...</span>';
                container.appendChild(ellipsisLi);
            }
            
            const lastLi = document.createElement('li');
            lastLi.className = 'page-item';
            lastLi.innerHTML = `<a class="page-link" href="#" data-page="${totalPages}">${totalPages}</a>`;
            container.appendChild(lastLi);
        }
        
        // 次へボタン
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
        nextLi.innerHTML = `<a class="page-link" href="#" data-page="${currentPage + 1}">次へ</a>`;
        container.appendChild(nextLi);
    };
    
    // 下部ページネーション
    createPaginationButtons(paginationList);
    
    // 上部ページネーション（存在する場合）
    if (paginationListTop) {
        createPaginationButtons(paginationListTop);
    }
}