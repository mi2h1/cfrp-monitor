// CFRP Monitor - 共通JavaScript

// Supabaseの設定
const SUPABASE_URL = 'https://nvchsqotmchzpharujap.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im52Y2hzcW90bWNoenBoYXJ1amFwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDUzMDc2OTAsImV4cCI6MjA2MDg4MzY5MH0.h6MdiDYNySabXxpeS_92KWuwUQlavQqv-9GJyKCn2jo';

const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

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

function logout() {
    localStorage.removeItem('currentUser');
    localStorage.removeItem('currentUserData');
    window.location.href = 'login.html';
}

// ログイン状態の表示とログアウト機能を設定
function setupAuthUI() {
    console.log('setupAuthUI called');
    const userInfo = document.getElementById('userInfo');
    const logoutBtn = document.getElementById('logoutBtn');
    
    console.log('userInfo:', userInfo, 'logoutBtn:', logoutBtn);
    if (!userInfo || !logoutBtn) {
        console.log('userInfo or logoutBtn not found, returning');
        return;
    }
    
    const user = getCurrentUser();
    if (user) {
        userInfo.textContent = `👤 ${user.data.display_name || user.userId}`;
        logoutBtn.style.display = 'block';
        
        logoutBtn.addEventListener('click', () => {
            if (confirm('ログアウトしますか？')) {
                logout();
            }
        });
    } else {
        // 未ログインの場合はログインページにリダイレクト
        if (!window.location.pathname.includes('login.html')) {
            window.location.href = 'login.html';
        }
    }
}

// ページ読み込み時に認証状態をチェック
document.addEventListener('DOMContentLoaded', () => {
    setupAuthUI();
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