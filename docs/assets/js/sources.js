// CFRP Monitor - 情報源管理ページJavaScript

let sources = [];
let candidates = [];
let currentEditingSourceId = null;
let currentViewMode = 'sources'; // 'sources' または 'candidates'
let authToken = null;
let userFeatures = null;

// 初期化
document.addEventListener('DOMContentLoaded', async () => {
    // 認証チェックはメインページのスクリプトで実行済み
    authToken = localStorage.getItem('auth_token');
    
    // レイアウトAPIの呼び出しが完了するまで待機
    const checkAuthInterval = setInterval(() => {
        if (window.userFeatures) {
            clearInterval(checkAuthInterval);
            initializePage();
        }
    }, 100);
    
    // 5秒後にタイムアウト
    setTimeout(() => {
        clearInterval(checkAuthInterval);
        if (!window.userFeatures) {
            window.location.href = '/login';
        }
    }, 5000);
});

async function initializePage() {
    // 権限チェック
    if (!window.userFeatures.can_manage_sources) {
        document.body.innerHTML = `
            <div class="container-fluid py-4">
                <div class="alert alert-danger text-center">
                    <h4>アクセス拒否</h4>
                    <p>情報源管理にアクセスする権限がありません。</p>
                    <a href="/articles" class="btn btn-primary">記事管理に戻る</a>
                </div>
            </div>
        `;
        return;
    }
    
    userFeatures = window.userFeatures;
    
    await loadSources();
    await loadCandidates();
    setupEventListeners();
    
    // 明示的に情報源リストモードに設定
    switchViewMode('sources');
}

// 情報源一覧を読み込み
async function loadSources() {
    try {
        const deletedFilter = document.getElementById('deletedFilter')?.value || 'active';
        
        const response = await fetch(`/api/sources?include_deleted=${deletedFilter}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || '情報源の読み込みに失敗しました');
        }
        
        sources = data.sources || [];
        populateFilters();
        renderSources();
        updateStats();
        
        document.getElementById('loading').style.display = 'none';
        document.getElementById('sourcesContainer').style.display = 'block';
        document.getElementById('statsContainer').style.display = 'block';
    } catch (error) {
        console.error('情報源読み込みエラー:', error);
        document.getElementById('loading').innerHTML = 
            '<div class="alert alert-danger">情報源の読み込みに失敗しました: ' + error.message + '</div>';
    }
}

// タスクログ機能は現在のAPIでは実装しないため削除

// フィルターを設定
function populateFilters() {
    // カテゴリフィルター
    const categories = [...new Set(sources.map(s => s.category).filter(Boolean))];
    const categorySelect = document.getElementById('categoryFilter');
    categories.forEach(category => {
        const option = document.createElement('option');
        option.value = category;
        option.textContent = category;
        categorySelect.appendChild(option);
    });

    // 国フィルター
    const countries = [...new Set(sources.map(s => s.country_code).filter(Boolean))];
    const countrySelect = document.getElementById('countryFilter');
    countries.forEach(country => {
        const option = document.createElement('option');
        option.value = country;
        option.textContent = country;
        countrySelect.appendChild(option);
    });
}

// 統計情報を更新
function updateStats() {
    const filtered = filterAndSortSources();
    const stats = {
        auto: filtered.filter(s => s.acquisition_mode === 'auto').length,
        manual: filtered.filter(s => s.acquisition_mode === 'manual').length,
        disabled: filtered.filter(s => s.acquisition_mode === 'disabled').length,
        new: filtered.filter(s => s.acquisition_mode === 'new').length,
        total: filtered.length
    };

    document.getElementById('autoCount').textContent = stats.auto;
    document.getElementById('manualCount').textContent = stats.manual;
    document.getElementById('disabledCount').textContent = stats.disabled;
    document.getElementById('newCount').textContent = stats.new;
    document.getElementById('totalCount').textContent = stats.total;
}

// 情報源を表示
function renderSources() {
    const container = document.getElementById('sourcesContainer');
    const filteredSources = filterAndSortSources();
    
    if (filteredSources.length === 0) {
        container.innerHTML = '<div class="alert alert-info">該当する情報源がありません</div>';
        return;
    }

    container.innerHTML = filteredSources.map(source => createCompactSourceCard(source)).join('');
    updateStats();
}

// フィルタリングとソート
function filterAndSortSources() {
    const modeFilter = document.getElementById('modeFilter').value;
    const categoryFilter = document.getElementById('categoryFilter').value;
    const countryFilter = document.getElementById('countryFilter').value;
    const sortOrder = document.getElementById('sortOrder').value;

    // フィルタリング
    let filtered = sources.filter(source => {
        if (modeFilter && source.acquisition_mode !== modeFilter) return false;
        if (categoryFilter && source.category !== categoryFilter) return false;
        if (countryFilter && source.country_code !== countryFilter) return false;
        return true;
    });

    // ソート
    filtered.sort((a, b) => {
        switch (sortOrder) {
            case 'name':
                return (a.name || '').localeCompare(b.name || '');
            case 'mode':
                return (a.acquisition_mode || '').localeCompare(b.acquisition_mode || '');
            case 'relevance':
                return (b.relevance || 0) - (a.relevance || 0);
            case 'created':
                return new Date(b.created_at || 0) - new Date(a.created_at || 0);
            default:
                return 0;
        }
    });

    return filtered;
}

// コンパクトな情報源カードを作成
function createCompactSourceCard(source) {
    const modeClass = source.deleted ? 'deleted-source' :
                     source.acquisition_mode === 'disabled' ? 'disabled-source' :
                     source.acquisition_mode === 'manual' ? 'manual-source' :
                     source.acquisition_mode === 'new' ? 'new-source' : 'auto-source';
    
    const urls = Array.isArray(source.urls) ? source.urls : [];
    const primaryUrl = urls.length > 0 ? urls[0] : source.domain;
    
    return `
        <div class="compact-card ${modeClass}" data-id="${source.id}">
            <div class="compact-info">
                <div class="compact-main">
                    <h6 class="mb-1">${escapeHtml(source.name || source.domain)}</h6>
                    <div class="small text-muted">${escapeHtml(primaryUrl)}</div>
                    ${source.acquisition_mode === 'auto' && source.last_collected_at ? `
                        <div class="small text-success mt-1">🕒 最終収集: ${new Date(source.last_collected_at).toLocaleString('ja-JP')}</div>
                    ` : ''}
                    ${source.description ? `<div class="small text-info mt-1">💬 ${escapeHtml(source.description)}</div>` : ''}
                </div>
                <div class="compact-meta">
                    <span><i class="fas fa-folder"></i> ${source.category || 'その他'}</span>
                    <span><i class="fas fa-globe-americas"></i> ${source.country_code || '?'}</span>
                    <span><i class="fas fa-star"></i> ${source.relevance || 0}</span>
                    ${source.deleted ? 
                        '<span class="badge bg-secondary ms-2">削除済み</span>' :
                        `<span class="badge bg-${getModeColor(source.acquisition_mode)} ms-2">
                            ${getModeLabel(source.acquisition_mode)}
                        </span>`
                    }
                </div>
            </div>
        </div>
    `;
}

// 詳細編集用の情報源カードを作成
function createDetailSourceCard(source) {
    const modeClass = source.acquisition_mode === 'disabled' ? 'disabled-source' :
                     source.acquisition_mode === 'manual' ? 'manual-source' :
                     source.acquisition_mode === 'new' ? 'new-source' : 'auto-source';
    
    const urls = Array.isArray(source.urls) ? source.urls : [];
    const policyUrl = source.policy_url;
    
    return `
        <div class="source-card ${modeClass}" data-id="${source.id}">
            <div class="d-flex justify-content-between align-items-start mb-2">
                <h5 class="mb-1">
                    ${escapeHtml(source.name || source.domain)}
                </h5>
                <span class="badge bg-${getModeColor(source.acquisition_mode)} status-badge">
                    ${getModeLabel(source.acquisition_mode)}
                </span>
            </div>
            
            <div class="source-meta mb-2">
                <span class="me-3"><i class="fas fa-globe"></i> ${source.domain}</span>
                <span class="me-3"><i class="fas fa-folder"></i> ${source.category || 'その他'}</span>
                <span class="me-3"><i class="fas fa-globe-americas"></i> ${source.country_code || 'Unknown'}</span>
                <span class="me-3"><i class="fas fa-star"></i> ${source.relevance || 0}</span>
            </div>
            
            <div class="url-editor mb-2">
                <strong>RSS/URL:</strong>
                <div class="url-container" data-id="${source.id}">
                    ${urls.map((url, index) => `
                        <div class="url-item" data-index="${index}">
                            <input type="url" class="form-control form-control-sm url-input" 
                                   value="${escapeHtml(url)}" placeholder="https://example.com/feed.xml">
                            <div class="url-actions">
                                <button class="btn btn-outline-primary btn-sm test-url-btn" 
                                        data-url="${escapeHtml(url)}" title="RSS記事を取得テスト">
                                    <i class="fas fa-search"></i>
                                </button>
                                <button class="btn btn-outline-danger btn-sm remove-url-btn" 
                                        title="URLを削除">
                                    ✕
                                </button>
                            </div>
                        </div>
                    `).join('')}
                    <div class="add-url-section">
                        <div class="input-group input-group-sm">
                            <input type="url" class="form-control new-url-input" 
                                   placeholder="新しいURLを追加...">
                            <button class="btn btn-outline-success add-url-btn" type="button">
                                <i class="fas fa-plus"></i> 追加
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            ${policyUrl ? `
                <div class="policy-url">
                    <strong>プライバシーポリシー:</strong> 
                    <a href="${policyUrl}" target="_blank" class="text-decoration-none small">${policyUrl}</a>
                </div>
            ` : ''}
            
            <div class="controls">
                <div class="row g-2">
                    <div class="col-md-3">
                        <label class="form-label small">取得モード:</label>
                        <select class="form-select form-select-sm mode-select" data-id="${source.id}">
                            <option value="auto" ${source.acquisition_mode === 'auto' ? 'selected' : ''}>自動収集</option>
                            <option value="manual" ${source.acquisition_mode === 'manual' ? 'selected' : ''}>手動のみ</option>
                            <option value="disabled" ${source.acquisition_mode === 'disabled' ? 'selected' : ''}>停止中</option>
                            <option value="new" ${source.acquisition_mode === 'new' ? 'selected' : ''}>新規追加</option>
                        </select>
                    </div>
                    <div class="col-md-2">
                        <label class="form-label small">関連度:</label>
                        <input type="number" class="form-control form-control-sm relevance-input" 
                               data-id="${source.id}" value="${source.relevance || 0}" min="0" max="10">
                    </div>
                    <div class="col-md-5">
                        <label class="form-label small">備考:</label>
                        <textarea class="form-control form-control-sm description-textarea" 
                                 data-id="${source.id}" rows="2" 
                                 placeholder="備考・メモを入力...">${escapeHtml(source.description || '')}</textarea>
                    </div>
                    <div class="col-md-2 d-flex align-items-end">
                        <button class="btn btn-success btn-sm save-btn w-100" data-id="${source.id}">保存</button>
                    </div>
                </div>
                <div class="mt-2">
                    ${source.updated_at ? `<small class="text-muted">最終更新: ${new Date(source.updated_at).toLocaleString('ja-JP')}</small>` : ''}
                    ${source.last_edited_by ? `<small class="text-info ms-3">編集者: ${source.last_edited_by}</small>` : ''}
                    ${source.acquisition_mode === 'auto' && source.last_collected_at ? `
                        <small class="text-success ms-3">🕒 最終収集: ${new Date(source.last_collected_at).toLocaleString('ja-JP')}</small>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

// モードの色を取得
function getModeColor(mode) {
    const colors = {
        'auto': 'success',
        'manual': 'warning',
        'disabled': 'danger',
        'new': 'info'
    };
    return colors[mode] || 'secondary';
}

// モードのラベルを取得
function getModeLabel(mode) {
    const labels = {
        'auto': '自動収集',
        'manual': '手動のみ',
        'disabled': '停止中',
        'new': '新規追加'
    };
    return labels[mode] || '不明';
}

// HTMLエスケープ
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// イベントリスナーを設定
function setupEventListeners() {
    // フィルター・ソート変更時
    ['modeFilter', 'categoryFilter', 'countryFilter', 'sortOrder'].forEach(id => {
        document.getElementById(id).addEventListener('change', renderSources);
    });
    
    // 削除フィルター変更時は再読み込み
    document.getElementById('deletedFilter').addEventListener('change', async () => {
        await loadSources();
    });

    // 更新ボタン
    document.getElementById('refreshBtn').addEventListener('click', async () => {
        document.getElementById('refreshBtn').disabled = true;
        await loadSources();
        document.getElementById('refreshBtn').disabled = false;
    });

    // コンパクトカードクリックのイベント委譲
    document.getElementById('sourcesContainer').addEventListener('click', (e) => {
        const card = e.target.closest('.compact-card');
        if (card) {
            const sourceId = card.dataset.id; // UUID文字列なのでparseIntしない
            openEditMode(sourceId);
        }
    });

    // 編集モードのイベント委譲
    document.getElementById('editModeContainer').addEventListener('click', async (e) => {
        if (e.target.classList.contains('save-btn')) {
            await saveSource(e.target.dataset.id);
        } else if (e.target.classList.contains('add-url-btn')) {
            addNewUrl(e.target);
        } else if (e.target.classList.contains('remove-url-btn')) {
            removeUrl(e.target);
        } else if (e.target.classList.contains('test-url-btn')) {
            await testUrl(e.target);
        } else if (e.target.classList.contains('btn-close-edit')) {
            closeEditMode();
        } else if (e.target.classList.contains('btn-delete-source')) {
            await deleteSource();
        }
    });
}

// 情報源を保存
async function saveSource(sourceId) {
    const card = document.querySelector(`[data-id="${sourceId}"]`);
    const mode = card.querySelector('.mode-select').value;
    const relevance = parseInt(card.querySelector('.relevance-input').value) || 0;
    const description = card.querySelector('.description-textarea')?.value;
    
    // URLリストを収集
    const urlInputs = card.querySelectorAll('.url-input');
    const urls = Array.from(urlInputs)
        .map(input => input.value.trim())
        .filter(url => url.length > 0);
    
    try {
        const updateData = {
            acquisition_mode: mode,
            relevance: relevance,
            description: description === '' ? null : description,
            urls: urls
        };
        
        const response = await fetch(`/api/sources?id=${sourceId}`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updateData)
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || '保存に失敗しました');
        }
        
        // UIを更新
        const saveBtn = card.querySelector('.save-btn');
        const originalText = saveBtn.textContent;
        saveBtn.textContent = '保存済み';
        saveBtn.classList.replace('btn-success', 'btn-outline-success');
        
        setTimeout(() => {
            saveBtn.textContent = originalText;
            saveBtn.classList.replace('btn-outline-success', 'btn-success');
        }, 2000);
        
        // カードのスタイルを更新
        card.className = `source-card ${mode === 'disabled' ? 'disabled-source' : 
                                       mode === 'manual' ? 'manual-source' :
                                       mode === 'new' ? 'new-source' : 'auto-source'}`;
        
        // ソースデータを更新
        const sourceIndex = sources.findIndex(s => s.id == sourceId);
        if (sourceIndex !== -1) {
            sources[sourceIndex].acquisition_mode = mode;
            sources[sourceIndex].relevance = relevance;
            sources[sourceIndex].description = description === '' ? null : description;
            sources[sourceIndex].urls = urls;
            sources[sourceIndex].updated_at = new Date().toISOString();
        }
        
        // 一覧表示を更新
        renderSources();
        
        // 統計情報を更新
        updateStats();
        
    } catch (error) {
        console.error('保存エラー:', error);
        alert('保存に失敗しました: ' + error.message);
    }
}

// 新しいURLを追加
function addNewUrl(button) {
    const container = button.closest('.url-container');
    const newUrlInput = container.querySelector('.new-url-input');
    const newUrl = newUrlInput.value.trim();
    
    if (!newUrl) {
        alert('URLを入力してください');
        return;
    }
    
    if (!isValidUrl(newUrl)) {
        alert('有効なURLを入力してください');
        return;
    }
    
    // 重複チェック
    const existingUrls = Array.from(container.querySelectorAll('.url-input'))
        .map(input => input.value.trim());
    if (existingUrls.includes(newUrl)) {
        alert('このURLは既に存在します');
        return;
    }
    
    // 新しいURL項目を作成
    const urlItemsContainer = container.querySelector('.add-url-section');
    const newUrlItem = document.createElement('div');
    newUrlItem.className = 'url-item';
    newUrlItem.innerHTML = `
        <input type="url" class="form-control form-control-sm url-input" 
               value="${escapeHtml(newUrl)}" placeholder="https://example.com/feed.xml">
        <div class="url-actions">
            <button class="btn btn-outline-primary btn-sm test-url-btn" 
                    data-url="${escapeHtml(newUrl)}" title="URLをテスト">
                <i class="fas fa-search"></i>
            </button>
            <button class="btn btn-outline-danger btn-sm remove-url-btn" 
                    title="URLを削除">
                ✕
            </button>
        </div>
    `;
    
    // 追加セクションの前に挿入
    urlItemsContainer.parentNode.insertBefore(newUrlItem, urlItemsContainer);
    
    // 入力欄をクリア
    newUrlInput.value = '';
}

// URLを削除
function removeUrl(button) {
    const urlItem = button.closest('.url-item');
    const container = button.closest('.url-container');
    
    // 最後のURL項目は削除を確認
    const urlItems = container.querySelectorAll('.url-item');
    if (urlItems.length === 1) {
        if (!confirm('最後のURLを削除してもよろしいですか？')) {
            return;
        }
    }
    
    urlItem.remove();
}

// URLをテスト（RSS記事取得）
async function testUrl(button) {
    const url = button.dataset.url || button.closest('.url-item').querySelector('.url-input').value;
    if (!url) return;
    
    // モーダルを開く
    openRssTestModal(url);
}

// RSSテストモーダルを開く
function openRssTestModal(url) {
    const modal = document.getElementById('rssTestModal');
    const overlay = document.querySelector('.rss-test-overlay');
    const content = document.getElementById('rssTestContent');
    
    modal.style.display = 'block';
    overlay.style.display = 'block';
    
    // ローディング表示
    content.innerHTML = `
        <div class="text-center">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">読み込み中...</span>
            </div>
            <p class="mt-2">RSSフィードを取得中...</p>
            <p class="small text-muted">${escapeHtml(url)}</p>
        </div>
    `;
    
    // RSSを取得してテスト
    testRssFeed(url, content);
}

// RSSテストモーダルを閉じる
function closeRssTestModal() {
    document.getElementById('rssTestModal').style.display = 'none';
    document.querySelector('.rss-test-overlay').style.display = 'none';
}

// RSSフィードをテスト
async function testRssFeed(url, contentElement = null) {
    const content = contentElement || document.getElementById('rssTestContent');
    
    try {
        // CORSプロキシを使用（無料の公開プロキシ）
        // 複数のプロキシを試す
        const proxies = [
            { 
                name: 'allorigins',
                url: (url) => `https://api.allorigins.win/get?url=${encodeURIComponent(url)}`,
                isJson: true
            },
            { 
                name: 'corsproxy.io',
                url: (url) => `https://corsproxy.io/?${encodeURIComponent(url)}`,
                isJson: false
            }
        ];
        
        let data = null;
        let lastError = null;
        
        // 各プロキシを順番に試す
        for (let i = 0; i < proxies.length; i++) {
            const proxy = proxies[i];
            try {
                const proxyUrl = proxy.url(url);
                console.log(`Trying ${proxy.name}: ${proxyUrl}`);
                
                const response = await fetch(proxyUrl);
                
                if (!response.ok) {
                    throw new Error(`HTTPエラー: ${response.status} ${response.statusText}`);
                }
                
                // プロキシによって異なるレスポンス形式を処理
                if (proxy.isJson) {
                    const jsonData = await response.json();
                    if (!jsonData.contents) {
                        throw new Error(`フィード取得失敗: ${jsonData.status?.http_code || 'No content'}`);
                    }
                    data = jsonData.contents;
                } else {
                    data = await response.text();
                }
                
                console.log(`Successfully fetched with ${proxy.name}`);
                break; // 成功したらループを抜ける
                
            } catch (error) {
                console.error(`${proxy.name} failed:`, error);
                lastError = error;
                if (i === proxies.length - 1) {
                    throw new Error(`全てのプロキシで失敗: ${lastError.message}`);
                }
            }
        }
        
        if (!data) {
            throw new Error('フィードの取得に失敗しました');
        }
        
        // XMLをパース
        console.log('Raw data (first 500 chars):', data.substring(0, 500));
        
        // XMLの先頭の空白や改行を削除
        const cleanData = data.trim();
        
        const parser = new DOMParser();
        const xml = parser.parseFromString(cleanData, 'text/xml');
        
        // エラーチェック
        const parseError = xml.querySelector('parsererror');
        if (parseError) {
            console.error('Parse error details:', parseError.textContent);
            console.error('XML start:', cleanData.substring(0, 200));
            
            // HTMLとして返されている可能性をチェック
            if (cleanData.toLowerCase().includes('<!doctype html') || cleanData.toLowerCase().includes('<html')) {
                // Access Deniedの場合
                if (cleanData.toLowerCase().includes('access denied')) {
                    throw new Error('ACCESS_DENIED');
                }
                throw new Error('HTMLページが返されました（RSSフィードではありません）');
            }
            
            throw new Error(`無効なXMLフォーマット: ${parseError.textContent.substring(0, 100)}`);
        }
        
        // RSS/Atomフィードの解析
        const items = xml.querySelectorAll('item, entry');
        if (items.length === 0) {
            throw new Error('記事が見つかりません');
        }
        
        // 最初の記事を取得
        const firstItem = items[0];
        const title = firstItem.querySelector('title')?.textContent || 'タイトルなし';
        const link = firstItem.querySelector('link')?.textContent || 
                    firstItem.querySelector('link')?.getAttribute('href') || '';
        const description = firstItem.querySelector('description, summary, content')?.textContent || '';
        const pubDate = firstItem.querySelector('pubDate, published, updated')?.textContent || '';
        
        // 結果を表示
        content.innerHTML = `
            <div class="alert alert-success">
                <h6><i class="fas fa-check-circle text-success"></i> RSSフィードの取得に成功しました！</h6>
                <p class="mb-1">記事数: ${items.length}件</p>
            </div>
            
            <h6>最新記事のプレビュー:</h6>
            <div class="rss-article-preview">
                <h6 class="text-primary">${escapeHtml(title)}</h6>
                ${pubDate ? `<p class="small text-muted mb-2"><i class="fas fa-calendar-alt"></i> ${new Date(pubDate).toLocaleString('ja-JP')}</p>` : ''}
                ${link ? `<p class="small mb-2"><i class="fas fa-link"></i> <a href="${escapeHtml(link)}" target="_blank" class="text-truncate d-inline-block" style="max-width: 400px;">${escapeHtml(link)}</a></p>` : ''}
                ${description ? `<div class="small">${escapeHtml(description.substring(0, 200))}${description.length > 200 ? '...' : ''}</div>` : ''}
            </div>
            
            <div class="mt-3 text-muted small">
                <p class="mb-1">URL: ${escapeHtml(url)}</p>
                <p class="mb-0">フォーマット: ${xml.documentElement.tagName === 'rss' ? 'RSS' : 'Atom'}</p>
            </div>
        `;
        
    } catch (error) {
        if (error.message === 'ACCESS_DENIED') {
            content.innerHTML = `
                <div class="alert alert-warning">
                    <h6><i class="fas fa-exclamation-triangle text-warning"></i> アクセスが拒否されました</h6>
                    <p>サーバーがプロキシ経由のアクセスをブロックしています。</p>
                </div>
                
                <div class="mt-3">
                    <p><strong>代替方法:</strong></p>
                    <ol>
                        <li><a href="${escapeHtml(url)}" target="_blank">こちらをクリック</a>して新しいタブでRSSを開く</li>
                        <li>表示されたXML/RSSの内容をコピー</li>
                        <li>下のテキストエリアに貼り付けて「解析」ボタンをクリック</li>
                    </ol>
                    
                    <div class="mt-3">
                        <label class="form-label">RSS/XMLコンテンツを貼り付け:</label>
                        <textarea class="form-control" id="manualRssInput" rows="6" placeholder="<?xml version=&quot;1.0&quot; ..."></textarea>
                        <button class="btn btn-primary mt-2" onclick="parseManualRss()">解析</button>
                    </div>
                </div>
                
                <div class="text-muted small mt-3">
                    <p class="mb-0">元のURL: ${escapeHtml(url)}</p>
                </div>
            `;
        } else {
            content.innerHTML = `
                <div class="alert alert-danger">
                    <h6><i class="fas fa-times-circle text-danger"></i> エラーが発生しました</h6>
                    <p class="mb-0">${escapeHtml(error.message)}</p>
                </div>
                
                <div class="mt-3">
                    <p class="small text-muted">考えられる原因:</p>
                    <ul class="small text-muted">
                        <li>URLが正しくない</li>
                        <li>RSS/Atomフィードではない</li>
                        <li>サーバーがアクセスを拒否している</li>
                        <li>ネットワークエラー</li>
                    </ul>
                </div>
                
                <div class="text-muted small">
                    <p class="mb-0">テストURL: ${escapeHtml(url)}</p>
                </div>
            `;
        }
    }
}

// 手動で貼り付けられたRSSを解析
function parseManualRss() {
    const manualContent = document.getElementById('manualRssInput').value.trim();
    const content = document.getElementById('rssTestContent');
    
    if (!manualContent) {
        alert('RSS/XMLコンテンツを貼り付けてください');
        return;
    }
    
    try {
        const parser = new DOMParser();
        const xml = parser.parseFromString(manualContent, 'text/xml');
        
        // エラーチェック
        const parseError = xml.querySelector('parsererror');
        if (parseError) {
            throw new Error('無効なXMLフォーマット');
        }
        
        // RSS/Atomフィードの解析
        const items = xml.querySelectorAll('item, entry');
        if (items.length === 0) {
            throw new Error('記事が見つかりません');
        }
        
        // 最初の記事を取得
        const firstItem = items[0];
        const title = firstItem.querySelector('title')?.textContent || 'タイトルなし';
        const link = firstItem.querySelector('link')?.textContent || 
                    firstItem.querySelector('link')?.getAttribute('href') || '';
        const description = firstItem.querySelector('description, summary, content')?.textContent || '';
        const pubDate = firstItem.querySelector('pubDate, published, updated')?.textContent || '';
        
        // 結果を表示
        content.innerHTML = `
            <div class="alert alert-success">
                <h6><i class="fas fa-check-circle text-success"></i> RSSフィードの解析に成功しました！（手動入力）</h6>
                <p class="mb-1">記事数: ${items.length}件</p>
            </div>
            
            <h6>最新記事のプレビュー:</h6>
            <div class="rss-article-preview">
                <h6 class="text-primary">${escapeHtml(title)}</h6>
                ${pubDate ? `<p class="small text-muted mb-2"><i class="fas fa-calendar-alt"></i> ${new Date(pubDate).toLocaleString('ja-JP')}</p>` : ''}
                ${link ? `<p class="small mb-2"><i class="fas fa-link"></i> <a href="${escapeHtml(link)}" target="_blank" class="text-truncate d-inline-block" style="max-width: 400px;">${escapeHtml(link)}</a></p>` : ''}
                ${description ? `<div class="small">${escapeHtml(description.substring(0, 200))}${description.length > 200 ? '...' : ''}</div>` : ''}
            </div>
            
            <div class="mt-3 text-muted small">
                <p class="mb-0">フォーマット: ${xml.documentElement.tagName === 'rss' ? 'RSS' : 'Atom'}</p>
                <p class="mb-0 text-success"><i class="fas fa-check-circle"></i> このURLは有効なRSSフィードです</p>
            </div>
        `;
        
    } catch (error) {
        alert('XMLの解析に失敗しました: ' + error.message);
    }
}

// URL形式チェック
function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}

// 編集モードを開く
function openEditMode(sourceId) {
    const source = sources.find(s => s.id === sourceId);
    
    if (!source) {
        console.error('Source not found for id:', sourceId);
        return;
    }
    
    // 現在編集中のソースIDを保存
    currentEditingSourceId = sourceId;
    
    const editContainer = document.getElementById('editModeContainer');
    const editContent = document.getElementById('editModeContent');
    
    // 詳細編集カードを生成
    editContent.innerHTML = createDetailSourceCard(source);
    
    // 編集モードを表示
    editContainer.style.display = 'block';
    
    // スクロールして編集エリアを表示
    editContainer.scrollIntoView({ behavior: 'smooth' });
}

// 編集モードを閉じる
function closeEditMode() {
    const editContainer = document.getElementById('editModeContainer');
    editContainer.style.display = 'none';
    currentEditingSourceId = null;
}

// 情報源を削除
async function deleteSource() {
    if (!currentEditingSourceId) {
        console.error('No source is currently being edited');
        return;
    }
    
    const source = sources.find(s => s.id === currentEditingSourceId);
    if (!source) {
        console.error('Source not found');
        return;
    }
    
    // 削除確認
    const confirmMessage = `「${source.name || source.domain}」を削除してもよろしいですか？\n\nこの情報源は一覧から除外され、自動収集も停止します。`;
    if (!confirm(confirmMessage)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/sources?id=${currentEditingSourceId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || '削除に失敗しました');
        }
        
        // ローカルの配列からも削除
        sources = sources.filter(s => s.id !== currentEditingSourceId);
        
        // 編集モードを閉じる
        closeEditMode();
        
        // 一覧を再表示
        renderSources();
        updateStats();
        
        alert('情報源を削除しました');
        
    } catch (error) {
        console.error('削除エラー:', error);
        alert('削除に失敗しました: ' + error.message);
    }
}

// ====================================================
// 候補管理機能
// ====================================================

// 候補一覧を読み込み
async function loadCandidates() {
    try {
        const response = await fetch('/api/source-candidates', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || '候補の読み込みに失敗しました');
        }
        
        candidates = data.candidates || [];
        
    } catch (error) {
        console.error('候補読み込みエラー:', error);
    }
}

// 表示モードの切り替え
function switchViewMode(mode) {
    currentViewMode = mode;
    
    // ナビゲーションの更新
    document.querySelectorAll('.view-mode-nav').forEach(nav => {
        nav.classList.remove('active');
    });
    const navElement = document.getElementById(`nav-${mode}`);
    if (navElement) {
        navElement.classList.add('active');
    }
    
    // フィルターの表示切り替え
    const sourceFilters = document.getElementById('sourceFilters');
    const candidateFilters = document.getElementById('candidateFilters');
    
    if (!sourceFilters || !candidateFilters) {
        console.error('フィルター要素が見つかりません');
        return;
    }
    
    if (mode === 'sources') {
        // 情報源リストモード
        sourceFilters.classList.add('show');
        candidateFilters.classList.remove('show');
        renderSources();
    } else if (mode === 'candidates') {
        // 探索候補モード
        sourceFilters.classList.remove('show');
        candidateFilters.classList.add('show');
        renderCandidates();
    }
}

// 候補一覧の表示
function renderCandidates() {
    const container = document.getElementById('sourcesContainer');
    const statusFilter = document.getElementById('candidateStatusFilter')?.value || '';
    const languageFilter = document.getElementById('candidateLanguageFilter')?.value || '';
    const sortOrder = document.getElementById('candidateSortOrder')?.value || 'discovered';
    
    // フィルタリング
    let filteredCandidates = candidates;
    if (statusFilter) {
        filteredCandidates = filteredCandidates.filter(c => c.status === statusFilter);
    }
    if (languageFilter) {
        filteredCandidates = filteredCandidates.filter(c => c.language === languageFilter);
    }
    
    // ソート
    filteredCandidates.sort((a, b) => {
        switch (sortOrder) {
            case 'relevance':
                return b.relevance_score - a.relevance_score;
            case 'name':
                return a.name.localeCompare(b.name);
            case 'status':
                return a.status.localeCompare(b.status);
            case 'discovered':
            default:
                return new Date(b.discovered_at) - new Date(a.discovered_at);
        }
    });
    
    if (filteredCandidates.length === 0) {
        container.innerHTML = '<div class="alert alert-info">表示する候補がありません</div>';
        return;
    }
    
    const candidateRows = filteredCandidates.map(candidate => `
        <tr>
            <td>
                <div class="d-flex align-items-center">
                    <span class="badge bg-${getStatusColor(candidate.status)} me-2">${getStatusText(candidate.status)}</span>
                    <strong>${escapeHtml(candidate.name)}</strong>
                </div>
                <div class="small text-muted">
                    <span class="me-3"><i class="fas fa-globe"></i> ${escapeHtml(candidate.domain)}</span>
                    <span class="me-3"><i class="fas fa-language"></i> ${escapeHtml(candidate.language)}</span>
                    <span class="me-3"><i class="fas fa-chart-line"></i> ${(candidate.relevance_score * 100).toFixed(0)}%</span>
                </div>
            </td>
            <td>
                <div class="small">
                    ${candidate.urls.map(url => `<div><i class="fas fa-rss"></i> <a href="${escapeHtml(url)}" target="_blank" class="text-truncate d-inline-block" style="max-width: 200px;">${escapeHtml(url)}</a></div>`).join('')}
                </div>
            </td>
            <td>
                <div class="small text-muted">
                    <div><i class="fas fa-calendar-alt"></i> ${new Date(candidate.discovered_at).toLocaleDateString('ja-JP')}</div>
                    <div><i class="fas fa-search"></i> ${getDiscoveryMethodText(candidate.discovery_method)}</div>
                </div>
            </td>
            <td>
                <div class="btn-group-sm">
                    ${candidate.status === 'pending' ? `
                        <button class="btn btn-success btn-sm me-1" onclick="approveCandidate('${candidate.id}')">
                            <i class="fas fa-check"></i> 承認
                        </button>
                        <button class="btn btn-warning btn-sm me-1" onclick="holdCandidate('${candidate.id}')">
                            <i class="fas fa-pause"></i> 保留
                        </button>
                        <button class="btn btn-outline-danger btn-sm" onclick="rejectCandidate('${candidate.id}')">
                            <i class="fas fa-times"></i> 却下
                        </button>
                    ` : `
                        <button class="btn btn-outline-secondary btn-sm" onclick="viewCandidateDetails('${candidate.id}')">
                            <i class="fas fa-info-circle"></i> 詳細
                        </button>
                    `}
                </div>
            </td>
        </tr>
    `).join('');
    
    container.innerHTML = `
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>候補情報</th>
                        <th>フィード</th>
                        <th>発見情報</th>
                        <th>アクション</th>
                    </tr>
                </thead>
                <tbody>
                    ${candidateRows}
                </tbody>
            </table>
        </div>
    `;
}

// 候補の承認（sources テーブルに追加）
async function approveCandidate(candidateId) {
    try {
        const candidate = candidates.find(c => c.id === candidateId);
        if (!candidate) return;
        
        if (!confirm(`候補「${candidate.name}」を承認して情報源に追加しますか？`)) {
            return;
        }
        
        // 情報源に追加
        const sourceData = {
            name: candidate.name,
            urls: candidate.urls,
            domain: candidate.domain,
            parser: 'rss',
            acquisition_mode: 'auto',
            category: candidate.category === 'unknown' ? 'discovered' : candidate.category,
            country_code: candidate.country_code,
            relevance: Math.min(10, Math.max(1, Math.round(candidate.relevance_score * 10)))
        };
        
        const sourceResponse = await fetch('/api/sources', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(sourceData)
        });
        
        const sourceResult = await sourceResponse.json();
        
        if (!sourceResult.success) {
            throw new Error(sourceResult.error || '情報源の追加に失敗しました');
        }
        
        // 候補のステータスを更新
        const candidateResponse = await fetch(`/api/source-candidates?id=${candidateId}`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                status: 'approved',
                reviewer_notes: '管理画面から承認'
            })
        });
        
        const candidateResult = await candidateResponse.json();
        
        if (!candidateResult.success) {
            throw new Error(candidateResult.error || '候補ステータスの更新に失敗しました');
        }
        
        // 画面を更新
        await loadSources();
        await loadCandidates();
        renderCandidates();
        
        alert('候補を承認し、情報源リストに追加しました');
        
    } catch (error) {
        console.error('候補承認エラー:', error);
        alert('候補の承認に失敗しました: ' + error.message);
    }
}

// 候補の保留
async function holdCandidate(candidateId) {
    try {
        const response = await fetch(`/api/source-candidates?id=${candidateId}`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                status: 'on_hold',
                reviewer_notes: '管理画面から保留'
            })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || '候補の保留に失敗しました');
        }
        
        await loadCandidates();
        renderCandidates();
        
    } catch (error) {
        console.error('候補保留エラー:', error);
        alert('候補の保留に失敗しました: ' + error.message);
    }
}

// 候補の却下
async function rejectCandidate(candidateId) {
    if (!confirm('この候補を却下しますか？')) return;
    
    try {
        const response = await fetch(`/api/source-candidates?id=${candidateId}`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                status: 'rejected',
                reviewer_notes: '管理画面から却下'
            })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || '候補の却下に失敗しました');
        }
        
        await loadCandidates();
        renderCandidates();
        
    } catch (error) {
        console.error('候補却下エラー:', error);
        alert('候補の却下に失敗しました: ' + error.message);
    }
}

// 候補の詳細を表示
function viewCandidateDetails(candidateId) {
    const candidate = candidates.find(c => c.id === candidateId);
    if (!candidate) {
        alert('候補が見つかりません');
        return;
    }
    
    const statusText = getStatusText(candidate.status);
    const discoveryMethodText = getDiscoveryMethodText(candidate.discovery_method);
    const relevancePercent = (candidate.relevance_score * 100).toFixed(1);
    
    const detailsHtml = `
        <div class="candidate-details">
            <h5>${escapeHtml(candidate.name)}</h5>
            
            <div class="row mb-3">
                <div class="col-md-6">
                    <strong>ドメイン:</strong> ${escapeHtml(candidate.domain)}
                </div>
                <div class="col-md-6">
                    <strong>ステータス:</strong> 
                    <span class="badge bg-${getStatusColor(candidate.status)}">${statusText}</span>
                </div>
            </div>
            
            <div class="row mb-3">
                <div class="col-md-6">
                    <strong>言語:</strong> ${escapeHtml(candidate.language)}
                </div>
                <div class="col-md-6">
                    <strong>関連度:</strong> ${relevancePercent}%
                </div>
            </div>
            
            <div class="row mb-3">
                <div class="col-md-6">
                    <strong>発見日:</strong> ${new Date(candidate.discovered_at).toLocaleDateString('ja-JP')}
                </div>
                <div class="col-md-6">
                    <strong>発見方法:</strong> ${discoveryMethodText}
                </div>
            </div>
            
            ${candidate.category ? `
                <div class="mb-3">
                    <strong>カテゴリ:</strong> ${escapeHtml(candidate.category)}
                </div>
            ` : ''}
            
            ${candidate.country_code ? `
                <div class="mb-3">
                    <strong>国コード:</strong> ${escapeHtml(candidate.country_code)}
                </div>
            ` : ''}
            
            <div class="mb-3">
                <strong>フィードURL:</strong>
                <ul class="list-unstyled ms-3">
                    ${candidate.urls.map(url => `
                        <li><i class="fas fa-rss"></i> <a href="${escapeHtml(url)}" target="_blank">${escapeHtml(url)}</a></li>
                    `).join('')}
                </ul>
            </div>
            
            ${candidate.reviewer_notes ? `
                <div class="mb-3">
                    <strong>審査メモ:</strong>
                    <div class="bg-light p-2 rounded">${escapeHtml(candidate.reviewer_notes)}</div>
                </div>
            ` : ''}
            
            ${candidate.status === 'pending' ? `
                <div class="mt-4">
                    <button class="btn btn-success me-2" onclick="approveCandidate('${candidate.id}'); document.getElementById('candidateDetailsModal').style.display='none';">
                        <i class="fas fa-check"></i> 承認
                    </button>
                    <button class="btn btn-warning me-2" onclick="holdCandidate('${candidate.id}'); document.getElementById('candidateDetailsModal').style.display='none';">
                        <i class="fas fa-pause"></i> 保留
                    </button>
                    <button class="btn btn-outline-danger" onclick="rejectCandidate('${candidate.id}'); document.getElementById('candidateDetailsModal').style.display='none';">
                        <i class="fas fa-times"></i> 却下
                    </button>
                </div>
            ` : ''}
        </div>
    `;
    
    // 簡易モーダルで表示
    showModal('候補詳細', detailsHtml);
}

// 簡易モーダル表示関数
function showModal(title, content) {
    // 既存のモーダルがあれば削除
    const existingModal = document.getElementById('candidateDetailsModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // モーダルHTML作成
    const modalHtml = `
        <div id="candidateDetailsModal" class="modal-overlay" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1050; display: flex; align-items: center; justify-content: center;">
            <div class="modal-content" style="background: white; border-radius: 8px; max-width: 800px; max-height: 90vh; overflow-y: auto; margin: 20px;">
                <div class="modal-header" style="padding: 15px 20px; border-bottom: 1px solid #dee2e6; display: flex; justify-content: between; align-items: center;">
                    <h5 style="margin: 0;">${escapeHtml(title)}</h5>
                    <button type="button" style="background: none; border: none; font-size: 24px; cursor: pointer;" onclick="document.getElementById('candidateDetailsModal').remove();">×</button>
                </div>
                <div class="modal-body" style="padding: 20px;">
                    ${content}
                </div>
            </div>
        </div>
    `;
    
    // DOMに追加
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 背景クリックで閉じる
    document.getElementById('candidateDetailsModal').addEventListener('click', function(e) {
        if (e.target === this) {
            this.remove();
        }
    });
}

// ユーティリティ関数
function getStatusColor(status) {
    const colors = {
        pending: 'primary',
        approved: 'success',
        rejected: 'danger',
        on_hold: 'warning'
    };
    return colors[status] || 'secondary';
}

function getStatusText(status) {
    const texts = {
        pending: '未審査',
        approved: '承認済み',
        rejected: '却下済み',
        on_hold: '保留中'
    };
    return texts[status] || status;
}

function getDiscoveryMethodText(method) {
    const texts = {
        weekly_source_discovery: '記事ベース探索',
        weekly_multilingual_discovery: '多言語探索',
        manual: '手動追加'
    };
    return texts[method] || method;
}