# -*- coding: utf-8 -*-
"""
既刊注文書 検索インデックス生成スクリプト（PC側で実行）

対象フォルダを走査し、各サブフォルダの「最上位のデータ（代表1件）」を抽出して
Notion埋め込み用の検索ページ (index.html) と index.json を生成します。
さらに、代表ファイルをこのリポジトリの files/ にコピーして、GitHub Pages から
クリックで開けるようにします（ISBN画像と同じ方式）。

使い方（Windows / PowerShell 等）:
    python build_index.py

生成物:
    - index.json   … 検索インデックス（デバッグ用）
    - index.html   … Notionに埋め込む検索ページ（データ埋め込み済み）
    - files/…      … 代表ファイル（PDF/HTML）のコピー（公開）

PUBLISH_CMD を設定しておけば、生成後に自動で git push まで実行します。
"""

import json
import os
import shutil
import unicodedata
from pathlib import Path
from urllib.parse import quote

# ===================== 設定（ここだけ触ればOK） =====================

# 検索対象のルートフォルダ（既刊注文書）
ROOT = r"C:\Users\moto8\OneDrive\デスクトップ\興陽館共有フォルダ★★★2026_02_20\3 営業共有\営業\旧PCデスクトップ\販売促進\16_注文書関連\既刊注文書"

# 生成後に実行する「公開コマンド」。空なら公開せずローカル生成のみ。
#   既定で「全部addしてcommit→push」までを自動実行します（＝Notionに自動反映）。
PUBLISH_CMD = 'git add -A && git commit -m "既刊注文書 更新" && git push'

# クリックでファイルを開けるようにする方式:
#   True  … 代表ファイルをこのリポジトリの files/ にコピーし、GitHub Pages から開けるURLにする
#           （ISBN画像と同じ方式。公開されます）
#   False … コピーしない（OneDrive URL または file:// になる）
COPY_FILES_INTO_REPO = True
FILES_SUBDIR = "files"

# OneDriveの共有リンクのベースURL（COPY_FILES_INTO_REPO=False のとき使用）。
ONEDRIVE_BASE_URL = ""

# 検索対象にする拡張子
EXTS = [".pdf", ".html", ".htm"]

# 代表ファイルの優先順位（先に来る拡張子を優先）。ここでは PDF > HTML。
PRIORITY = {".pdf": 0, ".html": 1, ".htm": 1}

# ===================================================================


def norm(s: str) -> str:
    """全角半角・大小・カタカナ等を吸収した正規化キー（曖昧検索用）。"""
    s = unicodedata.normalize("NFKC", s).lower()
    # カタカナ -> ひらがな
    out = []
    for ch in s:
        code = ord(ch)
        if 0x30A1 <= code <= 0x30F6:
            out.append(chr(code - 0x60))
        else:
            out.append(ch)
    s = "".join(out)
    # 空白・記号の一部を除去
    for c in [" ", "　", "\t", "_", "-", "・", "／", "/", "\\"]:
        s = s.replace(c, "")
    return s


def pick_representative(files):
    """フォルダ内の複数ファイルから代表1件を選ぶ（PDF優先 → 名前順）。"""
    files = sorted(
        files,
        key=lambda p: (PRIORITY.get(p.suffix.lower(), 9), p.name.lower()),
    )
    return files[0] if files else None


def make_link(relpath: str, abspath: str) -> str:
    """ヒット項目を開くためのURL/リンクを組み立てる。"""
    rel_url = "/".join(quote(part) for part in Path(relpath).parts)
    if COPY_FILES_INTO_REPO:
        # GitHub Pages 上の files/ に置いたコピーを開く（相対URL）
        return f"{FILES_SUBDIR}/{rel_url}"
    if ONEDRIVE_BASE_URL:
        return f"{ONEDRIVE_BASE_URL.rstrip('/')}/{rel_url}"
    # フォールバック: ローカルパス（同一PCで開く用）
    return "file:///" + abspath.replace("\\", "/")


def build():
    root = Path(ROOT)
    if not root.exists():
        raise SystemExit(f"[エラー] ルートフォルダが見つかりません: {ROOT}")

    out_dir = Path(__file__).resolve().parent
    files_dir = out_dir / FILES_SUBDIR

    # files/ を毎回作り直して、削除・改名されたファイルを残さない
    if COPY_FILES_INTO_REPO and files_dir.exists():
        shutil.rmtree(files_dir)

    entries = []
    copied = 0

    # ルート直下から順に walk。各フォルダで直下の対象ファイルから代表を1件選ぶ。
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        d = Path(dirpath)
        target_files = [d / f for f in filenames if Path(f).suffix.lower() in EXTS]
        if not target_files:
            continue
        rep = pick_representative(target_files)
        if rep is None:
            continue

        rel = rep.relative_to(root)
        folder_name = d.name if d != root else "(ルート)"
        title = rep.stem  # ファイル名（拡張子なし）＝タイトル

        # 代表ファイルを files/ にコピー（公開用）
        if COPY_FILES_INTO_REPO:
            dst = files_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(rep, dst)
                copied += 1
            except OSError as e:
                print(f"[警告] コピー失敗: {rep} ({e})")

        # 曖昧検索用の索引には「ファイル名」+「フォルダ名」を入れてヒット率を上げる
        haystack = norm(title) + "\n" + norm(folder_name)

        entries.append(
            {
                "title": title,
                "folder": folder_name,
                "ext": rep.suffix.lower().lstrip("."),
                "relpath": str(rel).replace("\\", "/"),
                "url": make_link(str(rel), str(rep)),
                "key": haystack,
            }
        )

    entries.sort(key=lambda e: e["folder"])

    # index.json
    (out_dir / "index.json").write_text(
        json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 検索HTML（データ埋め込み）。テンプレは `const DATA = [/*__DATA__*/];` の形なので
    # 外側の [] を除いた中身だけを差し込む（entries が空でも const DATA = []; になる）。
    inner = json.dumps(entries, ensure_ascii=False)[1:-1]
    html = HTML_TEMPLATE.replace("/*__DATA__*/", inner)
    (out_dir / "index.html").write_text(html, encoding="utf-8")

    print(f"[完了] {len(entries)} 件のフォルダを索引化しました。")
    if COPY_FILES_INTO_REPO:
        print(f"       {copied} 件のファイルを {FILES_SUBDIR}/ にコピーしました（公開）。")
    print(f"  - {out_dir / 'index.json'}")
    print(f"  - {out_dir / 'index.html'}")

    # 公開コマンド（設定されていれば実行）
    if PUBLISH_CMD:
        import subprocess
        print(f"[公開] {PUBLISH_CMD}")
        rc = subprocess.call(PUBLISH_CMD, shell=True, cwd=str(out_dir))
        print("[公開] 完了（数十秒でNotionに反映されます）" if rc == 0
              else f"[公開] 変更なし、または失敗 (exit={rc})")

    return len(entries)


# HTML本体は別ファイル template.html を読み込んで使う
HTML_TEMPLATE = (Path(__file__).resolve().parent / "template.html").read_text(
    encoding="utf-8"
) if (Path(__file__).resolve().parent / "template.html").exists() else "/*__DATA__*/"


if __name__ == "__main__":
    build()
