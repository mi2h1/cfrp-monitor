// CFRP Monitor - 記事詳細ページJavaScript

let currentArticle = null;
let articleComments = [];
let authToken = null;
let userFeatures = null;

// article-detail.jsの初期化関数（page-init.jsから呼び出される）
async function initializeArticleDetailApp() {
    // 認証チェックはメインページのスクリプトで実行済み
    authToken = localStorage.getItem('auth_token');
    userFeatures = window.userFeatures;
    
    // URLパラメータから記事IDを取得
    const urlParams = new URLSearchParams(window.location.search);
    const articleId = urlParams.get('id');
    
    if (!articleId) {
        document.getElementById('loading').innerHTML = 
            '<div class="alert alert-danger">記事IDが指定されていません</div>';
        return;
    }
    
    // 記事詳細とコメントを並列で読み込み
    const [articleResult, commentsResult] = await Promise.allSettled([
        loadArticleDetail(articleId),
        loadArticleComments(articleId)
    ]);
    
    if (articleResult.status === 'rejected') {
        document.getElementById('loading').innerHTML = 
            '<div class="alert alert-danger">記事の読み込みに失敗しました</div>';
        return;
    }
    
    if (commentsResult.status === 'rejected') {
        console.error('コメント読み込みエラー:', commentsResult.reason);
        // コメントの読み込みが失敗してもページは表示
    }
    
    // 記事詳細を表示
    renderArticleDetail();
    renderComments();
    
    // ローディングを非表示、コンテンツを表示
    document.getElementById('loading').style.display = 'none';
    document.getElementById('articleDetailContainer').style.display = 'block';
}

// 記事詳細を読み込み
async function loadArticleDetail(articleId) {
    try {
        const response = await fetch(`/api/articles?id=${articleId}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (!data.success || !data.articles?.length) {
            throw new Error('記事が見つかりません');
        }
        
        currentArticle = data.articles[0];
        
    } catch (error) {
        console.error('記事詳細読み込みエラー:', error);
        throw error;
    }
}

// 記事コメントを読み込み
async function loadArticleComments(articleId) {
    try {
        const response = await fetch(`/api/article-comments?article_id=${articleId}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            articleComments = data.comments || [];
        } else {
            console.error('コメント読み込みエラー:', data.error);
            articleComments = [];
        }
        
    } catch (error) {
        console.error('コメント読み込みエラー:', error);
        articleComments = [];
    }
}

// 記事詳細を表示
function renderArticleDetail() {
    if (!currentArticle) return;
    
    const container = document.getElementById('articleDetailContainer');
    
    const sourceName = currentArticle.sources?.name || currentArticle.sources?.domain || 'Unknown';
    const pubDate = currentArticle.published_at ? formatJSTDisplay(currentArticle.published_at) : '不明';
    
    container.innerHTML = `
        <div class="row">
            <div class="col-12">
                <!-- 記事ヘッダー -->
                <div class="card mb-4">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h4 class="mb-0">
                            ${currentArticle.flagged ? '<span class="badge bg-danger me-2">重要</span>' : ''}
                            記事詳細
                        </h4>
                        <div class="btn-group">
                            <button class="btn btn-outline-secondary btn-sm" onclick="editArticle()">
                                <i class="fas fa-edit"></i> 編集
                            </button>
                            <button class="btn btn-outline-primary btn-sm" onclick="window.open('${escapeHtml(currentArticle.url)}', '_blank')">
                                <i class="fas fa-external-link-alt"></i> 元記事を開く
                            </button>
                        </div>
                    </div>
                    <div class="card-body">
                        <h2 class="card-title">${escapeHtml(currentArticle.title || 'タイトルなし')}</h2>
                        
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <small class="text-muted">
                                    <i class="fas fa-rss"></i> 情報源: ${sourceName}
                                </small>
                            </div>
                            <div class="col-md-6 text-md-end">
                                <small class="text-muted">
                                    <i class="fas fa-calendar-alt"></i> 公開日: ${pubDate}
                                </small>
                            </div>
                        </div>
                        
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <span class="badge bg-${getStatusColor(currentArticle.status)}">
                                    ${getStatusLabel(currentArticle.status)}
                                </span>
                            </div>
                            <div class="col-md-6 text-md-end">
                                <small class="text-muted">
                                    <i class="fas fa-link"></i> 
                                    <a href="${currentArticle.url}" target="_blank" class="text-decoration-none">
                                        ${currentArticle.url}
                                    </a>
                                </small>
                            </div>
                        </div>
                        
                        ${currentArticle.body ? `
                            <div class="article-body mb-3">
                                <h5>記事内容</h5>
                                <div class="border rounded p-3 bg-light">
                                    ${escapeHtml(currentArticle.body).replace(/\\n/g, '<br>')}
                                </div>
                            </div>
                        ` : ''}
                        
                        ${currentArticle.comments ? `
                            <div class="article-comments mb-3">
                                <h5>備考</h5>
                                <div class="border rounded p-3 bg-light">
                                    ${escapeHtml(currentArticle.comments).replace(/\\n/g, '<br>')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
        
        <!-- コメント・スレッド -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">
                            <i class="fas fa-comments"></i> コメント
                            <span class="badge bg-secondary ms-2">${articleComments.length}</span>
                        </h5>
                    </div>
                    <div class="card-body">
                        <!-- 新規コメント投稿フォーム -->
                        <div class="mb-4">
                            <h6>コメントを投稿</h6>
                            <div class="form-group mb-2">
                                <textarea class="form-control" id="newComment" rows="3" placeholder="コメントを入力してください..."></textarea>
                            </div>
                            <button class="btn btn-primary" onclick="postComment('${currentArticle.id}')">
                                <i class="fas fa-paper-plane"></i> コメントを投稿
                            </button>
                        </div>
                        
                        <!-- コメント一覧 -->
                        <div id="commentsContainer">
                            <!-- JavaScript で動的に生成 -->
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// コメントを表示
function renderComments() {
    const container = document.getElementById('commentsContainer');
    
    if (articleComments.length === 0) {
        container.innerHTML = '<div class="text-muted text-center py-3">まだコメントはありません</div>';
        return;
    }
    
    // コメントツリーを構築
    const commentTree = buildCommentTree(articleComments);
    
    // コメントを表示
    const commentsHtml = commentTree.map((comment, index, array) => {
        const isLastRoot = index === array.length - 1;
        return renderCommentCard(comment, 0, isLastRoot);
    }).join('');
    container.innerHTML = commentsHtml;
}

// その他の関数は articles.js から移行
// buildCommentTree, renderCommentCard, postComment, showReplyForm等

// ステータスの色を取得
function getStatusColor(status) {
    const colors = {
        'unread': 'secondary',
        'reviewed': 'success',
        'flagged': 'warning',
        'archived': 'info'
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

// 記事編集（今後実装）
function editArticle() {
    alert('記事編集機能は今後実装予定です');
}

// HTMLエスケープ関数
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}