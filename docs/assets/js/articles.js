// CFRP Monitor - 記事管理ページJavaScript

let articles = [];
let sources = [];
let currentPage = 1;
let authToken = null;
let userFeatures = null;

// 初期化
document.addEventListener('DOMContentLoaded', async () => {
    // 認証チェックはメインページのスクリプトで実行済み
    authToken = localStorage.getItem('auth_token');
    userFeatures = window.userFeatures;
    
    await loadSources();
    await loadArticles();
    setupEventListeners();
});

// ソース一覧を読み込み
async function loadSources() {
    try {
        const response = await fetch('/api/sources', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            sources = data.sources || [];
            populateSourceFilter();
        } else {
            console.error('ソース読み込みエラー:', data.error);
        }
    } catch (error) {
        console.error('ソース読み込みエラー:', error);
    }
}

// 記事の総件数を取得（API経由）
async function getTotalArticlesCount(statusFilter = '', flaggedFilter = '', sourceFilter = '') {
    try {
        let url = '/api/articles?count_only=true';
        
        // フィルタリング条件を適用
        if (statusFilter) url += `&status=${encodeURIComponent(statusFilter)}`;
        if (flaggedFilter) url += `&flagged=${encodeURIComponent(flaggedFilter)}`;
        if (sourceFilter) url += `&source_id=${encodeURIComponent(sourceFilter)}`;
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            return data.count || 0;
        } else {
            throw new Error(data.error || '総件数取得に失敗しました');
        }
    } catch (error) {
        console.error('総件数取得エラー:', error);
        return 0;
    }
}

// 記事一覧を読み込み（サーバーサイドページネーション）
async function loadArticles() {
    try {
        // 総件数を取得
        const totalCount = await getTotalArticlesCount();
        
        // 初期表示用に最初のページを取得
        await loadArticlesPage(1, totalCount);
        
        document.getElementById('loading').style.display = 'none';
        document.getElementById('articlesContainer').style.display = 'block';
    } catch (error) {
        console.error('記事読み込みエラー:', error);
        document.getElementById('loading').innerHTML = '<div class="alert alert-danger">記事の読み込みに失敗しました</div>';
    }
}

// 指定されたページの記事を取得
async function loadArticlesPage(page, totalCount = null) {
    try {
        const itemsPerPage = parseInt(document.getElementById('itemsPerPage').value);
        const offset = (page - 1) * itemsPerPage;
        
        // フィルタリング条件を取得
        const statusFilter = document.getElementById('statusFilter').value;
        const flaggedFilter = document.getElementById('flaggedFilter').value;
        const sourceFilter = document.getElementById('sourceFilter').value;
        const sortOrder = document.getElementById('sortOrder').value;
        
        // 総件数が未取得の場合は取得（フィルタリング条件付き）
        if (totalCount === null) {
            totalCount = await getTotalArticlesCount(statusFilter, flaggedFilter, sourceFilter);
        }
        
        // API URLを構築
        let url = `/api/articles?limit=${itemsPerPage}&offset=${offset}&order=${sortOrder}`;
        
        // フィルタリング条件を適用
        if (statusFilter) {
            url += `&status=${encodeURIComponent(statusFilter)}`;
        }
        if (flaggedFilter) {
            url += `&flagged=${encodeURIComponent(flaggedFilter)}`;
        }
        if (sourceFilter) {
            url += `&source_id=${encodeURIComponent(sourceFilter)}`;
        }
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || '記事の読み込みに失敗しました');
        }
        
        articles = data.articles || [];
        currentPage = page;
        
        renderArticles();
        updatePagination(totalCount, itemsPerPage, page);
        
    } catch (error) {
        console.error('記事ページ読み込みエラー:', error);
        document.getElementById('articlesContainer').innerHTML = '<div class="alert alert-danger">記事の読み込みに失敗しました: ' + error.message + '</div>';
    }
}
            query = query.eq('source_id', sourceFilter);
        }
        
        // ソート条件を適用
        const ascending = sortOrder === 'asc';
        query = query.order('published_at', { ascending });
        
        // ページネーション
        query = query.range(offset, offset + itemsPerPage - 1);
        
        const { data, error } = await query;
        
        if (error) throw error;
        
        // グローバル変数を更新
        articles = data || [];
        currentPage = page;
        
        // 表示を更新
        renderArticlesWithServerPagination(totalCount, itemsPerPage);
        
    } catch (error) {
        console.error('ページ読み込みエラー:', error);
        throw error;
    }
}

// 最終タスク実行ログを読み込み
async function loadLastTaskLog() {
    try {
        const { data, error } = await supabase
            .from('task_logs')
            .select('*')
            .eq('task_type', 'daily_crawl')
            .order('executed_at', { ascending: false })
            .limit(1);
        
        if (error) throw error;
        
        if (data && data.length > 0) {
            const lastLog = data[0];
            const executedAt = new Date(lastLog.executed_at).toLocaleString('ja-JP');
            const statusBadge = lastLog.status === 'success' 
                ? '<span class="badge bg-success">成功</span>'
                : '<span class="badge bg-danger">失敗</span>';
            
            // ナビバーに表示
            const userInfo = document.getElementById('userInfo');
            if (userInfo) {
                const logInfo = document.createElement('span');
                logInfo.className = 'navbar-text text-white-50 me-3';
                logInfo.innerHTML = `📅 最終実行: ${executedAt} ${statusBadge}`;
                userInfo.parentNode.insertBefore(logInfo, userInfo);
            }
        }
    } catch (error) {
        console.error('タスクログ読み込みエラー:', error);
    }
}

// ソースフィルターを設定
function populateSourceFilter() {
    const select = document.getElementById('sourceFilter');
    sources.forEach(source => {
        const option = document.createElement('option');
        option.value = source.id;
        option.textContent = source.name || source.domain;
        select.appendChild(option);
    });
}

// 記事を表示（従来のクライアントサイドページネーション）
function renderArticles() {
    const container = document.getElementById('articlesContainer');
    const filteredArticles = filterAndSortArticles();
    const itemsPerPage = parseInt(document.getElementById('itemsPerPage').value);
    
    if (filteredArticles.length === 0) {
        container.innerHTML = '<div class="alert alert-info">該当する記事がありません</div>';
        document.getElementById('pagination').style.display = 'none';
        document.getElementById('paginationTop').style.display = 'none';
        return;
    }

    // ページネーション計算
    const totalPages = Math.ceil(filteredArticles.length / itemsPerPage);
    
    // 現在のページが総ページ数を超えている場合は1ページ目に戻す
    if (currentPage > totalPages && totalPages > 0) {
        currentPage = 1;
    }
    
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const paginatedArticles = filteredArticles.slice(startIndex, endIndex);

    // 記事表示
    container.innerHTML = paginatedArticles.map(article => createCompactArticleCard(article)).join('');
    
    // ページネーション表示
    renderPagination(filteredArticles.length, itemsPerPage, currentPage);
    document.getElementById('pagination').style.display = 'block';
    document.getElementById('paginationTop').style.display = 'block';
}

// 記事を表示（サーバーサイドページネーション）
function renderArticlesWithServerPagination(totalCount, itemsPerPage) {
    const container = document.getElementById('articlesContainer');
    
    if (articles.length === 0) {
        container.innerHTML = '<div class="alert alert-info">該当する記事がありません</div>';
        document.getElementById('pagination').style.display = 'none';
        document.getElementById('paginationTop').style.display = 'none';
        return;
    }

    // 記事表示
    container.innerHTML = articles.map(article => createCompactArticleCard(article)).join('');
    
    // ページネーション表示
    renderPagination(totalCount, itemsPerPage, currentPage);
    document.getElementById('pagination').style.display = 'block';
    document.getElementById('paginationTop').style.display = 'block';
}

// フィルタリングとソート
function filterAndSortArticles() {
    const statusFilter = document.getElementById('statusFilter').value;
    const flaggedFilter = document.getElementById('flaggedFilter').value;
    const sourceFilter = document.getElementById('sourceFilter').value;
    const sortOrder = document.getElementById('sortOrder').value;

    // フィルタリング
    let filtered = articles.filter(article => {
        if (statusFilter && article.status !== statusFilter) return false;
        if (flaggedFilter && String(article.flagged) !== flaggedFilter) return false;
        if (sourceFilter && article.source_id !== sourceFilter) return false;
        return true;
    });

    // ソート
    filtered.sort((a, b) => {
        const dateA = new Date(a.published_at || a.added_at || 0);
        const dateB = new Date(b.published_at || b.added_at || 0);
        
        if (sortOrder === 'asc') {
            return dateA - dateB; // 古い順
        } else {
            return dateB - dateA; // 新しい順
        }
    });

    return filtered;
}

// コンパクトな記事カードを作成
function createCompactArticleCard(article) {
    const sourceName = article.sources?.name || article.sources?.domain || 'Unknown';
    const pubDate = article.published_at ? new Date(article.published_at).toLocaleDateString('ja-JP') : '不明';
    const flaggedClass = article.flagged ? 'flagged' : '';
    
    return `
        <div class="compact-article-card ${flaggedClass}" data-id="${article.id}">
            <div class="d-flex justify-content-between align-items-start">
                <div class="flex-grow-1 me-3">
                    <div class="d-flex align-items-center gap-2 mb-1 flex-wrap">
                        <span class="badge bg-${getStatusColor(article.status)} status-badge">
                            ${getStatusLabel(article.status)}
                        </span>
                        ${article.flagged ? '<span class="badge bg-danger">重要</span>' : ''}
                        <h6 class="mb-0">
                            <a href="${article.url}" target="_blank" class="text-decoration-none" onclick="event.stopPropagation();">
                                ${escapeHtml(article.title || 'タイトルなし')}
                            </a>
                        </h6>
                    </div>
                    <div class="d-flex align-items-center gap-3 mb-1">
                        <small class="text-muted">📅 ${pubDate}</small>
                        <small class="text-muted">📰 ${sourceName}</small>
                    </div>
                    ${article.comments ? `<small class="text-muted d-block">💬 ${escapeHtml(article.comments.substring(0, 150))}${article.comments.length > 150 ? '...' : ''}</small>` : ''}
                </div>
                <div class="text-end">
                    <button class="btn btn-outline-primary btn-sm edit-article-btn" data-id="${article.id}" onclick="event.stopPropagation();">編集</button>
                </div>
            </div>
        </div>
    `;
}

// 詳細編集用の記事カードを作成
function createDetailArticleCard(article) {
    const sourceName = article.sources?.name || article.sources?.domain || 'Unknown';
    const pubDate = article.published_at ? new Date(article.published_at).toLocaleDateString('ja-JP') : '不明';
    const flaggedClass = article.flagged ? 'flagged' : '';
    
    return `
        <div class="article-card ${flaggedClass}" data-id="${article.id}">
            <div class="d-flex justify-content-between align-items-start mb-2">
                <h5 class="mb-1">
                    <a href="${article.url}" target="_blank" class="text-decoration-none">
                        ${escapeHtml(article.title || 'タイトルなし')}
                    </a>
                </h5>
                <span class="badge bg-${getStatusColor(article.status)} status-badge">
                    ${getStatusLabel(article.status)}
                </span>
            </div>
            
            <div class="article-meta mb-2">
                <span class="me-3">📅 ${pubDate}</span>
                <span class="me-3">📰 ${sourceName}</span>
                ${article.flagged ? '<span class="badge bg-danger">重要</span>' : ''}
            </div>
            
            ${article.body ? `
                <div class="article-body">
                    ${escapeHtml(article.body.substring(0, 500))}${article.body.length > 500 ? '...' : ''}
                </div>
            ` : ''}
            
            <div class="controls">
                <div class="row g-2">
                    <div class="col-md-3">
                        <label class="form-label small">ステータス:</label>
                        <select class="form-select form-select-sm status-select" data-id="${article.id}">
                            <option value="unread" ${article.status === 'unread' ? 'selected' : ''}>未読</option>
                            <option value="reviewed" ${article.status === 'reviewed' ? 'selected' : ''}>確認済み</option>
                            <option value="flagged" ${article.status === 'flagged' ? 'selected' : ''}>フラグ付き</option>
                            <option value="archived" ${article.status === 'archived' ? 'selected' : ''}>アーカイブ</option>
                        </select>
                    </div>
                    <div class="col-md-2">
                        <label class="form-label small">重要:</label>
                        <div class="form-check">
                            <input class="form-check-input flagged-check" type="checkbox" 
                                   data-id="${article.id}" ${article.flagged ? 'checked' : ''}>
                            <label class="form-check-label small">重要フラグ</label>
                        </div>
                    </div>
                    <div class="col-md-7">
                        <label class="form-label small">コメント:</label>
                        <textarea class="form-control form-control-sm comment-textarea" 
                                 data-id="${article.id}" rows="3" 
                                 placeholder="コメントを入力...">${escapeHtml(article.comments || '')}</textarea>
                    </div>
                </div>
                <div class="mt-2">
                    <button class="btn btn-success btn-sm save-btn" data-id="${article.id}">保存</button>
                    ${article.reviewed_at ? `<small class="text-muted ms-2">最終更新: ${new Date(article.reviewed_at).toLocaleString('ja-JP')}</small>` : ''}
                    ${article.last_edited_by ? `<small class="text-info ms-2">編集者: ${article.last_edited_by}</small>` : ''}
                </div>
            </div>
        </div>
    `;
}

// ステータスの色を取得
function getStatusColor(status) {
    const colors = {
        'unread': 'secondary',
        'reviewed': 'success',
        'flagged': 'warning',
        'archived': 'dark'
    };
    return colors[status] || 'secondary';
}

// ステータスのラベルを取得
function getStatusLabel(status) {
    const labels = {
        'unread': '未読',
        'reviewed': '確認済み',
        'flagged': 'フラグ付き',
        'archived': 'アーカイブ'
    };
    return labels[status] || '未読';
}

// イベントリスナーを設定
function setupEventListeners() {
    // フィルター・ソート・表示件数変更時
    setupFilterListeners(['statusFilter', 'flaggedFilter', 'sourceFilter', 'sortOrder', 'itemsPerPage'], () => {
        currentPage = 1; // フィルター変更時はページをリセット
        loadArticlesPage(1);
    });

    // 更新ボタン
    setupRefreshButton(loadArticles);
    
    // ページネーションクリック（下部）
    document.getElementById('paginationList').addEventListener('click', (e) => {
        e.preventDefault();
        const pageLink = e.target.closest('.page-link');
        if (pageLink && !pageLink.parentElement.classList.contains('disabled')) {
            const page = parseInt(pageLink.dataset.page);
            if (!isNaN(page)) {
                loadArticlesPage(page);
            }
        }
    });
    
    // ページネーションクリック（上部）
    document.getElementById('paginationListTop').addEventListener('click', (e) => {
        e.preventDefault();
        const pageLink = e.target.closest('.page-link');
        if (pageLink && !pageLink.parentElement.classList.contains('disabled')) {
            const page = parseInt(pageLink.dataset.page);
            if (!isNaN(page)) {
                loadArticlesPage(page);
            }
        }
    });

    // コンパクトカードクリックのイベント委譲
    document.getElementById('articlesContainer').addEventListener('click', (e) => {
        const card = e.target.closest('.compact-article-card');
        if (card && !e.target.classList.contains('edit-article-btn')) {
            const articleId = card.dataset.id;
            openEditMode(articleId);
        }
    });

    // 編集ボタンクリックのイベント委譲
    document.getElementById('articlesContainer').addEventListener('click', (e) => {
        if (e.target.classList.contains('edit-article-btn')) {
            const articleId = e.target.dataset.id;
            openEditMode(articleId);
        }
    });

    // 編集モードのイベント委譲
    document.getElementById('editModeContainer').addEventListener('click', async (e) => {
        if (e.target.classList.contains('save-btn')) {
            await saveArticle(e.target.dataset.id);
        } else if (e.target.classList.contains('btn-close-edit')) {
            closeEditMode();
        }
    });

    // ページネーションクリック
    setupPagination('#articlesContainer', renderArticles);
}

// 記事を保存
async function saveArticle(articleId) {
    // 編集モードのカードから値を取得
    const editCard = document.querySelector(`#editModeContainer [data-id="${articleId}"]`);
    if (!editCard) {
        console.error('編集カードが見つかりません');
        return;
    }
    
    const status = editCard.querySelector('.status-select').value;
    const flagged = editCard.querySelector('.flagged-check').checked;
    const comments = editCard.querySelector('.comment-textarea').value;
    
    try {
        const currentUser = getCurrentUser();
        const { error } = await supabase
            .from('items')
            .update({
                status: status,
                flagged: flagged,
                comments: comments || null,
                reviewed_at: new Date().toISOString(),
                last_edited_by: currentUser ? currentUser.userId : null
            })
            .eq('id', articleId);
        
        if (error) throw error;
        
        // UIを更新
        const saveBtn = editCard.querySelector('.save-btn');
        const originalText = saveBtn.textContent;
        saveBtn.textContent = '保存済み';
        saveBtn.classList.replace('btn-success', 'btn-outline-success');
        
        setTimeout(() => {
            saveBtn.textContent = originalText;
            saveBtn.classList.replace('btn-outline-success', 'btn-success');
        }, 2000);
        
        // 記事データを更新
        const articleIndex = articles.findIndex(a => a.id == articleId);
        if (articleIndex !== -1) {
            articles[articleIndex].status = status;
            articles[articleIndex].flagged = flagged;
            articles[articleIndex].comments = comments || null;
            articles[articleIndex].reviewed_at = new Date().toISOString();
            articles[articleIndex].last_edited_by = currentUser ? currentUser.userId : null;
        }
        
    } catch (error) {
        console.error('保存エラー:', error);
        alert('保存に失敗しました: ' + error.message);
    }
}

// 編集モードを開く
function openEditMode(articleId) {
    const article = articles.find(a => a.id == articleId);
    if (!article) return;

    // 編集カード作成
    document.getElementById('editCard').innerHTML = createDetailArticleCard(article);

    // 表示切り替え
    document.getElementById('articlesContainer').style.display = 'none';
    document.getElementById('pagination').style.display = 'none';
    document.getElementById('editModeContainer').style.display = 'block';
}

// 編集モードを閉じる
function closeEditMode() {
    document.getElementById('editModeContainer').style.display = 'none';
    document.getElementById('articlesContainer').style.display = 'block';
    document.getElementById('pagination').style.display = 'block';
}