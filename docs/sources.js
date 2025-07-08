// CFRP Monitor - 情報源管理ページJavaScript

let sources = [];
let categories = [];
let countries = [];

// 初期化
document.addEventListener('DOMContentLoaded', async () => {
    await loadSources();
    setupEventListeners();
});

// 情報源一覧を読み込み
async function loadSources() {
    try {
        const { data, error } = await supabase
            .from('sources')
            .select('*')
            .order('name');
        
        if (error) throw error;
        
        sources = data || [];
        
        // カテゴリとの国のユニークリストを作成
        categories = [...new Set(sources.map(s => s.category).filter(Boolean))];
        countries = [...new Set(sources.map(s => s.country_code).filter(Boolean))];
        
        populateFilters();
        renderSources();
        updateStats();
        
        document.getElementById('loading').style.display = 'none';
        document.getElementById('sourcesContainer').style.display = 'block';
        document.getElementById('statsContainer').style.display = 'block';
    } catch (error) {
        console.error('情報源読み込みエラー:', error);
        document.getElementById('loading').innerHTML = 
            '<div class="alert alert-danger">情報源の読み込みに失敗しました</div>';
    }
}

// フィルター選択肢を設定
function populateFilters() {
    // カテゴリフィルター
    const categorySelect = document.getElementById('categoryFilter');
    categories.forEach(category => {
        const option = document.createElement('option');
        option.value = category;
        option.textContent = category;
        categorySelect.appendChild(option);
    });
    
    // 国フィルター
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
    const filtered = filterAndSortSources();
    
    if (filtered.length === 0) {
        container.innerHTML = '<div class="alert alert-info">該当する情報源がありません</div>';
        return;
    }
    
    container.innerHTML = filtered.map(source => createCompactSourceCard(source)).join('');
    updateStats();
}

// フィルタリングとソート
function filterAndSortSources() {
    const modeFilter = document.getElementById('modeFilter').value;
    const deletedFilter = document.getElementById('deletedFilter').value;
    const categoryFilter = document.getElementById('categoryFilter').value;
    const countryFilter = document.getElementById('countryFilter').value;
    const sortOrder = document.getElementById('sortOrder').value;

    // フィルタリング
    let filtered = sources.filter(source => {
        // 削除フィルター
        if (deletedFilter === 'active' && source.deleted) return false;
        if (deletedFilter === 'deleted' && !source.deleted) return false;
        
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
                    <div class="compact-meta">
                        <span class="badge bg-${getModeColor(source.acquisition_mode)}">${getModeLabel(source.acquisition_mode)}</span>
                        <small>🌐 ${source.domain}</small>
                        <small>📊 ${source.relevance || 0}</small>
                        ${source.category ? `<small>📂 ${source.category}</small>` : ''}
                        ${source.country_code ? `<small>🌍 ${source.country_code}</small>` : ''}
                    </div>
                    ${source.description ? `
                        <small class="text-muted d-block mt-1">
                            ${escapeHtml(source.description.substring(0, 100))}${source.description.length > 100 ? '...' : ''}
                        </small>
                    ` : ''}
                </div>
                <div class="text-end">
                    <button class="btn btn-outline-primary btn-sm edit-source-btn" data-id="${source.id}">編集</button>
                </div>
            </div>
        </div>
    `;
}

// 詳細編集用の情報源カードを作成（省略 - 必要に応じて追加）
function createDetailSourceCard(source) {
    // 長いので省略 - 実際のsources.htmlから抜粋して追加
    return `<div>詳細編集カード（実装省略）</div>`;
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

// イベントリスナーを設定
function setupEventListeners() {
    // フィルター・ソート変更時
    setupFilterListeners(['modeFilter', 'deletedFilter', 'categoryFilter', 'countryFilter', 'sortOrder'], renderSources);

    // 更新ボタン
    setupRefreshButton(loadSources);

    // コンパクトカードクリックのイベント委譲
    document.getElementById('sourcesContainer').addEventListener('click', (e) => {
        const card = e.target.closest('.compact-card');
        if (card) {
            const sourceId = card.dataset.id;
            openEditMode(sourceId);
        }
    });
}

// 編集モードを開く（簡略版）
function openEditMode(sourceId) {
    console.log('編集モード開く:', sourceId);
    // 実装省略 - 必要に応じて追加
}

// その他の関数も必要に応じて追加...