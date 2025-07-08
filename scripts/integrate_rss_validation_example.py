#!/usr/bin/env python3
"""
新情報源発見スクリプトにRSS検証を統合する例
discover_*.py スクリプトに追加するコード例
"""

# 既存のimportに追加
from rss_validator import validate_new_source

def process_discovered_source(source_data: dict) -> dict:
    """
    発見された情報源を処理し、RSS検証を実行
    
    既存の discover_*.py の evaluate_source() 関数に追加
    """
    domain = source_data.get('domain')
    urls = source_data.get('urls', [])
    
    print(f"🔍 RSS検証中: {domain}")
    
    # RSS検証を実行
    rss_result = validate_new_source(domain, urls)
    
    # 検証結果を情報源データに統合
    source_data['rss_validation'] = rss_result
    source_data['acquisition_mode'] = rss_result['recommended_mode']
    
    # スコアリングに反映（既存のスコアリングロジックに追加）
    if rss_result['rss_found'] and rss_result['recommended_mode'] == 'auto':
        source_data['quality_score'] += 20  # RSS自動取得可能ボーナス
        source_data['notes'] = 'RSS feed validated and accessible'
    elif rss_result['recommended_mode'] == 'manual':
        source_data['quality_score'] += 10  # 手動チェック価値ありボーナス
        source_data['notes'] = f"Manual check required: {rss_result['reason']}"
    else:
        source_data['notes'] = f"No RSS available: {rss_result['reason']}"
    
    # ログ出力
    print(f"  ✅ Mode: {source_data['acquisition_mode']}")
    print(f"  📝 Note: {source_data['notes']}")
    
    return source_data

# discover_sources_unified.py の create_pull_request() 関数の修正例
def create_pull_request_with_rss_info():
    """
    PR作成時にRSS検証結果を含める
    """
    pr_body = f"""
## 🔍 新情報源の自動発見

### 📊 発見結果サマリー
- 発見数: {len(approved_sources)}個
- RSS自動取得可能: {sum(1 for s in approved_sources if s.get('acquisition_mode') == 'auto')}個
- 手動チェック推奨: {sum(1 for s in approved_sources if s.get('acquisition_mode') == 'manual')}個
- 無効/スキップ: {sum(1 for s in approved_sources if s.get('acquisition_mode') == 'disabled')}個

### 📋 発見された情報源

| 名前 | ドメイン | カテゴリ | スコア | RSS状態 | 取得モード |
|------|---------|----------|--------|---------|------------|
"""
    
    for source in approved_sources:
        rss_status = "✅ 有効" if source.get('rss_validation', {}).get('rss_found') else "❌ なし"
        mode_emoji = {
            'auto': '🤖',
            'manual': '👤', 
            'disabled': '❌'
        }.get(source.get('acquisition_mode', 'disabled'), '❓')
        
        pr_body += f"| {source['name']} | {source['domain']} | {source['category']} | "
        pr_body += f"{source['quality_score']} | {rss_status} | "
        pr_body += f"{mode_emoji} {source.get('acquisition_mode', 'unknown')} |\n"
    
    return pr_body

# 使用例: discover_gpt_categories.py への統合
def enhanced_discover_and_evaluate():
    """
    GPTカテゴリー発見にRSS検証を統合
    """
    discovered_sources = []
    
    for category, config in GPT_CATEGORIES.items():
        print(f"\n🔍 カテゴリー: {category}")
        
        # 既存の発見ロジック
        sources = discover_sources_for_category(category, config)
        
        # RSS検証を追加
        for source in sources:
            # RSS検証を実行
            enhanced_source = process_discovered_source(source)
            discovered_sources.append(enhanced_source)
    
    # 結果をフィルタリング
    # disabled以外を承認候補とする
    approved = [s for s in discovered_sources if s.get('acquisition_mode') != 'disabled']
    
    return approved