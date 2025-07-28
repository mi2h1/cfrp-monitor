// CFRP Monitor - 記事管理ページJavaScript

let articles = [];
let sources = [];
let currentPage = 1;
let authToken = null;
let userFeatures = null;

// articles.jsの初期化関数（page-init.jsから呼び出される）
async function initializeArticlesApp() {
    // 認証チェックはメインページのスクリプトで実行済み
    authToken = localStorage.getItem('auth_token');
    
    // userFeaturesを再取得して確実に設定
    userFeatures = window.userFeatures;
    
    // デバッグ: userFeaturesの内容を確認
    console.log('Debug - Articles initializeArticlesApp:', {
        userFeatures: userFeatures,
        windowUserFeatures: window.userFeatures,
        authToken: authToken ? 'present' : 'missing'
    });
    
    await loadSources();
    await loadArticles();
    setupEventListeners();
}

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
        // ローディング状態を表示
        showLoadingState();
        
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
            hideLoadingState();
            throw new Error(data.error || '記事の読み込みに失敗しました');
        }
        
        articles = data.articles || [];
        currentPage = page;
        
        // ローディング状態を非表示
        hideLoadingState();
        
        renderArticles();
        renderPagination(totalCount, itemsPerPage, page);
        
    } catch (error) {
        console.error('記事ページ読み込みエラー:', error);
        hideLoadingState();
        document.getElementById('articlesContainer').innerHTML = '<div class="alert alert-danger">記事の読み込みに失敗しました: ' + error.message + '</div>';
    }
}

// ローディング状態管理関数
function showLoadingState() {
    const container = document.getElementById('articlesContainer');
    container.innerHTML = `
        <div class="d-flex justify-content-center align-items-center" style="min-height: 300px;">
            <div class="text-center">
                <div class="spinner-border text-primary mb-3" role="status">
                    <span class="visually-hidden">読み込み中...</span>
                </div>
                <p class="text-muted">記事を読み込んでいます...</p>
            </div>
        </div>
    `;
}

function hideLoadingState() {
    // 特に何もしない（renderArticles()で内容が置き換わるため）
}

// タスクログ機能は削除（APIで実装しないため）

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

    // テーブル形式で記事表示
    container.innerHTML = `
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th style="width: 90px;">ステータス</th>
                        <th>タイトル</th>
                        <th style="width: 120px;">情報源</th>
                        <th style="width: 100px;">公開日</th>
                        <th style="width: 80px;">コメント</th>
                    </tr>
                </thead>
                <tbody>
                    ${paginatedArticles.map(article => createArticleTableRow(article)).join('')}
                </tbody>
            </table>
        </div>
    `;
    
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

    // テーブル形式で記事表示
    container.innerHTML = `
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th style="width: 90px;">ステータス</th>
                        <th>タイトル</th>
                        <th style="width: 120px;">情報源</th>
                        <th style="width: 100px;">公開日</th>
                        <th style="width: 80px;">コメント</th>
                    </tr>
                </thead>
                <tbody>
                    ${articles.map(article => createArticleTableRow(article)).join('')}
                </tbody>
            </table>
        </div>
    `;
    
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

// 記事テーブル行を作成
function createArticleTableRow(article) {
    const sourceName = article.sources?.name || article.sources?.domain || 'Unknown';
    const pubDate = article.published_at ? formatJSTDate(article.published_at) : '不明';
    const flaggedClass = article.flagged ? 'table-warning' : '';
    
    return `
        <tr class="${flaggedClass}" data-id="${article.id}" style="cursor: pointer;">
            <td>
                <span class="badge bg-${getStatusColor(article.status)} status-badge">
                    ${getStatusLabel(article.status)}
                </span>
            </td>
            <td>
                <div class="d-flex align-items-start gap-2">
                    ${article.flagged ? '<span class="badge bg-danger flex-shrink-0">重要</span>' : ''}
                    <div class="flex-grow-1">
                        <div class="fw-medium">${escapeHtml(article.title || 'タイトルなし')}</div>
                        <div class="small text-muted text-truncate" style="max-width: 400px;" title="${escapeHtml(article.url)}">${escapeHtml(article.url)}</div>
                        ${article.comments ? `<div class="small text-muted mt-1"><i class="fas fa-sticky-note"></i> ${escapeHtml(article.comments.substring(0, 100))}${article.comments.length > 100 ? '...' : ''}</div>` : ''}
                    </div>
                </div>
            </td>
            <td>
                <small class="text-muted">
                    <i class="fas fa-rss"></i> ${sourceName}
                </small>
            </td>
            <td>
                <small class="text-muted">
                    <i class="fas fa-calendar-alt"></i> ${pubDate}
                </small>
            </td>
            <td class="text-center">
                <span class="badge bg-secondary">
                    <i class="fas fa-comment"></i> ${article.comment_count || 0}
                </span>
            </td>
        </tr>
    `;
}

// 詳細編集用の記事カードを作成
function createDetailArticleCard(article) {
    const sourceName = article.sources?.name || article.sources?.domain || 'Unknown';
    const pubDate = article.published_at ? formatJSTDate(article.published_at) : '不明';
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
                <span class="me-3"><i class="fas fa-calendar-alt"></i> ${pubDate}</span>
                <span class="me-3"><i class="fas fa-rss"></i> ${sourceName}</span>
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
                        <label class="form-label small">備考:</label>
                        <textarea class="form-control form-control-sm comment-textarea" 
                                 data-id="${article.id}" rows="3" 
                                 placeholder="備考を入力...">${escapeHtml(article.comments || '')}</textarea>
                    </div>
                </div>
                <div class="mt-2">
                    <button class="btn btn-success btn-sm save-btn" data-id="${article.id}">保存</button>
                    ${article.reviewed_at ? `<small class="text-muted ms-2">最終更新: ${formatJSTDisplay(article.reviewed_at)}</small>` : ''}
                    ${article.last_edited_by ? `<small class="text-info ms-2">編集者: ${article.last_edited_by}</small>` : ''}
                </div>
            </div>
            
            <!-- コメントセクション -->
            <div class="mt-4 border-top pt-4">
                <h6 class="mb-3"><i class="fas fa-comments"></i> コメント</h6>
                
                <!-- コメント投稿フォーム -->
                <div class="comment-form mb-4">
                    <textarea class="form-control mb-2" id="newComment" rows="3" placeholder="コメントを投稿..."></textarea>
                    <button class="btn btn-primary btn-sm" onclick="postComment('${article.id}')">
                        <i class="fas fa-paper-plane"></i> コメントを投稿
                    </button>
                </div>
                
                <!-- コメント一覧 -->
                <div id="commentsContainer" class="comments-container">
                    <div class="text-center text-muted">
                        <i class="fas fa-spinner fa-spin"></i> コメントを読み込み中...
                    </div>
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

    // テーブル行クリックのイベント委譲
    document.getElementById('articlesContainer').addEventListener('click', (e) => {
        const row = e.target.closest('tr[data-id]');
        if (row) {
            const articleId = row.dataset.id;
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
        // TODO: API経由で記事を更新する処理に置き換える
        const updateData = {
            status: status,
            flagged: flagged,
            comments: comments || null
        };
        
        const response = await fetch(`/api/articles?id=${articleId}`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updateData)
        });
        
        const data = await response.json();
        if (!data.success) {
            throw new Error(data.error || '更新に失敗しました');
        }
        
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
    
    // コメントを読み込む
    loadArticleComments(articleId);
}

// 編集モードを閉じる
function closeEditMode() {
    document.getElementById('editModeContainer').style.display = 'none';
    document.getElementById('articlesContainer').style.display = 'block';
    document.getElementById('pagination').style.display = 'block';
}

// ===========================================
// コメント機能
// ===========================================

// 記事のコメントを読み込み
async function loadArticleComments(articleId) {
    try {
        const response = await fetch(`/api/article-comments?article_id=${articleId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            renderComments(data.comments || []);
        } else {
            console.error('コメント読み込みエラー:', data.error);
            document.getElementById('commentsContainer').innerHTML = 
                '<div class="alert alert-warning">コメントの読み込みに失敗しました</div>';
        }
    } catch (error) {
        console.error('コメント読み込みエラー:', error);
        document.getElementById('commentsContainer').innerHTML = 
            '<div class="alert alert-danger">コメントの読み込み中にエラーが発生しました</div>';
    }
}

// コメントを表示
function renderComments(comments) {
    const container = document.getElementById('commentsContainer');
    
    // デバッグ: コメントデータを確認
    console.log('Debug - renderComments:', {
        comments: comments,
        userFeatures: userFeatures
    });
    
    if (comments.length === 0) {
        container.innerHTML = '<div class="text-muted text-center">まだコメントがありません</div>';
        return;
    }
    
    // コメントを階層構造に変換
    const commentTree = buildCommentTree(comments);
    
    // HTML生成
    const commentsHtml = commentTree.map(comment => renderCommentCard(comment)).join('');
    container.innerHTML = commentsHtml;
}

// コメントの階層構造を構築（フラット表示）
function buildCommentTree(comments) {
    const rootComments = [];
    const commentsByRoot = {};
    
    // ルートコメントとその返信をグループ化
    comments.forEach(comment => {
        if (!comment.parent_comment_id) {
            // ルートコメント
            commentsByRoot[comment.id] = {
                root: { ...comment },
                replies: []
            };
        }
    });
    
    // 返信コメントを適切なルートに適用
    comments.forEach(comment => {
        if (comment.parent_comment_id) {
            // 直接の親がルートコメントかどうかチェック
            if (commentsByRoot[comment.parent_comment_id]) {
                // 直接の親がルートコメントの場合
                commentsByRoot[comment.parent_comment_id].replies.push({ ...comment });
            } else {
                // 親が返信コメントの場合、そのルートコメントを探す
                const parentComment = comments.find(c => c.id === comment.parent_comment_id);
                if (parentComment) {
                    // 親コメントのルートを再帰的に探す
                    const rootId = findRootCommentId(parentComment, comments);
                    if (commentsByRoot[rootId]) {
                        commentsByRoot[rootId].replies.push({ ...comment });
                    }
                }
            }
        }
    });
    
    // ルートコメントを作成日時でソート
    const sortedRootIds = Object.keys(commentsByRoot).sort((a, b) => {
        const dateA = new Date(commentsByRoot[a].root.created_at);
        const dateB = new Date(commentsByRoot[b].root.created_at);
        return dateB - dateA; // 新しい順
    });
    
    // 結果を構築
    sortedRootIds.forEach(rootId => {
        const group = commentsByRoot[rootId];
        // 返信を時間順でソート
        group.replies.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
        
        rootComments.push({
            ...group.root,
            replies: group.replies
        });
    });
    
    return rootComments;
}

// ルートコメントIDを再帰的に探す
function findRootCommentId(comment, allComments) {
    if (!comment.parent_comment_id) {
        return comment.id;
    }
    const parent = allComments.find(c => c.id === comment.parent_comment_id);
    return parent ? findRootCommentId(parent, allComments) : comment.id;
}

// コメントカードをレンダリング（フラット表示）
function renderCommentCard(comment, level = 0) {
    const marginLeft = level * 20;
    const isDeleted = comment.is_deleted;
    const isRootComment = level === 0;
    // 改行を<br>タグに変換
    const commentText = isDeleted ? '<em class="text-muted">このコメントは削除されました</em>' : escapeHtml(comment.comment).replace(/\n/g, '<br>');
    
    // 編集済み判定を改善（時刻比較を正確に）
    let isEdited = false;
    if (comment.created_at && comment.updated_at) {
        const createdTime = new Date(comment.created_at).getTime();
        const updatedTime = new Date(comment.updated_at).getTime();
        isEdited = Math.abs(updatedTime - createdTime) > 2000; // 2秒以上の差があれば編集済み
    }
    
    // 現在のユーザーがコメント投稿者かどうか
    const currentUser = userFeatures ? userFeatures.user_id : null;
    const isOwnComment = currentUser === comment.user_id;
    
    // デバッグ情報をコンソールに出力
    console.log('Debug - renderCommentCard:', {
        currentUser: currentUser,
        commentUserId: comment.user_id,
        isOwnComment: isOwnComment,
        userFeatures: userFeatures,
        windowUserFeatures: window.userFeatures,
        isDeleted: isDeleted,
        comment: comment
    });
    
    let html = `
        <div class="comment-card mb-3 position-relative" style="margin-left: ${marginLeft}px;" data-comment-id="${comment.id}">
            ${level > 0 ? `
                <div class="comment-tree-line" style="position: absolute; left: -10px; top: 0; bottom: 0; width: 2px; background-color: #dee2e6;"></div>
                <div class="comment-tree-branch" style="position: absolute; left: -10px; top: 20px; width: 15px; height: 2px; background-color: #dee2e6;"></div>
            ` : ''}
            <div class="card card-body py-2 px-3">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="comment-content flex-grow-1">
                        <div class="comment-meta mb-1 d-flex align-items-center">
                            <strong class="me-2">${escapeHtml(comment.user_id)}</strong>
                            <small class="text-muted me-1">${formatJSTDisplay(comment.created_at)}</small>
                            ${isEdited ? '<small class="text-info me-2">(編集済み)</small>' : ''}
                            ${isOwnComment && !isDeleted ? `
                                <button class="btn btn-link btn-sm p-0 ms-1 edit-meta-btn" onclick="showCommentEditForm('${comment.id}')" style="font-size: 0.75rem; line-height: 1; color: #6c757d;" title="コメントを編集">
                                    <i class="fas fa-edit"></i>
                                </button>
                            ` : '<!-- Debug: No edit button - currentUser: ' + currentUser + ', commentUserId: ' + comment.user_id + ', isOwnComment: ' + isOwnComment + ', isDeleted: ' + isDeleted + ' -->'}
                        </div>
                        <div class="comment-text" id="commentText-${comment.id}">${commentText}</div>
                        
                        <!-- 編集フォーム（初期非表示） -->
                        <div class="edit-form mt-2" id="editForm-${comment.id}" style="display: none;">
                            <textarea class="form-control mb-2" id="editText-${comment.id}" rows="3">${escapeHtml(comment.comment)}</textarea>
                            <div class="d-flex gap-2">
                                <button class="btn btn-success btn-sm" onclick="submitCommentEdit('${comment.id}')">
                                    <i class="fas fa-save"></i> 保存
                                </button>
                                <button class="btn btn-outline-secondary btn-sm" onclick="cancelCommentEdit('${comment.id}')">
                                    キャンセル
                                </button>
                            </div>
                        </div>
                    </div>
                    ${!isDeleted ? `
                        <div class="comment-actions ms-2">
                            <button class="btn btn-outline-primary btn-sm reply-btn" onclick="showReplyForm('${comment.id}')">
                                <i class="fas fa-reply"></i> 返信
                            </button>
                        </div>
                    ` : ''}
                </div>
            </div>
            
            <!-- 返信フォーム -->
            <div class="reply-form mt-2" id="replyForm-${comment.id}" style="display: none; margin-left: ${marginLeft + 20}px;">
                <div class="card card-body py-2 px-3 bg-light">
                    <div class="mb-2">
                        <small class="text-muted">
                            <i class="fas fa-reply"></i> <strong>${escapeHtml(comment.user_id)}</strong> への返信
                        </small>
                    </div>
                    <textarea class="form-control mb-2" id="replyText-${comment.id}" rows="2" placeholder="返信を入力..."></textarea>
                    <div class="d-flex gap-2">
                        <button class="btn btn-primary btn-sm" onclick="submitReply('${comment.id}')">
                            <i class="fas fa-paper-plane"></i> 返信を投稿
                        </button>
                        <button class="btn btn-outline-secondary btn-sm" onclick="hideReplyForm('${comment.id}')">
                            キャンセル
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 返信があればフラットに追加（全て同じ階層）
    if (comment.replies && comment.replies.length > 0) {
        const repliesHtml = comment.replies.map(reply => renderCommentCard(reply, 1)).join('');
        html += repliesHtml;
    }
    
    return html;
}

// コメントを投稿
async function postComment(articleId, parentCommentId = null) {
    const commentText = document.getElementById('newComment').value.trim();
    
    if (!commentText) {
        alert('コメントを入力してください');
        return;
    }
    
    try {
        const response = await fetch('/api/article-comments', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                article_id: articleId,
                parent_comment_id: parentCommentId,
                comment: commentText
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 入力欄をクリア
            document.getElementById('newComment').value = '';
            
            // コメントを再読み込み
            loadArticleComments(articleId);
            
            // 記事一覧のコメント数も更新
            const article = articles.find(a => a.id === articleId);
            if (article) {
                article.comment_count = (article.comment_count || 0) + 1;
            }
        } else {
            alert('コメントの投稿に失敗しました: ' + data.error);
        }
    } catch (error) {
        console.error('コメント投稿エラー:', error);
        alert('コメントの投稿中にエラーが発生しました');
    }
}

// 返信フォームを表示
function showReplyForm(commentId) {
    // 他の返信フォームを非表示にする
    document.querySelectorAll('.reply-form').forEach(form => {
        form.style.display = 'none';
    });
    
    // 指定されたコメントの返信フォームを表示
    const replyForm = document.getElementById(`replyForm-${commentId}`);
    if (replyForm) {
        replyForm.style.display = 'block';
        
        // テキストエリアにフォーカス
        const textarea = document.getElementById(`replyText-${commentId}`);
        if (textarea) {
            textarea.focus();
        }
    }
}

// 返信フォームを非表示
function hideReplyForm(commentId) {
    const replyForm = document.getElementById(`replyForm-${commentId}`);
    if (replyForm) {
        replyForm.style.display = 'none';
        
        // テキストエリアをクリア
        const textarea = document.getElementById(`replyText-${commentId}`);
        if (textarea) {
            textarea.value = '';
        }
    }
}

// 返信を投稿（フラット表示）
async function submitReply(parentCommentId) {
    const textarea = document.getElementById(`replyText-${parentCommentId}`);
    if (!textarea) return;
    
    const replyText = textarea.value.trim();
    if (!replyText) {
        alert('返信内容を入力してください');
        return;
    }
    
    // 現在表示中の記事IDを取得
    const articleCard = document.querySelector('#editModeContainer .article-card');
    if (!articleCard) return;
    
    const articleId = articleCard.dataset.id;
    
    // 投稿ボタンを無効化
    const submitBtn = textarea.parentElement.querySelector('.btn-primary');
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 投稿中...';
    
    try {
        // 親コメントIDをそのまま送信（APIでルートコメントを探す処理を実施）
        const response = await fetch('/api/article-comments', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                article_id: articleId,
                parent_comment_id: parentCommentId,
                comment: replyText
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 返信フォームを非表示にしてクリア
            hideReplyForm(parentCommentId);
            
            // コメントを再読み込み
            loadArticleComments(articleId);
            
            // 記事一覧のコメント数も更新
            const article = articles.find(a => a.id === articleId);
            if (article) {
                article.comment_count = (article.comment_count || 0) + 1;
            }
        } else {
            alert('返信の投稿に失敗しました: ' + data.error);
        }
    } catch (error) {
        console.error('返信投稿エラー:', error);
        alert('返信の投稿中にエラーが発生しました');
    } finally {
        // ボタンを元に戻す
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

// ===========================================
// コメント編集機能
// ===========================================

// コメント編集フォームを表示
function showCommentEditForm(commentId) {
    // 他の編集フォームを非表示
    document.querySelectorAll('.edit-form').forEach(form => {
        form.style.display = 'none';
    });
    
    // 編集フォームを表示
    const editForm = document.getElementById(`editForm-${commentId}`);
    const commentText = document.getElementById(`commentText-${commentId}`);
    const editBtn = document.querySelector(`[onclick="showCommentEditForm('${commentId}')"]`);
    
    if (editForm && commentText && editBtn) {
        editForm.style.display = 'block';
        commentText.style.display = 'none';
        editBtn.style.display = 'none';
        
        // テキストエリアにフォーカス
        const textarea = document.getElementById(`editText-${commentId}`);
        if (textarea) {
            textarea.focus();
        }
    }
}

// コメント編集をキャンセル
function cancelCommentEdit(commentId) {
    const editForm = document.getElementById(`editForm-${commentId}`);
    const commentText = document.getElementById(`commentText-${commentId}`);
    const editBtn = document.querySelector(`[onclick="showCommentEditForm('${commentId}')"]`);
    
    if (editForm && commentText && editBtn) {
        editForm.style.display = 'none';
        commentText.style.display = 'block';
        editBtn.style.display = 'inline-block';
    }
}

// コメント編集を投稿
async function submitCommentEdit(commentId) {
    const textarea = document.getElementById(`editText-${commentId}`);
    if (!textarea) return;
    
    const editedText = textarea.value.trim();
    if (!editedText) {
        alert('コメント内容を入力してください');
        return;
    }
    
    // 現在表示中の記事IDを取得
    const articleCard = document.querySelector('#editModeContainer .article-card');
    if (!articleCard) return;
    
    const articleId = articleCard.dataset.id;
    
    // 保存ボタンを無効化
    const saveBtn = textarea.parentElement.querySelector('.btn-success');
    const originalText = saveBtn.textContent;
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 保存中...';
    
    try {
        const response = await fetch('/api/article-comments', {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                comment_id: commentId,
                comment: editedText
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 編集フォームを非表示
            cancelCommentEdit(commentId);
            
            // コメントを再読み込み
            loadArticleComments(articleId);
        } else {
            alert('コメントの編集に失敗しました: ' + data.error);
        }
    } catch (error) {
        console.error('コメント編集エラー:', error);
        alert('コメントの編集中にエラーが発生しました');
    } finally {
        // ボタンを元に戻す
        saveBtn.disabled = false;
        saveBtn.innerHTML = originalText;
    }
}

