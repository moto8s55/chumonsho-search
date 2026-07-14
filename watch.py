# -*- coding: utf-8 -*-
"""
既刊注文書 フォルダ 自動監視スクリプト（追加インストール不要）

対象フォルダを一定間隔で監視し、PDF/HTMLの追加・削除・改名・更新を検知したら
自動で build_index.py を実行して検索ページを再生成（＆設定していれば公開）します。

使い方:
    python watch.py
    （または watch.bat をダブルクリック）

停止: Ctrl+C（またはウィンドウを閉じる）

ポーリング方式なので watchdog 等のライブラリは不要です。
"""

import importlib.util
import os
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent

# build_index.py を読み込む（設定 ROOT / EXTS などを共有する）
spec = importlib.util.spec_from_file_location("build_index", HERE / "build_index.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

# 監視間隔（秒）。短くすると反応が速く、負荷はわずかに増えます。
INTERVAL = 10
# 変更検知後、連続変更が落ち着くまで待つ猶予（秒）
SETTLE = 3


def snapshot():
    """対象ファイルの (パス, サイズ, 更新時刻) の集合を返す。差分検知の指紋。"""
    root = Path(b.ROOT)
    sig = set()
    if not root.exists():
        return None
    for dirpath, dirnames, filenames in os.walk(root):
        for f in filenames:
            if Path(f).suffix.lower() in b.EXTS:
                p = Path(dirpath) / f
                try:
                    st = p.stat()
                    sig.add((str(p), st.st_size, int(st.st_mtime)))
                except OSError:
                    pass
    return frozenset(sig)


def rebuild():
    try:
        n = b.build()
        print(f"[{time.strftime('%H:%M:%S')}] 再生成しました（{n} 件）")
    except SystemExit as e:
        print(f"[{time.strftime('%H:%M:%S')}] 生成失敗: {e}")
    except Exception as e:  # noqa: BLE001
        print(f"[{time.strftime('%H:%M:%S')}] エラー: {e}")


def main():
    print("=== 既刊注文書 自動監視を開始しました ===")
    print(f"対象: {b.ROOT}")
    print(f"監視間隔: {INTERVAL}秒 / 停止するには Ctrl+C")
    prev = snapshot()
    if prev is None:
        print(f"[警告] 対象フォルダが見つかりません: {b.ROOT}")
    else:
        rebuild()  # 起動時に一度生成しておく

    while True:
        try:
            time.sleep(INTERVAL)
            cur = snapshot()
            if cur is None:
                continue
            if cur != prev:
                print(f"[{time.strftime('%H:%M:%S')}] 変更を検知。落ち着くのを待っています…")
                # 連続変更が収まるまで待つ（コピー中などの取りこぼし防止）
                while True:
                    time.sleep(SETTLE)
                    again = snapshot()
                    if again == cur:
                        break
                    cur = again
                rebuild()
                prev = cur
        except KeyboardInterrupt:
            print("\n=== 監視を終了しました ===")
            break


if __name__ == "__main__":
    main()
