// CFRP Monitor - セキュリティ制限JavaScript

// 本番環境でのセキュリティ制限
function enableProductionSecurity() {
    // 本番環境かどうかを判定
    const isProduction = location.hostname !== 'localhost' && 
                        location.hostname !== '127.0.0.1' && 
                        !location.hostname.includes('127.0.0.1');
    
    if (!isProduction) {
        console.log('開発環境のため、セキュリティ制限は無効です');
        return;
    }
    
    console.log('本番環境用セキュリティ制限を有効化しました');
    
    // 開発者ツール検知
    let devToolsOpen = false;
    
    function detectDevTools() {
        const threshold = 160;
        if (window.outerHeight - window.innerHeight > threshold || 
            window.outerWidth - window.innerWidth > threshold) {
            if (!devToolsOpen) {
                devToolsOpen = true;
                handleDevToolsOpen();
            }
        } else {
            devToolsOpen = false;
        }
    }
    
    function handleDevToolsOpen() {
        document.body.innerHTML = `
            <div style="display: flex; justify-content: center; align-items: center; height: 100vh; background: #f8f9fa;">
                <div style="text-align: center; padding: 2rem; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h1 style="color: #dc3545; margin-bottom: 1rem;">⚠️ セキュリティ警告</h1>
                    <p style="color: #6c757d; font-size: 1.1rem;">開発者ツールの使用は許可されていません。</p>
                    <p style="color: #6c757d;">ページを再読み込みしてください。</p>
                    <button onclick="location.reload()" style="background: #007bff; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer;">
                        ページを再読み込み
                    </button>
                </div>
            </div>
        `;
    }
    
    // 定期的にチェック
    setInterval(detectDevTools, 1000);
    
    // 開発者ツール関連のキーボードショートカットのみ無効化
    document.addEventListener('keydown', e => {
        // F12
        if (e.key === 'F12') {
            e.preventDefault();
            return false;
        }
        
        // Ctrl+Shift+I (開発者ツール)
        if (e.ctrlKey && e.shiftKey && e.key === 'I') {
            e.preventDefault();
            return false;
        }
        
        // Ctrl+Shift+C (要素選択)
        if (e.ctrlKey && e.shiftKey && e.key === 'C') {
            e.preventDefault();
            return false;
        }
        
        // Ctrl+Shift+J (コンソール)
        if (e.ctrlKey && e.shiftKey && e.key === 'J') {
            e.preventDefault();
            return false;
        }
        
        // Ctrl+U (ソース表示)
        if (e.ctrlKey && e.key === 'u') {
            e.preventDefault();
            return false;
        }
    });
    
    // コンソール警告
    console.log('%c⚠️ セキュリティ警告', 'font-size: 20px; color: red; font-weight: bold;');
    console.log('%c開発者ツールの使用は監視されています。', 'font-size: 16px; color: red;');
    console.log('%c不正なアクセスは記録され、報告されます。', 'font-size: 16px; color: red;');
}

// ページ読み込み時に実行
document.addEventListener('DOMContentLoaded', enableProductionSecurity);

// デバッグ情報の無効化
if (typeof console !== 'undefined') {
    const isProduction = location.hostname !== 'localhost' && 
                        location.hostname !== '127.0.0.1' && 
                        !location.hostname.includes('127.0.0.1');
    
    if (isProduction) {
        console.log = function() {};
        console.warn = function() {};
        console.error = function() {};
        console.info = function() {};
        console.debug = function() {};
    }
}