// CFRP Monitor - インデックス（リダイレクト）ページJavaScript

// 認証状態をチェックしてリダイレクト
(function() {
    const authToken = localStorage.getItem('auth_token');
    
    if (authToken) {
        // 認証済みの場合は記事管理ページへ
        window.location.replace('/articles');
    } else {
        // 未認証の場合はログインページへ
        window.location.replace('/login');
    }
})();