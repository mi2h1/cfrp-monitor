#!/usr/bin/env python3
"""
raw フォルダの古いデータを自動削除するスクリプト
デフォルトで30日以上前のデータを削除
"""
import os
import shutil
import argparse
from datetime import datetime, timedelta
from pathlib import Path

def cleanup_old_raw_data(base_dir: Path, days_to_keep: int = 30, dry_run: bool = False):
    """
    指定された日数より古いrawデータフォルダを削除
    
    Args:
        base_dir: rawフォルダのベースディレクトリ
        days_to_keep: 保持する日数（デフォルト30日）
        dry_run: True の場合、実際には削除せずに対象を表示するのみ
    """
    if not base_dir.exists():
        print(f"エラー: {base_dir} が存在しません")
        return
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    deleted_count = 0
    total_size = 0
    
    print(f"{'[DRY RUN] ' if dry_run else ''}削除対象: {cutoff_date.date()} より前のデータ")
    print("-" * 50)
    
    # 日付形式のディレクトリをスキャン
    for item in base_dir.iterdir():
        if not item.is_dir():
            continue
            
        # YYYY-MM-DD 形式のディレクトリ名をパース
        try:
            dir_date = datetime.strptime(item.name, "%Y-%m-%d")
        except ValueError:
            # 日付形式でないディレクトリはスキップ
            continue
        
        # カットオフ日より古い場合
        if dir_date < cutoff_date:
            # ディレクトリサイズを計算
            dir_size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
            total_size += dir_size
            
            print(f"{'削除予定' if dry_run else '削除中'}: {item.name} "
                  f"({dir_size / 1024 / 1024:.1f} MB)")
            
            if not dry_run:
                shutil.rmtree(item)
            
            deleted_count += 1
    
    print("-" * 50)
    print(f"{'削除予定' if dry_run else '削除完了'}: {deleted_count} フォルダ, "
          f"合計 {total_size / 1024 / 1024:.1f} MB")

def main():
    parser = argparse.ArgumentParser(
        description="raw フォルダの古いデータを削除します"
    )
    parser.add_argument(
        "--days", "-d", 
        type=int, 
        default=30,
        help="保持する日数 (デフォルト: 30)"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="実際には削除せず、削除対象を表示するのみ"
    )
    parser.add_argument(
        "--path", "-p",
        type=str,
        default="raw",
        help="raw フォルダのパス (デフォルト: ./raw)"
    )
    
    args = parser.parse_args()
    
    # スクリプトの場所から相対パスを解決
    script_dir = Path(__file__).parent
    raw_dir = (script_dir.parent / args.path).resolve()
    
    cleanup_old_raw_data(raw_dir, args.days, args.dry_run)

if __name__ == "__main__":
    main()