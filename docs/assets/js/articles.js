// CFRP Monitor - 記事管理ページJavaScript

let articles = [];
let sources = [];
let currentPage = 1;

// 初期化
document.addEventListener('DOMContentLoaded', async () => {
    await loadSources();
    await loadArticles();
    setupEventListeners();
});

// ソース一覧を読み込み
async function loadSources() {
    try {
        const { data, error } = await supabase
            .from('sources')
            .select('id, name, domain')
            .order('name');
        
        if (error) throw error;
        
        sources = data || [];
        populateSourceFilter();
    } catch (error) {
        console.error('ソース読み込みエラー:', error);
    }
}

// 記事一覧を読み込み
async function loadArticles() {
    try {
        const { data, error } = await supabase
            .from('items')
            .select(`
                *,
                sources(name, domain)
            `)
            .order('pub_date', { ascending: false })
            .limit(100);
        
        if (error) throw error;
        
        articles = data || [];
        currentPage = 1; // ページをリセット
        renderArticles();
        document.getElementById('loading').style.display = 'none';
        document.getElementById('articlesContainer').style.display = 'block';
        document.getElementById('pagination').style.display = 'block';
    } catch (error) {
        console.error('記事読み込みエラー:', error);
        document.getElementById('loading').innerHTML = 
            '<div class="alert alert-danger">記事の読み込みに失敗しました</div>';
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

// 記事を表示
function renderArticles() {
    const container = document.getElementById('articlesContainer');
    const filteredArticles = filterAndSortArticles();
    const itemsPerPage = parseInt(document.getElementById('itemsPerPage').value);
    
    if (filteredArticles.length === 0) {
        container.innerHTML = '<div class="alert alert-info">該当する記事がありません</div>';
        document.getElementById('pagination').style.display = 'none';
        return;
    }

    // ページネーション計算
    const totalPages = Math.ceil(filteredArticles.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const paginatedArticles = filteredArticles.slice(startIndex, endIndex);

    // ページが範囲外の場合は1ページ目に戻す
    if (currentPage > totalPages && totalPages > 0) {
        currentPage = 1;
        renderArticles();
        return;
    }

    // 記事表示
    container.innerHTML = paginatedArticles.map(article => createCompactArticleCard(article)).join('');
    
    // ページネーション表示
    renderPagination(filteredArticles.length, itemsPerPage, currentPage);
    document.getElementById('pagination').style.display = 'block';
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
                    ${article.reviewed_at ? `<small class="text-muted ms-2">最終更新: ${new Date(article.reviewed_at).toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' })}</small>` : ''}
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
    setupFilterListeners(['statusFilter', 'flaggedFilter', 'sourceFilter', 'sortOrder', 'itemsPerPage'], renderArticles);

    // 更新ボタン
    setupRefreshButton(loadArticles);

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
                reviewed_at: new Date(new Date().getTime() + (9 * 60 * 60 * 1000)).toISOString(),
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
            articles[articleIndex].reviewed_at = new Date(new Date().getTime() + (9 * 60 * 60 * 1000)).toISOString();
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