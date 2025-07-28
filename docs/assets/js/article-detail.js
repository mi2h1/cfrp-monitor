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
                if (parentComment && parentComment.parent_comment_id) {
                    // 親の親（ルートコメント）があれば、そこに追加
                    if (commentsByRoot[parentComment.parent_comment_id]) {
                        commentsByRoot[parentComment.parent_comment_id].replies.push({ ...comment });
                    }
                } else {
                    // ルートコメントが見つからない場合は、新しいルートコメントとして扱う
                    if (parentComment) {
                        commentsByRoot[parentComment.id] = {
                            root: { ...parentComment },
                            replies: [{ ...comment }]
                        };
                    }
                }
            }
        }
    });
    
    // 結果を配列に変換
    Object.values(commentsByRoot).forEach(group => {
        const rootWithReplies = { ...group.root };
        if (group.replies.length > 0) {
            rootWithReplies.replies = group.replies.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
        }
        rootComments.push(rootWithReplies);
    });
    
    // ルートコメントを作成日時順でソート
    return rootComments.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
}

// コメントカードをレンダリング
function renderCommentCard(comment, level = 0, isLast = false, parentHasMoreSiblings = false) {
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
    let currentUser = null;
    
    // 1. window.currentUserからユーザーIDを取得
    if (window.currentUser) {
        currentUser = window.currentUser.user_id || window.currentUser.id || window.currentUser.username;
    }
    
    // 2. フォールバック: userFeaturesから取得
    if (!currentUser && userFeatures) {
        currentUser = userFeatures.user_id || userFeatures.userId || userFeatures.current_user || userFeatures.username;
    }
    
    // 3. フォールバック: JWTトークンからユーザーIDを取得
    if (!currentUser && authToken) {
        try {
            const payload = JSON.parse(atob(authToken.split('.')[1]));
            currentUser = payload.user_id || payload.username || payload.sub;
        } catch (e) {
            console.error('JWT decode error:', e);
        }
    }
    
    const isOwnComment = currentUser && (currentUser === comment.user_id);
    
    let html = `
        <div class="comment-card mb-3" style="margin-left: ${marginLeft}px;" data-comment-id="${comment.id}">
            <div class="card card-body py-2 px-3">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="comment-content flex-grow-1">
                        <div class="comment-meta mb-1 d-flex align-items-center">
                            <strong class="me-2">${escapeHtml(comment.user_id)}</strong>
                            <small class="text-muted me-1">${formatJSTDisplay(comment.created_at)}</small>
                            ${isEdited ? '<small class="text-info me-2">(編集済み)</small>' : ''}
                            ${isOwnComment && !isDeleted ? `
                                <button class="btn btn-link btn-sm p-1 ms-1 edit-meta-btn" onclick="showCommentEditForm('${comment.id}')" style="font-size: 0.75rem; line-height: 1; color: #6c757d;" title="コメントを編集">
                                    <i class="fas fa-edit me-1"></i>編集
                                </button>
                            ` : ''}
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
                    ${!isDeleted && level === 0 && (!comment.replies || comment.replies.length === 0) ? `
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
    
    // 返信があれば引用スタイルのコンテナで囲む
    if (comment.replies && comment.replies.length > 0) {
        const repliesHtml = comment.replies.map((reply, index, array) => {
            const isLastReply = index === array.length - 1;
            return renderCommentCard(reply, 1, isLastReply);
        }).join('');
        
        // 返信群の最後に1つの返信ボタンを追加（適切な間隔で配置）
        const groupReplyButton = `
            <div class="group-reply-container mt-3 mb-2" style="margin-left: 20px; padding-top: 10px; border-top: 1px solid #f0f0f0;">
                <button class="btn btn-outline-primary btn-sm reply-btn" onclick="showReplyForm('${comment.id}')">
                    <i class="fas fa-reply"></i> 返信
                </button>
            </div>
        `;
        
        html += `
            <div class="replies-container">
                ${repliesHtml}
                ${groupReplyButton}
            </div>
        `;
    }
    
    return html;
}

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
            // 新規コメントフォームをクリア
            document.getElementById('newComment').value = '';
            
            // コメント一覧を再読み込み
            await loadArticleComments(articleId);
            renderComments();
            
            alert('コメントを投稿しました');
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
    // 他の返信フォームを非表示
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

// 返信を投稿
async function submitReply(parentCommentId) {
    const replyText = document.getElementById(`replyText-${parentCommentId}`).value.trim();
    
    if (!replyText) {
        alert('返信内容を入力してください');
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
                article_id: currentArticle.id,
                parent_comment_id: parentCommentId,
                comment: replyText
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 返信フォームを非表示・クリア
            hideReplyForm(parentCommentId);
            
            // コメント一覧を再読み込み
            await loadArticleComments(currentArticle.id);
            renderComments();
            
            alert('返信を投稿しました');
        } else {
            alert('返信の投稿に失敗しました: ' + data.error);
        }
        
    } catch (error) {
        console.error('返信投稿エラー:', error);
        alert('返信の投稿中にエラーが発生しました');
    }
}

// コメント編集フォームを表示
function showCommentEditForm(commentId) {
    const commentText = document.getElementById(`commentText-${commentId}`);
    const editForm = document.getElementById(`editForm-${commentId}`);
    
    if (commentText && editForm) {
        commentText.style.display = 'none';
        editForm.style.display = 'block';
        
        // テキストエリアにフォーカス
        const textarea = document.getElementById(`editText-${commentId}`);
        if (textarea) {
            textarea.focus();
        }
    }
}

// コメント編集をキャンセル
function cancelCommentEdit(commentId) {
    const commentText = document.getElementById(`commentText-${commentId}`);
    const editForm = document.getElementById(`editForm-${commentId}`);
    
    if (commentText && editForm) {
        commentText.style.display = 'block';
        editForm.style.display = 'none';
    }
}

// コメント編集を保存
async function submitCommentEdit(commentId) {
    const newText = document.getElementById(`editText-${commentId}`).value.trim();
    
    if (!newText) {
        alert('コメント内容を入力してください');
        return;
    }
    
    try {
        const response = await fetch(`/api/article-comments?id=${commentId}`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                comment: newText
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // コメント一覧を再読み込み
            await loadArticleComments(currentArticle.id);
            renderComments();
            
            alert('コメントを更新しました');
        } else {
            alert('コメントの更新に失敗しました: ' + data.error);
        }
        
    } catch (error) {
        console.error('コメント更新エラー:', error);
        alert('コメントの更新中にエラーが発生しました');
    }
}

// HTMLエスケープ関数
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}