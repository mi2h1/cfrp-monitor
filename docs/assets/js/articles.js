// CFRP Monitor - 記事管理ページJavaScript

let articles = [];
let sources = [];
let currentPage = 1;
let authToken = null;
let userFeatures = null;

// キャッシング戦略
let sourcesCache = null;
let sourcesCacheTime = null;
let articlesCache = new Map(); // フィルター条件別のキャッシュ
let articlesCacheTime = new Map();
const CACHE_DURATION = 5 * 60 * 1000; // 5分間
const ARTICLES_CACHE_DURATION = 2 * 60 * 1000; // 記事は2分間（より頻繁に更新される可能性があるため）

// デバウンス用変数
let filterDebounceTimer = null;
const DEBOUNCE_DELAY = 300; // 300ms

// デバウンス関数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// articles.jsの初期化関数（page-init.jsから呼び出される）
async function initializeArticlesApp() {
    // 認証チェックはメインページのスクリプトで実行済み
    authToken = localStorage.getItem('auth_token');
    
    // userFeaturesを再取得して確実に設定
    userFeatures = window.userFeatures;
    
    // URLパラメータから初期状態を復元
    restoreStateFromURL();
    
    // 初期ローディング: テーブル形式スケルトン表示
    showLoadingState();
    document.getElementById('articlesContainer').style.display = 'block';
    
    // 並列処理で初期化を高速化
    const [sourcesResult, articlesResult] = await Promise.allSettled([
        loadSources(),
        loadArticles()
    ]);
    
    // エラーハンドリング
    if (sourcesResult.status === 'rejected') {
        console.error('ソース読み込みエラー:', sourcesResult.reason);
    }
    
    if (articlesResult.status === 'rejected') {
        console.error('記事読み込みエラー:', articlesResult.reason);
        document.getElementById('articlesContainer').innerHTML = 
            '<div class="alert alert-danger">記事の読み込みに失敗しました</div>';
        return;
    }
    
    setupEventListeners();
}

// URLパラメータから状態を復元
function restoreStateFromURL() {
    const params = new URLSearchParams(window.location.search);
    
    // ページ番号
    const page = params.get('page');
    if (page) {
        currentPage = parseInt(page) || 1;
    }
    
    // フィルター状態を復元
    if (params.get('status')) {
        const statusFilter = document.getElementById('statusFilter');
        if (statusFilter) statusFilter.value = params.get('status');
    }
    
    if (params.get('flagged')) {
        const flaggedFilter = document.getElementById('flaggedFilter');
        if (flaggedFilter) flaggedFilter.value = params.get('flagged');
    }
    
    if (params.get('source')) {
        const sourceFilter = document.getElementById('sourceFilter');
        if (sourceFilter) sourceFilter.value = params.get('source');
    }
    
    if (params.get('comments')) {
        const commentFilter = document.getElementById('commentFilter');
        if (commentFilter) commentFilter.value = params.get('comments');
    }
    
    if (params.get('order')) {
        const sortOrder = document.getElementById('sortOrder');
        if (sortOrder) sortOrder.value = params.get('order');
    }
    
    if (params.get('limit')) {
        const itemsPerPage = document.getElementById('itemsPerPage');
        if (itemsPerPage) itemsPerPage.value = params.get('limit');
    }
}

// 現在の状態をURLに反映
function updateURLWithCurrentState() {
    const params = new URLSearchParams();
    
    // 現在のフィルター状態を取得
    const statusFilter = document.getElementById('statusFilter')?.value;
    const flaggedFilter = document.getElementById('flaggedFilter')?.value;
    const sourceFilter = document.getElementById('sourceFilter')?.value;
    const commentFilter = document.getElementById('commentFilter')?.value;
    const sortOrder = document.getElementById('sortOrder')?.value;
    const itemsPerPage = document.getElementById('itemsPerPage')?.value;
    
    // パラメータを設定
    if (currentPage > 1) params.set('page', currentPage);
    if (statusFilter) params.set('status', statusFilter);
    if (flaggedFilter) params.set('flagged', flaggedFilter);
    if (sourceFilter) params.set('source', sourceFilter);
    if (commentFilter) params.set('comments', commentFilter);
    if (sortOrder && sortOrder !== 'desc') params.set('order', sortOrder);
    if (itemsPerPage && itemsPerPage !== '20') params.set('limit', itemsPerPage);
    
    // URLを更新（ページリロードなし）
    const newURL = params.toString() ? `?${params.toString()}` : window.location.pathname;
    window.history.replaceState({}, '', newURL);
}

// ソース一覧を読み込み（キャッシング対応）
async function loadSources() {
    try {
        // キャッシュチェック
        if (sourcesCache && sourcesCacheTime && 
            (Date.now() - sourcesCacheTime) < CACHE_DURATION) {
            console.log('ソースデータをキャッシュから取得');
            sources = sourcesCache;
            populateSourceFilter();
            return;
        }
        
        const response = await fetch('/api/sources?used_only=true', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            // キャッシュに保存
            sourcesCache = data.sources || [];
            sourcesCacheTime = Date.now();
            sources = sourcesCache;
            populateSourceFilter();
            console.log('ソースデータを新規取得してキャッシュに保存');
        } else {
            console.error('ソース読み込みエラー:', data.error);
        }
    } catch (error) {
        console.error('ソース読み込みエラー:', error);
    }
}

// 記事の総件数を取得（API経由）
async function getTotalArticlesCount(statusFilter = '', flaggedFilter = '', sourceFilter = '', commentFilter = '') {
    try {
        let url = '/api/articles?count_only=true';
        
        // フィルタリング条件を適用
        if (statusFilter) url += `&status=${encodeURIComponent(statusFilter)}`;
        if (flaggedFilter) url += `&flagged=${encodeURIComponent(flaggedFilter)}`;
        if (sourceFilter) url += `&source_id=${encodeURIComponent(sourceFilter)}`;
        if (commentFilter) url += `&has_comments=${encodeURIComponent(commentFilter)}`;
        
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
        // パフォーマンス最適化: 総件数とページデータを並列取得
        const [totalCountResult, pageDataResult] = await Promise.allSettled([
            getTotalArticlesCount(),
            loadArticlesPageData(1) // 新しい関数で記事データのみ取得
        ]);
        
        if (totalCountResult.status === 'fulfilled' && pageDataResult.status === 'fulfilled') {
            const totalCount = totalCountResult.value;
            const { articles: pageArticles, page } = pageDataResult.value;
            
            // データを設定
            articles = pageArticles;
            currentPage = page;
            
            // URL更新
            updateURLWithCurrentState();
            
            // UI更新
            renderArticles();
            renderPagination(totalCount, parseInt(document.getElementById('itemsPerPage').value), page);
            
            // ページネーションの表示
            const paginationElement = document.getElementById('pagination');
            if (paginationElement) {
                paginationElement.style.display = 'block';
            }
        } else {
            // エラーハンドリング - フォールバック処理
            const totalCount = await getTotalArticlesCount();
            await loadArticlesPage(1, totalCount);
        }
        
        // ローディング状態を解除してコンテンツを表示（スケルトンはrenderArticles()で自動置換）
        document.getElementById('loading').style.display = 'none';
        document.getElementById('articlesContainer').style.display = 'block';
    } catch (error) {
        console.error('記事読み込みエラー:', error);
        document.getElementById('articlesContainer').innerHTML = '<div class="alert alert-danger">記事の読み込みに失敗しました</div>';
    }
}

// パフォーマンス最適化: 記事データのみを取得（UI更新なし）
async function loadArticlesPageData(page) {
    const itemsPerPage = parseInt(document.getElementById('itemsPerPage').value);
    
    // フィルタリング条件を取得
    const statusFilter = document.getElementById('statusFilter').value;
    const flaggedFilter = document.getElementById('flaggedFilter').value;
    const sourceFilter = document.getElementById('sourceFilter').value;
    const commentFilter = document.getElementById('commentFilter').value;
    const sortOrder = document.getElementById('sortOrder').value;
    
    // キャッシング戦略: キャッシュキーを生成
    const filters = { statusFilter, flaggedFilter, sourceFilter, commentFilter, sortOrder, itemsPerPage };
    const cacheKey = generateCacheKey(page, filters);
    
    // キャッシュから取得を試行
    const cachedData = getArticlesFromCache(cacheKey);
    if (cachedData) {
        return cachedData;
    }
    
    // キャッシュにない場合はAPIから取得
    const offset = (page - 1) * itemsPerPage;
    let url = `/api/articles?limit=${itemsPerPage}&offset=${offset}&sort=${sortOrder}`;
    
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
    if (commentFilter) {
        url += `&has_comments=${encodeURIComponent(commentFilter)}`;
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
    
    const result = {
        articles: data.articles || [],
        page: page
    };
    
    // キャッシュに保存
    setArticlesCache(cacheKey, result);
    
    return result;
}

// 指定されたページの記事を取得
async function loadArticlesPage(page, totalCount = null) {
    try {
        // ローディング状態を表示
        showLoadingState();
        
        const itemsPerPage = parseInt(document.getElementById('itemsPerPage').value);
        
        // フィルタリング条件を取得
        const statusFilter = document.getElementById('statusFilter').value;
        const flaggedFilter = document.getElementById('flaggedFilter').value;
        const sourceFilter = document.getElementById('sourceFilter').value;
        const commentFilter = document.getElementById('commentFilter').value;
        const sortOrder = document.getElementById('sortOrder').value;
        
        // キャッシング戦略: キャッシュからの取得を試行
        const filters = { statusFilter, flaggedFilter, sourceFilter, commentFilter, sortOrder, itemsPerPage };
        const cacheKey = generateCacheKey(page, filters);
        const cachedData = getArticlesFromCache(cacheKey);
        
        if (cachedData) {
            articles = cachedData.articles;
            currentPage = cachedData.page;
            
            // URL更新
            updateURLWithCurrentState();
            
            // ローディング状態を非表示して記事一覧を表示
            hideLoadingState();
            document.getElementById('loading').style.display = 'none'; // 明示的にローディング要素を非表示
            document.getElementById('articlesContainer').style.display = 'block';
            
            renderArticles();
            renderPagination(totalCount || articles.length, itemsPerPage, page);
            
            // ページネーションの表示とボタン有効化
            const paginationElement = document.getElementById('pagination');
            if (paginationElement) {
                paginationElement.style.display = 'block';
            }
            enablePaginationButtons();
            return;
        }
        
        const offset = (page - 1) * itemsPerPage;
        
        // 総件数が未取得の場合は取得（フィルタリング条件付き）
        if (totalCount === null) {
            totalCount = await getTotalArticlesCount(statusFilter, flaggedFilter, sourceFilter, commentFilter);
        }
        
        // コメントフィルターがある場合、全データから総件数を再取得
        if (commentFilter) {
            totalCount = await getTotalArticlesCount(statusFilter, flaggedFilter, sourceFilter, commentFilter);
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
        if (commentFilter) {
            url += `&has_comments=${encodeURIComponent(commentFilter)}`;
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
        
        // キャッシュに保存
        const cacheData = { articles: articles, page: page };
        setArticlesCache(cacheKey, cacheData);
        
        // URL更新
        updateURLWithCurrentState();
        
        // ローディング状態を非表示して記事一覧を表示
        hideLoadingState();
        document.getElementById('loading').style.display = 'none'; // 明示的にローディング要素を非表示
        document.getElementById('articlesContainer').style.display = 'block';
        
        renderArticles();
        renderPagination(totalCount, itemsPerPage, page);
        
        // ページネーションの表示とボタン有効化
        const paginationElement = document.getElementById('pagination');
        if (paginationElement) {
            paginationElement.style.display = 'block';
        }
        enablePaginationButtons();
        
    } catch (error) {
        console.error('記事ページ読み込みエラー:', error);
        hideLoadingState();
        document.getElementById('loading').style.display = 'none'; // 明示的にローディング要素を非表示
        const articlesContainer = document.getElementById('articlesContainer');
        if (articlesContainer) {
            articlesContainer.style.display = 'block';
            articlesContainer.innerHTML = '<div class="alert alert-danger">記事の読み込みに失敗しました: ' + error.message + '</div>';
        }
        enablePaginationButtons();
    }
}

// ローディング状態管理関数（テーブル形式スケルトンローダー）
function showLoadingState() {
    const container = document.getElementById('articlesContainer');
    const skeletonCount = parseInt(document.getElementById('itemsPerPage').value) || 20;
    
    // 実際のテーブル構造と同じ形式でスケルトンを作成
    const skeletonHTML = `
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th style="width: 90px;">ステータス</th>
                        <th>タイトル</th>
                        <th style="width: 140px;">情報源</th>
                        <th style="width: 120px;">公開日</th>
                        <th style="width: 80px;" title="AI要約の有無">AI要約</th>
                        <th style="width: 80px;">コメント</th>
                    </tr>
                </thead>
                <tbody>
                    ${Array.from({length: skeletonCount}, (_, i) => `
                        <tr>
                            <td>
                                <div class="skeleton-badge" style="width: 70px; height: 20px;"></div>
                            </td>
                            <td>
                                <div class="skeleton-text" style="width: ${60 + Math.random() * 30}%; height: 18px; margin-bottom: 4px;"></div>
                                <div class="skeleton-text" style="width: ${40 + Math.random() * 20}%; height: 14px;"></div>
                            </td>
                            <td>
                                <div class="skeleton-text" style="width: 80%; height: 16px;"></div>
                            </td>
                            <td>
                                <div class="skeleton-text" style="width: 90%; height: 16px;"></div>
                            </td>
                            <td class="text-center">
                                <div class="skeleton-badge" style="width: 20px; height: 20px; border-radius: 50%; margin: 0 auto;"></div>
                            </td>
                            <td class="text-center">
                                <div class="skeleton-badge" style="width: 30px; height: 18px; border-radius: 12px; margin: 0 auto;"></div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = skeletonHTML;
}

function hideLoadingState() {
    // 特に何もしない（renderArticles()で内容が置き換わるため）
}

// 記事詳細用スケルトンローダーを作成
function createArticleDetailSkeleton() {
    return `
        <div class="row">
            <div class="col-12">
                <div class="card mb-4">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <!-- タイトル部分のスケルトン -->
                        <div style="flex: 1;">
                            <div class="skeleton-badge mb-2" style="width: 60px; height: 24px;"></div>
                            <div class="skeleton-text" style="width: 70%; height: 24px;"></div>
                        </div>
                        <div class="skeleton-badge" style="width: 120px; height: 32px;"></div>
                    </div>
                    <div class="card-body">
                        <div class="row mb-3">
                            <!-- 左側: 記事情報のスケルトン -->
                            <div class="col-md-3">
                                <!-- 公開日時 -->
                                <div class="mb-3">
                                    <div class="skeleton-text" style="width: 90%; height: 16px;"></div>
                                </div>
                                
                                <!-- 情報源 -->
                                <div class="mb-3">
                                    <div class="skeleton-text" style="width: 80%; height: 16px;"></div>
                                </div>
                                
                                <!-- URL -->
                                <div class="mb-3">
                                    <div class="skeleton-text" style="width: 100%; height: 16px;"></div>
                                </div>
                                
                                <!-- ステータス -->
                                <div class="mb-3">
                                    <div class="skeleton-text" style="width: 50%; height: 14px; margin-bottom: 4px;"></div>
                                    <div class="skeleton-badge" style="width: 100%; height: 32px;"></div>
                                </div>
                                
                                <!-- 重要記事フラグ -->
                                <div class="mb-3">
                                    <div class="skeleton-text" style="width: 70%; height: 16px;"></div>
                                </div>
                            </div>
                            
                            <!-- 右側: AI要約エリアのスケルトン -->
                            <div class="col-md-9">
                                <div class="ai-summary-section">
                                    <div class="d-flex justify-content-between align-items-center mb-3">
                                        <div class="skeleton-text" style="width: 120px; height: 24px;"></div>
                                        <div class="skeleton-badge" style="width: 100px; height: 32px;"></div>
                                    </div>
                                    <div class="alert alert-light">
                                        <div class="skeleton-text" style="width: 100%; height: 16px; margin-bottom: 8px;"></div>
                                        <div class="skeleton-text" style="width: 95%; height: 16px; margin-bottom: 8px;"></div>
                                        <div class="skeleton-text" style="width: 88%; height: 16px; margin-bottom: 8px;"></div>
                                        <div class="skeleton-text" style="width: 92%; height: 16px; margin-bottom: 8px;"></div>
                                        <div class="skeleton-text" style="width: 85%; height: 16px; margin-bottom: 16px;"></div>
                                        <div class="skeleton-text" style="width: 60%; height: 14px;"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- 備考欄のスケルトン -->
                        <div class="article-comments mb-3">
                            <div class="skeleton-text" style="width: 60px; height: 20px; margin-bottom: 8px;"></div>
                            <div class="skeleton-badge" style="width: 100%; height: 80px;"></div>
                        </div>
                        
                        <div class="d-flex justify-content-between align-items-center">
                            <div class="skeleton-text" style="width: 200px; height: 14px;"></div>
                            <div class="skeleton-badge" style="width: 80px; height: 32px;"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- コメント部分のスケルトン -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <div class="skeleton-text" style="width: 100px; height: 20px;"></div>
                    </div>
                    <div class="card-body">
                        <!-- コメント投稿フォームのスケルトン -->
                        <div class="mb-4">
                            <div class="skeleton-badge" style="width: 100%; height: 80px; margin-bottom: 8px;"></div>
                            <div class="skeleton-badge" style="width: 100px; height: 32px;"></div>
                        </div>
                        
                        <!-- 既存コメントのスケルトン -->
                        ${Array.from({length: 3}, (_, i) => `
                            <div class="comment-card mb-3">
                                <div class="card">
                                    <div class="card-body">
                                        <div class="d-flex align-items-center mb-2">
                                            <div class="skeleton-text" style="width: 80px; height: 16px; margin-right: 16px;"></div>
                                            <div class="skeleton-text" style="width: 120px; height: 14px;"></div>
                                        </div>
                                        <div class="skeleton-text" style="width: 100%; height: 16px; margin-bottom: 6px;"></div>
                                        <div class="skeleton-text" style="width: ${70 + Math.random() * 25}%; height: 16px;"></div>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;
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

// 記事を表示（サーバーサイドページネーション使用）
function renderArticles() {
    const container = document.getElementById('articlesContainer');
    
    if (articles.length === 0) {
        container.innerHTML = '<div class="alert alert-info">該当する記事がありません</div>';
        document.getElementById('pagination').style.display = 'none';
        document.getElementById('paginationTop').style.display = 'none';
        return;
    }

    // サーバーサイドで既にページネーション・フィルタリング済みの記事を使用
    const paginatedArticles = articles;

    // DocumentFragmentを使用した効率的なDOM操作
    const fragment = document.createDocumentFragment();
    const tableContainer = document.createElement('div');
    tableContainer.className = 'table-responsive';
    
    const table = document.createElement('table');
    table.className = 'table table-hover';
    
    // ヘッダー作成
    const thead = document.createElement('thead');
    thead.innerHTML = `
        <tr>
            <th style="width: 90px;">ステータス</th>
            <th>タイトル</th>
            <th style="width: 140px;">情報源</th>
            <th style="width: 120px;">公開日</th>
            <th style="width: 80px;" title="AI要約の有無">AI要約</th>
            <th style="width: 80px;">コメント</th>
        </tr>
    `;
    
    // ボディ作成
    const tbody = document.createElement('tbody');
    paginatedArticles.forEach(article => {
        const row = createArticleTableRowElement(article);
        tbody.appendChild(row);
    });
    
    table.appendChild(thead);
    table.appendChild(tbody);
    tableContainer.appendChild(table);
    
    // 一度のDOM操作で更新
    container.innerHTML = '';
    container.appendChild(tableContainer);
    
    // ページネーション表示は loadArticlesPage で行うため削除
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
                        <th style="width: 140px;">情報源</th>
                        <th style="width: 120px;">公開日</th>
                        <th style="width: 80px;" title="AI要約の有無">AI要約</th>
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

// 削除: 不要なクライアントサイドフィルタリング（サーバーサイドで処理済み）
// filterAndSortArticles関数を削除 - パフォーマンス最適化のため

// DOM要素を直接作成する高速化関数
function createArticleTableRowElement(article) {
    const row = document.createElement('tr');
    row.className = article.flagged ? 'table-warning' : '';
    row.dataset.id = article.id;
    row.style.cursor = 'pointer';
    
    // ステータスセル
    const statusCell = document.createElement('td');
    const statusBadge = document.createElement('span');
    statusBadge.className = `badge bg-${getStatusColor(article.status)} status-badge`;
    statusBadge.textContent = getStatusLabel(article.status);
    statusCell.appendChild(statusBadge);
    
    // 重要フラグをステータスセルに追加
    if (article.flagged) {
        const importantBadge = document.createElement('span');
        importantBadge.className = 'badge border border-danger text-danger bg-transparent mt-1';
        importantBadge.textContent = '重要';
        statusCell.appendChild(importantBadge);
    }
    
    // タイトルセル
    const titleCell = document.createElement('td');
    
    const titleDiv = document.createElement('div');
    titleDiv.className = 'fw-medium';
    titleDiv.textContent = article.title || 'タイトルなし';
    titleCell.appendChild(titleDiv);
    
    const urlDiv = document.createElement('div');
    urlDiv.className = 'small text-muted text-truncate';
    urlDiv.style.maxWidth = '350px';
    urlDiv.title = article.url;
    urlDiv.textContent = article.url;
    titleCell.appendChild(urlDiv);
    
    // コメント表示
    if (article.comments) {
        const commentDiv = document.createElement('div');
        commentDiv.className = 'small text-muted mt-1';
        const icon = document.createElement('i');
        icon.className = 'fas fa-sticky-note';
        commentDiv.appendChild(icon);
        const text = article.comments.length > 100 ? 
            article.comments.substring(0, 100) + '...' : 
            article.comments;
        commentDiv.appendChild(document.createTextNode(' ' + text));
        titleCell.appendChild(commentDiv);
    }
    
    // 情報源セル
    const sourceCell = document.createElement('td');
    sourceCell.className = 'text-nowrap';
    const sourceSmall = document.createElement('small');
    sourceSmall.className = 'text-muted';
    const sourceIcon = document.createElement('i');
    sourceIcon.className = 'fas fa-rss';
    sourceSmall.appendChild(sourceIcon);
    const sourceName = article.sources?.name || article.sources?.domain || 'Unknown';
    sourceSmall.appendChild(document.createTextNode(' ' + sourceName));
    sourceCell.appendChild(sourceSmall);
    
    // 日付セル
    const dateCell = document.createElement('td');
    dateCell.className = 'text-nowrap';
    const dateSmall = document.createElement('small');
    dateSmall.className = 'text-muted';
    const dateIcon = document.createElement('i');
    dateIcon.className = 'fas fa-calendar-alt';
    dateSmall.appendChild(dateIcon);
    const pubDate = article.published_at ? formatJSTDate(article.published_at) : '不明';
    dateSmall.appendChild(document.createTextNode(' ' + pubDate));
    dateCell.appendChild(dateSmall);
    
    // AI要約セル
    const summaryCell = document.createElement('td');
    summaryCell.className = 'text-center';
    if (article.ai_summary && article.ai_summary.trim()) {
        // AI要約済みの場合
        const summaryIcon = document.createElement('i');
        summaryIcon.className = 'fas fa-robot text-info';
        summaryIcon.title = 'AI要約済み';
        summaryCell.appendChild(summaryIcon);
    } else {
        // AI要約未作成の場合
        const noSummarySpan = document.createElement('span');
        noSummarySpan.className = 'text-muted';
        noSummarySpan.textContent = '-';
        summaryCell.appendChild(noSummarySpan);
    }
    
    // コメント数セル
    const commentCell = document.createElement('td');
    commentCell.className = 'text-center';
    const commentBadge = document.createElement('span');
    const commentCount = article.comment_count || 0;
    // コメント数に応じて色を変更
    commentBadge.className = commentCount > 0 ? 'badge bg-primary' : 'badge bg-secondary';
    const commentIcon = document.createElement('i');
    commentIcon.className = 'fas fa-comment';
    commentBadge.appendChild(commentIcon);
    commentBadge.appendChild(document.createTextNode(' ' + commentCount));
    commentCell.appendChild(commentBadge);
    
    // セルを行に追加
    row.appendChild(statusCell);
    row.appendChild(titleCell);
    row.appendChild(sourceCell);
    row.appendChild(dateCell);
    row.appendChild(summaryCell);
    row.appendChild(commentCell);
    
    return row;
}

// 記事テーブル行を作成（文字列版・後方互換性のため残す）
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
                ${article.flagged ? '<span class="badge border border-danger text-danger bg-transparent mt-1">重要</span>' : ''}
            </td>
            <td>
                <div class="fw-medium">${escapeHtml(article.title || 'タイトルなし')}</div>
                <div class="small text-muted text-truncate" style="max-width: 350px;" title="${escapeHtml(article.url)}">${escapeHtml(article.url)}</div>
                ${article.comments ? `<div class="small text-muted mt-1"><i class="fas fa-sticky-note"></i> ${escapeHtml(article.comments.substring(0, 100))}${article.comments.length > 100 ? '...' : ''}</div>` : ''}
            </td>
            <td class="text-nowrap">
                <small class="text-muted">
                    <i class="fas fa-rss"></i> ${sourceName}
                </small>
            </td>
            <td class="text-nowrap">
                <small class="text-muted">
                    <i class="fas fa-calendar-alt"></i> ${pubDate}
                </small>
            </td>
            <td class="text-center">
                ${article.ai_summary && article.ai_summary.trim() ? 
                    '<i class="fas fa-robot text-info" title="AI要約済み"></i>' : 
                    '<span class="text-muted">-</span>'
                }
            </td>
            <td class="text-center">
                <span class="badge ${(article.comment_count || 0) > 0 ? 'bg-primary' : 'bg-secondary'}">
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
    // デバウンス処理付きフィルター処理
    const debouncedFilterHandler = debounce(() => {
        currentPage = 1; // フィルター変更時はページをリセット
        updateURLWithCurrentState(); // URL更新
        loadArticlesPage(1);
    }, DEBOUNCE_DELAY);
    
    // フィルター・ソート・表示件数変更時（デバウンス版）
    const filterIds = ['statusFilter', 'flaggedFilter', 'sourceFilter', 'commentFilter', 'sortOrder', 'itemsPerPage'];
    filterIds.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('change', debouncedFilterHandler);
        }
    });
    
    // 記事行クリックイベント（編集可能詳細画面を表示）
    document.getElementById('articlesContainer').addEventListener('click', (e) => {
        const row = e.target.closest('tr[data-id]');
        if (row) {
            const articleId = row.dataset.id;
            console.log('記事編集画面を表示:', articleId);
            // 編集可能な詳細画面を表示
            showEditableArticleDetail(articleId);
        }
    });

    // 更新ボタン（キャッシュクリア機能付き）
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
            refreshBtn.disabled = true;
            // キャッシュをクリアして強制更新
            clearArticlesCache();
            sourcesCache = null;
            sourcesCacheTime = null;
            await loadArticles();
            refreshBtn.disabled = false;
        });
    }
    
    // ページネーションクリック（下部）
    document.getElementById('paginationList').addEventListener('click', (e) => {
        e.preventDefault();
        const pageLink = e.target.closest('.page-link');
        if (pageLink && !pageLink.parentElement.classList.contains('disabled')) {
            const page = parseInt(pageLink.dataset.page);
            if (!isNaN(page)) {
                handlePaginationClick(page);
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
                handlePaginationClick(page);
            }
        }
    });

    // 削除: 重複したイベントリスナー（上で統合済み）

    // 削除: 旧編集モードのイベントリスナー（統合モードに変更）

    // ページネーションクリック
    setupPagination('#articlesContainer', renderArticles);
}

// 削除: 旧saveArticle関数（saveArticleDetailに統合済み）

// 編集モードを開く（統合モード対応）
function openEditMode(articleId) {
    // 統合モードに変更されたため、showEditableArticleDetailを使用
    showEditableArticleDetail(articleId);
}

// 編集モードを閉じる（統合モード対応）
function closeEditMode() {
    // 統合モードに合わせてhideArticleDetailを使用
    hideArticleDetail();
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
    
    // デバッグ: コメントデータを確認（簡略化）
    // console.log('Debug - renderComments:', {
    //     comments: comments,
    //     userFeatures: userFeatures
    // });
    
    if (comments.length === 0) {
        container.innerHTML = '<div class="text-muted text-center">まだコメントがありません</div>';
        return;
    }
    
    // コメントを階層構造に変換
    const commentTree = buildCommentTree(comments);
    
    // HTML生成
    const commentsHtml = commentTree.map((comment, index, array) => {
        const isLastRoot = index === array.length - 1;
        return renderCommentCard(comment, 0, isLastRoot);
    }).join('');
    container.innerHTML = commentsHtml;
}

// コメントの階層構造を構築（削除されたコメントも考慮）
function buildCommentTree(comments) {
    const rootComments = [];
    const commentsByRoot = {};
    const orphanedReplies = [];
    
    // まず、全てのコメントからルートコメントを識別
    comments.forEach(comment => {
        if (!comment.parent_comment_id) {
            // ルートコメント（削除されたものも含む）
            commentsByRoot[comment.id] = {
                root: { ...comment },
                replies: []
            };
        }
    });
    
    // 返信コメントを処理
    comments.forEach(comment => {
        if (comment.parent_comment_id) {
            // 直接の親がルートコメントかどうかチェック
            if (commentsByRoot[comment.parent_comment_id]) {
                // 直接の親がルートコメントの場合
                commentsByRoot[comment.parent_comment_id].replies.push({ ...comment });
            } else {
                // 親が返信コメントの場合、そのルートコメントを探す
                const rootId = findRootCommentId(comment, comments);
                if (rootId && commentsByRoot[rootId]) {
                    commentsByRoot[rootId].replies.push({ ...comment });
                } else {
                    // 孤立した返信（親が完全に削除されている場合）
                    orphanedReplies.push(comment);
                }
            }
        }
    });
    
    // 孤立した返信のために削除された親コメントを作成
    orphanedReplies.forEach(orphan => {
        const virtualParentId = orphan.parent_comment_id;
        if (!commentsByRoot[virtualParentId]) {
            // 削除された親コメントの仮想エントリを作成
            commentsByRoot[virtualParentId] = {
                root: {
                    id: virtualParentId,
                    is_deleted: true,
                    created_at: orphan.created_at, // 子コメントの日時を使用
                    virtual_parent: true // 仮想親フラグ
                },
                replies: []
            };
        }
        commentsByRoot[virtualParentId].replies.push({ ...orphan });
    });
    
    // ルートコメントを「そのツリー内の最新コメント日時」でソート
    const sortedRootIds = Object.keys(commentsByRoot).sort((a, b) => {
        const latestDateA = getLatestDateInTree(commentsByRoot[a]);
        const latestDateB = getLatestDateInTree(commentsByRoot[b]);
        return latestDateB - latestDateA; // 新しい順
    });
    
    // 結果を構築（削除された親でも子がいる場合は表示）
    sortedRootIds.forEach(rootId => {
        const group = commentsByRoot[rootId];
        
        // 削除されたコメントでも子コメントがある場合は表示
        if (!group.root.is_deleted || group.replies.length > 0) {
            // 返信を時間順でソート
            group.replies.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
            
            rootComments.push({
                ...group.root,
                replies: group.replies
            });
        }
    });
    
    return rootComments;
}

// コメントツリー内の最新日時を取得する関数
function getLatestDateInTree(commentGroup) {
    // 親コメントの日時
    const rootDate = new Date(commentGroup.root.created_at);
    let latestDate = rootDate;
    
    // 全ての返信の中から最新日時を探す
    function findLatestInReplies(replies) {
        replies.forEach(reply => {
            const replyDate = new Date(reply.created_at);
            if (replyDate > latestDate) {
                latestDate = replyDate;
            }
            
            // 返信の返信も再帰的にチェック
            if (reply.replies && reply.replies.length > 0) {
                findLatestInReplies(reply.replies);
            }
        });
    }
    
    if (commentGroup.replies && commentGroup.replies.length > 0) {
        findLatestInReplies(commentGroup.replies);
    }
    
    return latestDate;
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
function renderCommentCard(comment, level = 0, isLast = false, parentHasMoreSiblings = false) {
    const marginLeft = level * 20;
    const isDeleted = comment.is_deleted;
    const isVirtualParent = comment.virtual_parent;
    const isRootComment = level === 0;
    
    // 削除されたコメントか仮想親コメントの場合の表示
    let commentText, displayName, displayDate;
    if (isDeleted || isVirtualParent) {
        commentText = '<em class="text-muted">このコメントは削除されました</em>';
        displayName = '<em class="text-muted">削除済みコメント</em>';
        displayDate = comment.created_at ? formatJSTDisplay(comment.created_at) : '';
    } else {
        commentText = escapeHtml(comment.comment).replace(/\n/g, '<br>');
        displayName = escapeHtml(comment.users?.display_name || comment.user_id);
        displayDate = formatJSTDisplay(comment.created_at);
    }
    
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
            const tokenPayload = JSON.parse(atob(authToken.split('.')[1]));
            currentUser = tokenPayload.user_id || tokenPayload.sub || tokenPayload.username;
        } catch (e) {
            console.warn('JWTトークンのパースに失敗:', e);
        }
    }
    
    const isOwnComment = currentUser && currentUser === comment.user_id;
    
    let html = `
        <div class="comment-card mb-3" style="margin-left: ${marginLeft}px;" data-comment-id="${comment.id}">
            <div class="card card-body py-2 px-3 position-relative">
                <!-- 削除ボタンを右上に配置 -->
                ${isOwnComment && !isDeleted && !isVirtualParent ? `
                    <div class="position-absolute top-0 end-0" style="padding: 8px 12px;">
                        <a href="#" class="text-danger small text-decoration-none" onclick="deleteComment('${comment.id}'); return false;" style="font-size: 0.7rem;" title="コメントを削除">コメントを削除</a>
                    </div>
                ` : ''}
                
                <div class="comment-content">
                    <div class="comment-meta mb-1 d-flex align-items-center">
                        <strong class="me-2">${displayName}</strong>
                        <small class="text-muted me-1">${displayDate}</small>
                        ${!isDeleted && !isVirtualParent && isEdited ? '<small class="text-info me-2">(編集済み)</small>' : ''}
                        ${isOwnComment && !isDeleted && !isVirtualParent ? `
                            <button class="btn btn-link btn-sm p-1 ms-1 edit-meta-btn" onclick="showCommentEditForm('${comment.id}')" style="font-size: 0.75rem; line-height: 1; color: #6c757d;" title="コメントを編集">
                                <i class="fas fa-edit me-1"></i>編集
                            </button>
                        ` : ''}
                    </div>
                    <div class="comment-text" id="commentText-${comment.id}">${commentText}</div>
                    
                    <!-- 編集フォーム（初期非表示） -->
                    ${!isDeleted && !isVirtualParent ? `
                        <div class="edit-form mt-2" id="editForm-${comment.id}" style="display: none;">
                            <textarea class="form-control mb-2" id="editText-${comment.id}" rows="3">${escapeHtml(comment.comment || '')}</textarea>
                            <div class="d-flex gap-2">
                                <button class="btn btn-success btn-sm" onclick="submitCommentEdit('${comment.id}')">
                                    <i class="fas fa-save"></i> 保存
                                </button>
                                <button class="btn btn-outline-secondary btn-sm" onclick="cancelCommentEdit('${comment.id}')">
                                    キャンセル
                                </button>
                            </div>
                        </div>
                    ` : ''}
                    
                    <!-- 返信ボタンを右下に配置（子コメントがない場合のみ） -->
                    ${!isDeleted && !isVirtualParent && level === 0 && (!comment.replies || comment.replies.length === 0) ? `
                        <div class="d-flex justify-content-end mt-2">
                            <button class="btn btn-outline-primary btn-sm reply-btn" onclick="showReplyForm('${comment.id}')">
                                <i class="fas fa-reply"></i> 返信
                            </button>
                        </div>
                    ` : ''}
                </div>
            </div>
            
            <!-- 返信フォーム -->
            ${!isDeleted && !isVirtualParent ? `
                <div class="reply-form mt-2" id="replyForm-${comment.id}" style="display: none; margin-left: ${marginLeft + 20}px;">
                    <div class="card card-body py-2 px-3 bg-light">
                        <div class="mb-2">
                            <small class="text-muted">
                                <i class="fas fa-reply"></i> <strong>${displayName}</strong> への返信
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
            ` : ''}
        </div>
    `;
    
    // 返信があれば引用スタイルのコンテナで囲む
    if (comment.replies && comment.replies.length > 0) {
        const repliesHtml = comment.replies.map((reply, index, array) => {
            const isLastReply = index === array.length - 1;
            return renderCommentCard(reply, 1, isLastReply);
        }).join('');
        
        // 返信群の最後に1つの返信ボタンを追加（削除されたコメントには表示しない）
        const groupReplyButton = !isDeleted && !isVirtualParent ? `
            <div class="group-reply-container mt-2 mb-4" style="margin-left: 15px; padding-top: 8px;">
                <button class="btn btn-outline-primary btn-sm reply-btn" onclick="showReplyForm('${comment.id}')">
                    <i class="fas fa-reply"></i> 返信
                </button>
            </div>
        ` : '<div class="mb-4"></div>'; // 削除されたコメントの場合はスペースのみ
        
        html += `
            <div class="replies-container">
                ${repliesHtml}
                ${groupReplyButton}
            </div>
        `;
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
            
            // パフォーマンス最適化: コメントのみ再読み込み（記事データは既に読み込み済み）
            await refreshCommentsOnly(articleId);
            
            // 記事一覧のコメント数も更新
            const article = articles.find(a => a.id === articleId);
            if (article) {
                article.comment_count = (article.comment_count || 0) + 1;
            }
            
            // キャッシュをクリア（コメント数が変更されたため）
            clearArticlesCache();
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
    
    // 現在表示中の記事のIDを取得（統合モード対応）
    const url = new URL(window.location);
    const articleId = url.searchParams.get('edit');
    if (!articleId) return;
    
    // 投稿ボタンを無効化してローディング状態に
    const submitBtn = textarea.parentElement.querySelector('.btn-primary');
    const originalBtnContent = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>投稿中...';
    submitBtn.classList.remove('btn-primary');
    submitBtn.classList.add('btn-secondary');
    
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
            // 投稿成功状態に変更
            submitBtn.innerHTML = '<i class="fas fa-check me-1"></i>投稿完了';
            submitBtn.classList.remove('btn-secondary');
            submitBtn.classList.add('btn-success');
            
            // 返信フォームを非表示にしてクリア
            hideReplyForm(parentCommentId);
            
            // パフォーマンス最適化: コメントのみ再読み込み（記事データは既に読み込み済み）
            await refreshCommentsOnly(articleId);
            
            // 記事一覧のコメント数も更新
            const article = articles.find(a => a.id === articleId);
            if (article) {
                article.comment_count = (article.comment_count || 0) + 1;
            }
            
            // キャッシュをクリア（コメント数が変更されたため）
            clearArticlesCache();
            
            // 2秒後にボタンを元に戻す
            setTimeout(() => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnContent;
                submitBtn.classList.remove('btn-success');
                submitBtn.classList.add('btn-primary');
            }, 2000);
            
        } else {
            // エラー状態に変更
            submitBtn.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>投稿失敗';
            submitBtn.classList.remove('btn-secondary');
            submitBtn.classList.add('btn-danger');
            
            setTimeout(() => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnContent;
                submitBtn.classList.remove('btn-danger');
                submitBtn.classList.add('btn-primary');
            }, 3000);
            
            console.error('返信投稿失敗:', data.error);
        }
    } catch (error) {
        console.error('返信投稿エラー:', error);
        
        // エラー状態に変更
        submitBtn.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>投稿失敗';
        submitBtn.classList.remove('btn-secondary');
        submitBtn.classList.add('btn-danger');
        
        setTimeout(() => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnContent;
            submitBtn.classList.remove('btn-danger');
            submitBtn.classList.add('btn-primary');
        }, 3000);
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
    
    // 現在表示中の記事のIDを取得（統合モード対応）
    const url = new URL(window.location);
    const articleId = url.searchParams.get('edit');
    if (!articleId) return;
    
    // 保存ボタンを無効化してローディング状態に
    const saveBtn = textarea.parentElement.querySelector('.btn-success');
    const originalBtnContent = saveBtn.innerHTML;
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>保存中...';
    saveBtn.classList.remove('btn-success');
    saveBtn.classList.add('btn-secondary');
    
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
            // 保存成功状態に変更
            saveBtn.innerHTML = '<i class="fas fa-check me-1"></i>保存完了';
            saveBtn.classList.remove('btn-secondary');
            saveBtn.classList.add('btn-success');
            
            // 編集フォームを非表示
            cancelCommentEdit(commentId);
            
            // コメントを再読み込み（統合モード対応）
            await loadAndRenderEditableArticleDetail(articleId);
            
        } else {
            // エラー状態に変更
            saveBtn.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>保存失敗';
            saveBtn.classList.remove('btn-secondary');
            saveBtn.classList.add('btn-danger');
            
            setTimeout(() => {
                saveBtn.disabled = false;
                saveBtn.innerHTML = originalBtnContent;
                saveBtn.classList.remove('btn-danger');
                saveBtn.classList.add('btn-success');
            }, 3000);
            
            console.error('コメント編集失敗:', data.error);
        }
    } catch (error) {
        console.error('コメント編集エラー:', error);
        
        // エラー状態に変更
        saveBtn.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>保存失敗';
        saveBtn.classList.remove('btn-secondary');
        saveBtn.classList.add('btn-danger');
        
        setTimeout(() => {
            saveBtn.disabled = false;
            saveBtn.innerHTML = originalBtnContent;
            saveBtn.classList.remove('btn-danger');
            saveBtn.classList.add('btn-success');
        }, 3000);
    }
}

// 編集可能な記事詳細を表示
async function showEditableArticleDetail(articleId) {
    try {
        // URL更新（ブラウザバック対応）
        const url = new URL(window.location);
        url.searchParams.set('edit', articleId);
        window.history.pushState({edit: articleId}, '', url);
        
        // 記事一覧コンテナを特定して非表示
        const mainContainer = document.querySelector('.main-content .container-fluid') || 
                             document.querySelector('#articlesContainer').closest('.container-fluid');
        
        if (mainContainer) {
            mainContainer.style.display = 'none';
        }
        
        // 記事詳細コンテナを作成・表示
        let detailContainer = document.getElementById('articleDetailView');
        if (!detailContainer) {
            detailContainer = document.createElement('div');
            detailContainer.id = 'articleDetailView';
            detailContainer.className = 'container-fluid py-3';
            
            const parentContainer = document.querySelector('.main-content') || 
                                   document.querySelector('main') || 
                                   document.body;
            
            if (parentContainer) {
                parentContainer.appendChild(detailContainer);
            } else {
                console.error('親コンテナが見つかりません');
                return;
            }
        }
        
        detailContainer.innerHTML = `
            <div class="mb-3">
                <button class="btn btn-outline-secondary" onclick="hideArticleDetail()">
                    <i class="fas fa-arrow-left"></i> 記事一覧に戻る
                </button>
            </div>
            <div id="detailLoading"></div>
            <div id="articleDetailContent" style="display: none;">
                <!-- 記事詳細がここに表示される -->
            </div>
        `;
        
        detailContainer.style.display = 'block';
        
        // ページトップにスクロール
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
        
        // スケルトンローダーを表示
        const detailLoading = document.getElementById('detailLoading');
        detailLoading.innerHTML = createArticleDetailSkeleton();
        detailLoading.style.display = 'block';
        
        // 記事詳細を読み込み
        await loadAndRenderEditableArticleDetail(articleId);
        
    } catch (error) {
        console.error('記事詳細表示エラー:', error);
    }
}

// 記事詳細を非表示にして一覧に戻る  
function hideArticleDetail() {
    // URL更新
    const url = new URL(window.location);
    url.searchParams.delete('detail');
    window.history.pushState({}, '', url);
    
    // 記事詳細を非表示
    const detailContainer = document.getElementById('articleDetailView');
    if (detailContainer) {
        detailContainer.style.display = 'none';
    }
    
    // 記事一覧を表示
    const mainContainer = document.querySelector('.main-content .container-fluid') || 
                         document.querySelector('#articlesContainer').closest('.container-fluid');
    
    if (mainContainer) {
        mainContainer.style.display = 'block';
    } else {
        console.error('記事一覧コンテナが見つかりません');
        // フォールバック: ページリロード
        window.location.reload();
    }
}

// 編集可能な記事詳細データを読み込んで表示
async function loadAndRenderEditableArticleDetail(articleId) {
    try {
        // 記事詳細とコメントを並列読み込み
        
        const [articleResponse, commentsResponse] = await Promise.all([
            fetch(`/api/articles?id=${articleId}`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            }),
            fetch(`/api/article-comments?article_id=${articleId}`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            })
        ]);
        
        const articleData = await articleResponse.json();
        const commentsData = await commentsResponse.json();
        
        if (!articleData.success || !articleData.articles?.length) {
            throw new Error('記事が見つかりません');
        }
        
        const article = articleData.articles[0];
        const comments = commentsData.success ? commentsData.comments || [] : [];
        
        // 編集可能な記事詳細を表示
        renderEditableArticleDetailContent(article, comments);
        
        // ローディングを非表示、コンテンツを表示
        document.getElementById('detailLoading').style.display = 'none';
        document.getElementById('articleDetailContent').style.display = 'block';
        
    } catch (error) {
        console.error('記事詳細読み込みエラー:', error);
        document.getElementById('detailLoading').innerHTML = 
            '<div class="alert alert-danger">記事の読み込みに失敗しました</div>';
    }
}

// 記事詳細コンテンツをレンダリング（編集可能）
function renderEditableArticleDetailContent(article, comments) {
    const container = document.getElementById('articleDetailContent');
    const sourceName = article.sources?.name || article.sources?.domain || 'Unknown';
    const pubDate = article.published_at ? formatJSTDisplay(article.published_at) : '不明';
    
    container.innerHTML = `
        <div class="row">
            <div class="col-12">
                <div class="card mb-4">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h4 class="mb-0">
                            ${article.flagged ? '<span class="badge bg-danger me-2">重要</span>' : ''}
                            ${escapeHtml(article.title || 'タイトルなし')}
                        </h4>
                        <div class="btn-group">
                            <button class="btn btn-outline-primary btn-sm" onclick="window.open('${escapeHtml(article.url)}', '_blank')">
                                <i class="fas fa-external-link-alt"></i> 元記事を開く
                            </button>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="row mb-3">
                            <!-- 左側: 情報源・URL・ステータス -->
                            <div class="col-md-3">
                                <!-- 公開日時 -->
                                <div class="mb-3">
                                    <div class="small text-muted">
                                        <i class="fas fa-calendar-alt me-1"></i>
                                        <span>${pubDate}</span>
                                    </div>
                                </div>
                                
                                <!-- 情報源 -->
                                <div class="mb-3">
                                    <div class="small text-muted">
                                        <i class="fas fa-rss me-1"></i>
                                        <span>${sourceName}</span>
                                    </div>
                                </div>
                                
                                <!-- URL -->
                                <div class="mb-3">
                                    <div class="small text-muted">
                                        <i class="fas fa-link me-1"></i>
                                        <a href="${article.url}" target="_blank" class="text-decoration-none text-truncate d-inline-block" title="${escapeHtml(article.url)}" style="max-width: 200px;">${article.url}</a>
                                    </div>
                                </div>
                                
                                <!-- ステータス -->
                                <div class="mb-3">
                                    <label class="form-label small mb-1">ステータス</label>
                                    <select class="form-select form-select-sm" id="editStatus">
                                        <option value="unread" ${article.status === 'unread' ? 'selected' : ''}>未読</option>
                                        <option value="reviewed" ${article.status === 'reviewed' ? 'selected' : ''}>確認済み</option>
                                        <option value="flagged" ${article.status === 'flagged' ? 'selected' : ''}>フラグ付き</option>
                                        <option value="archived" ${article.status === 'archived' ? 'selected' : ''}>アーカイブ</option>
                                    </select>
                                </div>
                                
                                <!-- 重要記事フラグ -->
                                <div class="mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="editFlagged" ${article.flagged ? 'checked' : ''}>
                                        <label class="form-check-label" for="editFlagged">重要記事</label>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- 右側: AI要約エリア -->
                            <div class="col-md-9">
                                <!-- AI要約セクション -->
                                <div class="ai-summary-section">
                                    <div class="d-flex justify-content-between align-items-center mb-3">
                                        <h5 class="mb-0">
                                            <i class="fas fa-robot me-2"></i> AI要約
                                        </h5>
                                        <button class="btn btn-outline-primary btn-sm" onclick="generateAISummary('${article.id}')" id="generateSummaryBtn">
                                            <i class="fas fa-magic me-1"></i> ${article.ai_summary ? '要約再生成' : '要約生成'}
                                        </button>
                                    </div>
                                    <div id="summaryContainer">
                                        ${article.ai_summary ? `
                                            <div class="alert alert-info mb-0" style="font-size: 0.95rem; line-height: 1.6;">
                                                <div>
                                                    ${escapeHtml(article.ai_summary)}
                                                </div>
                                                <div class="text-muted small mt-3 pt-2 border-top">
                                                    <i class="fas fa-robot me-1"></i>Google Gemini APIによる要約
                                                </div>
                                            </div>
                                        ` : `
                                            <div class="alert alert-light text-muted text-center py-4">
                                                <i class="fas fa-robot fa-2x mb-2 d-block"></i>
                                                「要約生成」ボタンをクリックして記事の要約を生成できます
                                            </div>
                                        `}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="article-comments mb-3">
                            <label class="form-label"><h5>備考</h5></label>
                            <textarea class="form-control" id="editComments" rows="4" placeholder="備考を入力...">${escapeHtml(article.comments || '')}</textarea>
                        </div>
                        <div class="d-flex justify-content-between align-items-center">
                            <div class="text-muted small">
                                ${article.reviewed_at ? `<i class="fas fa-clock me-1"></i>最終更新: ${formatJSTDisplay(article.reviewed_at)}` : ''}
                                ${article.last_edited_by ? ` <i class="fas fa-user me-1"></i>編集者: ${article.last_edited_by}` : ''}
                            </div>
                            <button class="btn btn-success btn-sm" onclick="saveArticleDetail('${article.id}')" id="saveBtn">
                                <i class="fas fa-save"></i> 保存
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">
                            <i class="fas fa-comments"></i> コメント
                            <span class="badge bg-secondary ms-2">${comments.length}</span>
                        </h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-4">
                            <h6>コメントを投稿</h6>
                            <div class="form-group mb-2">
                                <textarea class="form-control" id="newDetailComment" rows="3" placeholder="コメントを入力してください..."></textarea>
                            </div>
                            <button class="btn btn-primary" onclick="postDetailComment('${article.id}')">
                                <i class="fas fa-paper-plane"></i> コメントを投稿
                            </button>
                        </div>
                        
                        <div id="detailCommentsContainer">
                            ${renderDetailComments(comments)}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// 詳細画面用のコメント表示
function renderDetailComments(comments) {
    if (!comments || comments.length === 0) {
        return '<div class="text-muted text-center py-3">まだコメントはありません</div>';
    }
    
    const commentTree = buildCommentTree(comments);
    return commentTree.map((comment, index, array) => {
        const isLastRoot = index === array.length - 1;
        return renderCommentCard(comment, 0, isLastRoot);
    }).join('');
}

// 詳細画面用のコメント投稿
async function postDetailComment(articleId) {
    const commentText = document.getElementById('newDetailComment').value.trim();
    const submitBtn = document.querySelector(`button[onclick="postDetailComment('${articleId}')"]`);
    
    if (!commentText) {
        alert('コメントを入力してください');
        return;
    }
    
    // ボタンをローディング状態に変更
    const originalBtnContent = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>投稿中...';
    submitBtn.classList.remove('btn-primary');
    submitBtn.classList.add('btn-secondary');
    
    try {
        const response = await fetch('/api/article-comments', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                article_id: articleId,
                comment: commentText
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 投稿成功状態に変更
            submitBtn.innerHTML = '<i class="fas fa-check me-1"></i>投稿完了';
            submitBtn.classList.remove('btn-secondary');
            submitBtn.classList.add('btn-success');
            
            // フォームをクリア
            document.getElementById('newDetailComment').value = '';
            
            // 記事詳細を再読み込み（最新状態に更新）
            await loadAndRenderEditableArticleDetail(articleId);
            
            // 2秒後にボタンを元に戻す
            setTimeout(() => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnContent;
                submitBtn.classList.remove('btn-success');
                submitBtn.classList.add('btn-primary');
            }, 2000);
            
        } else {
            // エラー状態に変更
            submitBtn.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>投稿失敗';
            submitBtn.classList.remove('btn-secondary');
            submitBtn.classList.add('btn-danger');
            
            setTimeout(() => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnContent;
                submitBtn.classList.remove('btn-danger');
                submitBtn.classList.add('btn-primary');
            }, 3000);
            
            console.error('コメント投稿失敗:', data.error);
        }
        
    } catch (error) {
        console.error('コメント投稿エラー:', error);
        
        // エラー状態に変更
        submitBtn.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>投稿失敗';
        submitBtn.classList.remove('btn-secondary');
        submitBtn.classList.add('btn-danger');
        
        setTimeout(() => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnContent;
            submitBtn.classList.remove('btn-danger');
            submitBtn.classList.add('btn-primary');
        }, 3000);
    }
}

// コメント削除関数
async function deleteComment(commentId) {
    if (!confirm('このコメントを削除してもよろしいですか？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/article-comments?comment_id=${commentId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            // コメントカードを非表示にする
            const commentCard = document.querySelector(`[data-comment-id="${commentId}"]`);
            if (commentCard) {
                commentCard.style.transition = 'opacity 0.3s';
                commentCard.style.opacity = '0';
                setTimeout(() => {
                    commentCard.remove();
                }, 300);
            }
            
            // 記事一覧のコメント数を更新
            // URLから記事IDを取得
            const urlParams = new URLSearchParams(window.location.search);
            const articleId = urlParams.get('edit');
            if (articleId) {
                const article = articles.find(a => a.id === articleId);
                if (article && article.comment_count > 0) {
                    article.comment_count--;
                    // 記事一覧の表示も更新
                    const countBadge = document.querySelector(`tr[data-id="${articleId}"] .comment-count`);
                    if (countBadge) {
                        countBadge.textContent = article.comment_count;
                        countBadge.className = article.comment_count > 0 ? 'badge bg-primary ms-1 comment-count' : 'badge bg-secondary ms-1 comment-count';
                    }
                }
            }
            
            // キャッシュをクリア（コメント数が変更されたため）
            clearArticlesCache();
        } else {
            alert('削除に失敗しました: ' + (data.error || '不明なエラー'));
        }
    } catch (error) {
        console.error('コメント削除エラー:', error);
        alert('削除に失敗しました');
    }
}

// ブラウザバック対応
window.addEventListener('popstate', (e) => {
    if (e.state && e.state.edit) {
        showEditableArticleDetail(e.state.edit);
    } else {
        hideArticleDetail();
        // URLパラメータに基づいてページ表示を更新
        const urlParams = new URLSearchParams(window.location.search);
        const page = parseInt(urlParams.get('page')) || 1;
        const status = urlParams.get('status') || '';
        const flagged = urlParams.get('flagged') || '';
        const source = urlParams.get('source') || '';
        const comment = urlParams.get('comment') || '';
        const sort = urlParams.get('sort') || 'desc';
        
        // フィルター要素の状態を更新
        if (document.getElementById('statusFilter')) {
            document.getElementById('statusFilter').value = status;
        }
        if (document.getElementById('flaggedFilter')) {
            document.getElementById('flaggedFilter').value = flagged;
        }
        if (document.getElementById('sourceFilter')) {
            document.getElementById('sourceFilter').value = source;
        }
        if (document.getElementById('commentFilter')) {
            document.getElementById('commentFilter').value = comment;
        }
        if (document.getElementById('sortOrder')) {
            document.getElementById('sortOrder').value = sort;
        }
        
        // 現在のページ番号を更新
        currentPage = page;
        
        // 総件数を取得してから指定ページを読み込み
        getTotalArticlesCount().then(totalCount => {
            loadArticlesPage(page, totalCount);
        }).catch(error => {
            console.error('総件数取得エラー:', error);
            loadArticlesPage(page);
        });
    }
});

// 記事詳細の保存
async function saveArticleDetail(articleId) {
    const status = document.getElementById('editStatus').value;
    const flagged = document.getElementById('editFlagged').checked;
    const comments = document.getElementById('editComments').value.trim();
    
    try {
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
        
        // 保存成功のフィードバック
        const saveBtn = document.getElementById('saveBtn');
        const originalText = saveBtn.innerHTML;
        saveBtn.innerHTML = '<i class="fas fa-check"></i> 保存済み';
        saveBtn.classList.replace('btn-success', 'btn-outline-success');
        
        setTimeout(() => {
            saveBtn.innerHTML = originalText;
            saveBtn.classList.replace('btn-outline-success', 'btn-success');
        }, 2000);
        
        // 記事一覧のデータも更新
        const articleIndex = articles.findIndex(a => a.id == articleId);
        if (articleIndex !== -1) {
            articles[articleIndex].status = status;
            articles[articleIndex].flagged = flagged;
            articles[articleIndex].comments = comments || null;
            articles[articleIndex].reviewed_at = new Date().toISOString();
        }
        
        // キャッシュをクリア（記事データが変更されたため）
        clearArticlesCache();
        
    } catch (error) {
        console.error('保存エラー:', error);
        alert('保存に失敗しました: ' + error.message);
    }
}



// 段階的ローディング表示（廃止 - showLoadingState()に統一）

// スケルトンローダーを隠す（廃止 - renderArticles()で自動置換）

// キャッシング戦略: キャッシュキー生成
function generateCacheKey(page, filters) {
    const { statusFilter, flaggedFilter, sourceFilter, commentFilter, sortOrder, itemsPerPage } = filters || {};
    return `page_${page}_status_${statusFilter || ''}_flagged_${flaggedFilter || ''}_source_${sourceFilter || ''}_comment_${commentFilter || ''}_sort_${sortOrder || 'desc'}_limit_${itemsPerPage || 20}`;
}

// キャッシング戦略: 記事データをキャッシュから取得
function getArticlesFromCache(cacheKey) {
    const cached = articlesCache.get(cacheKey);
    const cacheTime = articlesCacheTime.get(cacheKey);
    
    if (cached && cacheTime && (Date.now() - cacheTime) < ARTICLES_CACHE_DURATION) {
        console.log('記事データをキャッシュから取得:', cacheKey);
        return cached;
    }
    
    return null;
}

// キャッシング戦略: 記事データをキャッシュに保存
function setArticlesCache(cacheKey, data) {
    articlesCache.set(cacheKey, data);
    articlesCacheTime.set(cacheKey, Date.now());
    console.log('記事データをキャッシュに保存:', cacheKey);
    
    // キャッシュサイズ制限（メモリ管理）
    if (articlesCache.size > 20) {
        const oldestKey = Array.from(articlesCacheTime.entries())
            .sort((a, b) => a[1] - b[1])[0][0];
        articlesCache.delete(oldestKey);
        articlesCacheTime.delete(oldestKey);
    }
}

// キャッシング戦略: キャッシュをクリア（データ更新時）
function clearArticlesCache() {
    articlesCache.clear();
    articlesCacheTime.clear();
    console.log('記事キャッシュをクリア');
}

// ページネーションクリック時のUX改善
async function handlePaginationClick(page) {
    // 既に同じページの場合は何もしない
    if (page === currentPage) {
        return;
    }
    
    // 1. ページネーションボタンを無効化
    disablePaginationButtons();
    
    // 2. ページトップにスムーススクロール
    window.scrollTo({ 
        top: 0, 
        behavior: 'smooth' 
    });
    
    // 3. 記事一覧にスケルトンローダーを表示
    const articlesContainer = document.getElementById('articlesContainer');
    const loadingElement = document.getElementById('loading');
    
    // スケルトンローダーを表示
    if (articlesContainer) {
        showLoadingState();
        articlesContainer.style.display = 'block';
    }
    
    // 従来のローディング要素を非表示
    if (loadingElement) {
        loadingElement.style.display = 'none';
    }
    
    // 4. 少し待ってからページ読み込み（スムーススクロールが完了するまで）
    setTimeout(async () => {
        try {
            await loadArticlesPage(page);
            // 成功時はページネーションボタンを再有効化（loadArticlesPageで処理される）
        } catch (error) {
            console.error('ページ読み込みエラー:', error);
            // ローディング要素を非表示にして記事一覧を表示
            if (loadingElement) {
                loadingElement.style.display = 'none';
            }
            const articlesContainer = document.getElementById('articlesContainer');
            if (articlesContainer) {
                articlesContainer.style.display = 'block';
                articlesContainer.innerHTML = '<div class="alert alert-danger">ページの読み込みに失敗しました</div>';
            }
            // エラー時もページネーションボタンを再有効化
            enablePaginationButtons();
        }
    }, 300); // 300ms待機（スクロールアニメーション時間を考慮）
}

// ページネーションボタンを無効化
function disablePaginationButtons() {
    const paginationButtons = document.querySelectorAll('#paginationList .page-link, #paginationListTop .page-link');
    paginationButtons.forEach(button => {
        button.style.pointerEvents = 'none';
        button.style.opacity = '0.6';
    });
}

// ページネーションボタンを有効化
function enablePaginationButtons() {
    const paginationButtons = document.querySelectorAll('#paginationList .page-link, #paginationListTop .page-link');
    paginationButtons.forEach(button => {
        button.style.pointerEvents = '';
        button.style.opacity = '';
    });
}

// パフォーマンス最適化: コメントのみ再読み込み
async function refreshCommentsOnly(articleId) {
    try {
        const response = await fetch(`/api/article-comments?article_id=${articleId}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        const commentsData = await response.json();
        
        if (commentsData.success) {
            const comments = commentsData.comments || [];
            const commentsContainer = document.getElementById('commentsContainer');
            
            if (commentsContainer) {
                // コメント数を更新
                const commentsCount = document.getElementById('commentsCount');
                if (commentsCount) {
                    commentsCount.textContent = `${comments.length}件`;
                }
                
                // コメント一覧を再描画
                if (comments.length === 0) {
                    commentsContainer.innerHTML = '<p class="text-muted">まだコメントはありません</p>';
                } else {
                    const commentsTree = buildCommentTree(comments);
                    commentsContainer.innerHTML = Object.values(commentsTree)
                        .map(commentGroup => renderCommentCard(commentGroup.root, 0, false, commentGroup.replies))
                        .join('');
                }
            }
        }
    } catch (error) {
        console.error('コメント再読み込みエラー:', error);
        // エラー時は従来の方法にフォールバック
        await loadAndRenderEditableArticleDetail(articleId);
    }
}

// AI要約生成機能
async function generateAISummary(articleId) {
    const generateBtn = document.getElementById('generateSummaryBtn');
    const summaryContainer = document.getElementById('summaryContainer');
    
    // ボタンをローディング状態に変更
    generateBtn.disabled = true;
    generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 生成中...';
    
    // ローディング表示
    summaryContainer.innerHTML = `
        <div class="d-flex align-items-center text-muted">
            <div class="spinner-border spinner-border-sm me-2" role="status">
                <span class="visually-hidden">生成中...</span>
            </div>
            記事を読み込んでAI要約を生成しています...
        </div>
    `;
    
    try {
        // 記事データを取得
        const articleResponse = await fetch(`/api/articles?id=${articleId}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        const articleData = await articleResponse.json();
        if (!articleData.success || !articleData.articles?.length) {
            throw new Error('記事データの取得に失敗しました');
        }
        
        const article = articleData.articles[0];
        
        // 記事URLをチェック
        if (!article.url || article.url.trim().length === 0) {
            throw new Error('記事URLが存在しないため要約を生成できません');
        }
        
        // AI要約APIを呼び出し
        const summaryResponse = await fetch('/api/article-summary', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                article_id: articleId,
                article_url: article.url
            })
        });
        
        // レスポンスのデバッグ情報を追加
        console.log('Summary API response status:', summaryResponse.status);
        console.log('Summary API response headers:', summaryResponse.headers);
        
        const responseText = await summaryResponse.text();
        console.log('Summary API raw response:', responseText);
        
        let summaryData;
        try {
            summaryData = JSON.parse(responseText);
        } catch (parseError) {
            console.error('JSON parse error:', parseError);
            console.error('Response text that failed to parse:', responseText);
            throw new Error(`サーバーから無効なレスポンスが返されました: ${parseError.message}`);
        }
        
        if (summaryData.success) {
            // デバッグ情報をコンソールに出力
            if (summaryData.debug_info) {
                console.log('=== EXTRACTED ARTICLE CONTENT START ===');
                console.log('Full content length:', summaryData.debug_info.extracted_content_length);
                console.log('Content preview:', summaryData.debug_info.extracted_content_preview);
                console.log('=== EXTRACTED ARTICLE CONTENT END ===');
            }
            
            // 成功時の表示
            summaryContainer.innerHTML = `
                <div class="alert alert-info mb-0">
                    <div style="line-height: 1.4;">
                        <i class="fas fa-lightbulb me-1"></i>
                        ${escapeHtml(summaryData.summary)}
                    </div>
                    <div class="text-muted small mt-2">
                        <i class="fas fa-robot me-1"></i>Google Gemini APIによる要約
                    </div>
                </div>
            `;
            
            // ボタンのテキストを更新（既存要約がある場合は「再生成完了」）
            const hasExistingSummary = generateBtn.innerHTML.includes('再生成');
            generateBtn.innerHTML = `<i class="fas fa-check"></i> ${hasExistingSummary ? '再生成完了' : '生成完了'}`;
            generateBtn.classList.remove('btn-outline-primary');
            generateBtn.classList.add('btn-success');
            
            // 2秒後にボタンを元の状態に戻す
            setTimeout(() => {
                generateBtn.innerHTML = '<i class="fas fa-magic"></i> 要約再生成';
                generateBtn.classList.remove('btn-success');
                generateBtn.classList.add('btn-outline-primary');
            }, 2000);
            
        } else {
            throw new Error(summaryData.error || '要約の生成に失敗しました');
        }
        
    } catch (error) {
        console.error('AI要約生成エラー:', error);
        
        // エラー表示
        summaryContainer.innerHTML = `
            <div class="alert alert-warning mb-0">
                <i class="fas fa-exclamation-triangle me-1"></i>
                要約の生成に失敗しました: ${escapeHtml(error.message)}
                <button class="btn btn-outline-warning btn-sm ms-2" onclick="generateAISummary('${articleId}')">
                    <i class="fas fa-retry"></i> 再試行
                </button>
            </div>
        `;
        
        // ボタンを元に戻す
        generateBtn.innerHTML = '<i class="fas fa-magic"></i> 要約生成';
        generateBtn.classList.remove('btn-success');
        generateBtn.classList.add('btn-outline-primary');
    } finally {
        // ボタンを有効化
        generateBtn.disabled = false;
    }
}
