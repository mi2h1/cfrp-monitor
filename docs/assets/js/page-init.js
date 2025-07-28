// CFRP Monitor - ページ初期化スクリプト

// 記事管理ページの初期化
function initializeArticlesPage() {
    document.addEventListener('DOMContentLoaded', async function() {
        try {
            await initializeNavigation('articles');
            // userFeaturesが設定された後でarticles.jsの初期化を実行
            if (typeof initializeArticlesApp === 'function') {
                await initializeArticlesApp();
            }
        } catch (error) {
            console.error('Navigation initialization failed:', error);
        }
    });
}

// 情報源管理ページの初期化
function initializeSourcesPage() {
    document.addEventListener('DOMContentLoaded', async function() {
        const layout = await initializeNavigation('sources');
        if (!layout) return;
        if (!checkPagePermission('can_manage_sources')) return;
    });
}

// ユーザー管理ページの初期化
function initializeUsersPage() {
    document.addEventListener('DOMContentLoaded', async function() {
        const layout = await initializeNavigation('users');
        if (!layout) return;
        if (!checkPagePermission('can_manage_users')) return;
    });
}