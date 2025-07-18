#!/usr/bin/env python3
"""
日本時間（JST）統一処理ユーティリティ
全システムでの日時処理を日本時間に統一するための共通関数
"""

import datetime
import pytz

# 日本時間タイムゾーン
JST = pytz.timezone('Asia/Tokyo')

def now_jst():
    """現在の日本時間を取得"""
    return datetime.datetime.now(JST)

def now_jst_iso():
    """現在の日本時間をISO形式で取得（タイムゾーン情報付き）"""
    return now_jst().isoformat()

def now_jst_naive():
    """現在の日本時間をnaive datetimeで取得（タイムゾーン情報なし）"""
    return now_jst().replace(tzinfo=None)

def now_jst_naive_iso():
    """現在の日本時間をnaive ISO形式で取得（DB書き込み用）"""
    return now_jst_naive().isoformat()

def today_jst():
    """今日の日付を日本時間で取得"""
    return now_jst().date()

def today_jst_iso():
    """今日の日付を日本時間でISO形式で取得"""
    return today_jst().isoformat()

def parse_to_jst(date_string):
    """日付文字列を解析して日本時間に変換"""
    try:
        if not date_string:
            return None
        
        # ISO形式の日付をパース
        if 'T' in date_string:
            # datetimeの場合
            if date_string.endswith('Z'):
                # UTC時間として解析
                dt = datetime.datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            elif '+' in date_string or '-' in date_string[-6:]:
                # タイムゾーン情報付き
                dt = datetime.datetime.fromisoformat(date_string)
            else:
                # naive datetime（DBから取得した場合はJSTと仮定）
                dt = datetime.datetime.fromisoformat(date_string)
                dt = JST.localize(dt)
        else:
            # 日付のみの場合
            return datetime.datetime.fromisoformat(date_string).date()
        
        # JSTに変換
        if dt.tzinfo is None:
            # naive datetimeの場合はJSTとして扱う
            return JST.localize(dt)
        else:
            # タイムゾーン付きの場合はJSTに変換
            return dt.astimezone(JST)
    
    except Exception as e:
        print(f"Date parsing error: {e}")
        return None

def format_jst_display(dt_string):
    """日時文字列をJST表示用（yyyy/mm/dd hh:mm）にフォーマット"""
    try:
        if not dt_string:
            return None
        
        jst_dt = parse_to_jst(dt_string)
        if jst_dt:
            return jst_dt.strftime('%Y/%m/%d %H:%M')
        return None
    
    except Exception as e:
        print(f"Date formatting error: {e}")
        return None

def safe_date_parse(txt):
    """安全な日付パース（旧関数の置き換え用）"""
    try:
        if not txt:
            return None
        
        # dateutil.parserを使用してパース
        from dateutil import parser as dtparser
        parsed_date = dtparser.parse(txt)
        
        # タイムゾーンが設定されていない場合はUTCと仮定
        if parsed_date.tzinfo is None:
            parsed_date = pytz.utc.localize(parsed_date)
        
        # 日本時間に変換
        japan_time = parsed_date.astimezone(JST)
        
        return japan_time.date().isoformat()
    except Exception:
        return None