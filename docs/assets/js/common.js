// CFRP Monitor - 共通JavaScript

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
            generateNavigation(data.layout.navigation, activePageId);
            displayUserInfo(data.user, data.layout.user_menu);
            window.userFeatures = data.layout.features;
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
function generateNavigation(navItems, activePageId) {
    const navContainer = document.getElementById('sidebarNav');
    if (!navContainer) return;
    
    navContainer.innerHTML = navItems.map(item => 
        `<div class="nav-item">
            <a class="nav-link ${(activePageId === item.id) ? 'active' : ''}" href="${item.href}">
                <span class="nav-icon"><i class="fas ${item.icon || 'fa-circle'}"></i></span>
                <span>${item.label}</span>
            </a>
        </div>`
    ).join('');
}

// 統一されたユーザー情報表示関数（サイドバー用）
function displayUserInfo(user, userMenu) {
    const userNameElement = document.getElementById('userName');
    const userRoleElement = document.getElementById('userRole');
    
    if (userNameElement) {
        userNameElement.textContent = userMenu.display_name;
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