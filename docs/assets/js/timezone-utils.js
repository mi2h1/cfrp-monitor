// CFRP Monitor - 日本時間（JST）統一処理ユーティリティ（JavaScript版）
// 全フロントエンドでの日時処理を日本時間に統一するための共通関数

/**
 * 現在の日本時間を取得
 * @returns {Date} JST の Date オブジェクト
 */
function nowJST() {
    return new Date(new Date().toLocaleString("en-US", {timeZone: "Asia/Tokyo"}));
}

/**
 * 現在の日本時間をISO形式で取得
 * @returns {string} ISO形式の日時文字列
 */
function nowJSTISO() {
    return nowJST().toISOString();
}

/**
 * 今日の日付を日本時間で取得
 * @returns {string} YYYY-MM-DD形式の日付文字列
 */
function todayJST() {
    const jst = nowJST();
    return jst.getFullYear() + '-' + 
           String(jst.getMonth() + 1).padStart(2, '0') + '-' + 
           String(jst.getDate()).padStart(2, '0');
}

/**
 * 日時文字列をJST表示用（yyyy/mm/dd hh:mm）にフォーマット
 * @param {string} dateString - ISO形式またはその他の日時文字列
 * @returns {string|null} 表示用の日時文字列またはnull
 */
function formatJSTDisplay(dateString) {
    try {
        if (!dateString) return null;
        
        // Date オブジェクトに変換
        let date = new Date(dateString);
        
        // 無効な日付の場合はnullを返す
        if (isNaN(date.getTime())) return null;
        
        // 日本時間に変換
        const jstDate = new Date(date.toLocaleString("en-US", {timeZone: "Asia/Tokyo"}));
        
        // yyyy/mm/dd hh:mm形式でフォーマット
        const year = jstDate.getFullYear();
        const month = String(jstDate.getMonth() + 1).padStart(2, '0');
        const day = String(jstDate.getDate()).padStart(2, '0');
        const hours = String(jstDate.getHours()).padStart(2, '0');
        const minutes = String(jstDate.getMinutes()).padStart(2, '0');
        
        return `${year}/${month}/${day} ${hours}:${minutes}`;
    } catch (error) {
        console.error('Date formatting error:', error);
        return null;
    }
}

/**
 * 日時文字列をJST日付のみ（yyyy/mm/dd）にフォーマット
 * @param {string} dateString - ISO形式またはその他の日時文字列
 * @returns {string|null} 表示用の日付文字列またはnull
 */
function formatJSTDate(dateString) {
    try {
        if (!dateString) return null;
        
        let date = new Date(dateString);
        if (isNaN(date.getTime())) return null;
        
        const jstDate = new Date(date.toLocaleString("en-US", {timeZone: "Asia/Tokyo"}));
        
        const year = jstDate.getFullYear();
        const month = String(jstDate.getMonth() + 1).padStart(2, '0');
        const day = String(jstDate.getDate()).padStart(2, '0');
        
        return `${year}/${month}/${day}`;
    } catch (error) {
        console.error('Date formatting error:', error);
        return null;
    }
}

/**
 * 相対時間表示（「〇時間前」など）
 * @param {string} dateString - ISO形式またはその他の日時文字列
 * @returns {string|null} 相対時間文字列またはnull
 */
function formatJSTRelative(dateString) {
    try {
        if (!dateString) return null;
        
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return null;
        
        const now = nowJST();
        const diffMs = now - date;
        const diffMinutes = Math.floor(diffMs / (1000 * 60));
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        
        if (diffMinutes < 1) return 'たった今';
        if (diffMinutes < 60) return `${diffMinutes}分前`;
        if (diffHours < 24) return `${diffHours}時間前`;
        if (diffDays < 7) return `${diffDays}日前`;
        
        // 1週間以上前は通常の日付表示
        return formatJSTDate(dateString);
    } catch (error) {
        console.error('Relative date formatting error:', error);
        return null;
    }
}

/**
 * HTML要素内の日時を自動でJST表示に変換
 * data-datetime属性を持つ要素を自動変換
 */
function convertDateTimesToJST() {
    const elements = document.querySelectorAll('[data-datetime]');
    elements.forEach(element => {
        const dateString = element.getAttribute('data-datetime');
        const format = element.getAttribute('data-format') || 'full'; // full, date, relative
        
        let formattedDate;
        switch (format) {
            case 'date':
                formattedDate = formatJSTDate(dateString);
                break;
            case 'relative':
                formattedDate = formatJSTRelative(dateString);
                break;
            default:
                formattedDate = formatJSTDisplay(dateString);
        }
        
        if (formattedDate) {
            element.textContent = formattedDate;
        }
    });
}

// DOM読み込み完了時に自動変換を実行
document.addEventListener('DOMContentLoaded', convertDateTimesToJST);