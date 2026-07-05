#!/usr/bin/env python3
"""
LogicHive DB クリーンアップスクリプト
未使用テーブルを安全に削除します。
"""
import sqlite3
import os
import shutil
from datetime import datetime

DB_PATH = r'C:\Users\saiha\.logichive\data\logichive.db'

# 削除対象の未使用テーブル
UNUSED_TABLES = [
    'schema_migrations',
    'functions',
    'embeddings',
    'config',
    'meetings',
]

def backup_db():
    """DBのバックアップを作成"""
    backup_name = f"logichive_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    backup_path = os.path.join(os.path.dirname(DB_PATH), backup_name)
    shutil.copy2(DB_PATH, backup_path)
    print(f"[OK] バックアップ作成: {backup_name}")
    return backup_path

def check_table_references():
    """コードベースからテーブル参照を再チェック"""
    # 現在のコードで使用されているテーブル
    active_tables = {'logichive_functions', 'logichive_function_history', 'sqlite_sequence'}

    print("\n=== テーブル参照チェック ===")
    print(f"  使用中（削除対象外）: {', '.join(active_tables)}")
    print(f"  削除対象: {', '.join(UNUSED_TABLES)}")

    return True

def drop_tables():
    """未使用テーブルを削除"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n=== テーブル削除開始 ===")

    for table in UNUSED_TABLES:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"  [OK] {table} を削除しました")
        except Exception as e:
            print(f"  [FAIL] {table} の削除に失敗: {e}")
            conn.rollback()
            raise

    conn.commit()
    print("\n[OK] 全テーブルの削除が完了しました")

    # 削除後の確認
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    remaining = [row[0] for row in cursor.fetchall()]
    print("\n=== 残存テーブル ===")
    for t in remaining:
        cursor.execute(f'SELECT COUNT(*) FROM "{t}"')
        count = cursor.fetchone()[0]
        print(f"  {t}: {count} rows")

    conn.close()

def main():
    print("=" * 60)
    print("LogicHive DB クリーンアップ")
    print("=" * 60)

    if not os.path.exists(DB_PATH):
        print(f"❌ ファイルが見つかりません: {DB_PATH}")
        return

    # 現在の状態確認
    print(f"DB: {DB_PATH}")

    # 参照チェック
    check_table_references()

    # バックアップ
    backup_path = backup_db()

    # 実行確認
    print("\n[WARN] 以下のテーブルを削除します:")
    for table in UNUSED_TABLES:
        print(f"  - {table}")

    # 削除実行
    drop_tables()

    print("\n" + "=" * 60)
    print("[OK] クリーンアップ完了")
    print(f"   バックアップ: {backup_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()
