// Supabase設定ファイル
// 実際の値に置き換えてください

const SUPABASE_CONFIG = {
    url: 'YOUR_SUPABASE_URL',
    anonKey: 'YOUR_SUPABASE_ANON_KEY'
};

// 使用方法:
// 1. Supabase プロジェクト設定から URL と anon key をコピー
// 2. 上記の値を実際の値に置き換え
// 3. index.html でこのファイルを読み込み

// セキュリティ注意事項:
// - anon key は公開されても安全ですが、適切な RLS 設定が必要です
// - 本番環境では適切なドメイン制限を設定してください