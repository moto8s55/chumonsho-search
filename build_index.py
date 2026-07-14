# -*- coding: utf-8 -*-
"""
既刊注文書 検索インデックス生成スクリプト（PC側で実行）

対象フォルダを走査し、各サブフォルダの「最上位のデータ（代表1件）」を抽出して
Notion埋め込み用の検索ページ (index.html) と index.json を生成します。

使い方（Windows / PowerShell 等）:
    python build_index.py

生成物:
    - index.json   … 検索インデックス（デバッグ/再利用用）
    - index.html   … Notionに埋め込む検索ページ（データ埋め込み済み・単体で動く）

このフォルダ(公開リポジトリのクローン)で `git push` すると、GitHub Actions が
自動でGitHub Pagesへ公開します。そのURLをNotionで「/埋め込み」して貼り付けてください。
"""

import json
import os
import unicodedata
from pathlib import Path
from urllib.parse import quote

# ===================== 設定（ここだけ触ればOK） =====================

# 検索対象のルートフォルダ（既刊注文書）
ROOT = r"C:\Users\moto8\OneDrive\デスクトップ\興陽館共有フォルダ★★★2026_02_20\3 営業共有\営業\旧PCデスクトップ\販売促進\16_注文書関連\既刊注文書"

# 生成後に実行する「公開コマンド」（任意）。空なら公開せずローカル生成のみ。
#   このリポジトリ(公開リポジトリのクローン)で自動公開する場合の例:
#     PUBLISH_CMD = 'git add index.html index.json && git commit -m "index更新" && git push'
#   push すると GitHub Actions が Pages へ自動デプロイします。
#   ※ Notionの埋め込みは公開URLを見るので、更新を反映するにはこの公開が必要です。
PUBLISH_CMD = ""

# OneDriveの共有リンクのベースURL。
#   - このフォルダ(既刊注文書)をOneDriveで「リンクをコピー」して得たURLを貼る。
#   - 空のままだと、リンクは付かず（ローカルパスのみ）になります。
# 例（法人/SharePoint系）: "https://<tenant>-my.sharepoint.com/personal/xxx/Documents/.../既刊注文書"
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


def make_link(abspath: str, relpath: str) -> str:
    """OneDrive共有リンク（ベースが設定されていれば）を組み立てる。"""
    if ONEDRIVE_BASE_URL:
        base = ONEDRIVE_BASE_URL.rstrip("/")
        rel = "/".join(quote(part) for part in Path(relpath).parts)
        return f"{base}/{rel}"
    # フォールバック: ローカルパス（同一PCで開く用）
    return "file:///" + abspath.replace("\\", "/")


def build():
    root = Path(ROOT)
    if not root.exists():
        raise SystemExit(f"[エラー] ルートフォルダが見つかりません: {ROOT}")

    entries = []
    seen_folders = set()

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

        # 曖昧検索用の索引には「ファイル名」+「フォルダ名」を入れてヒット率を上げる
        haystack = norm(title) + "\n" + norm(folder_name)

        entries.append(
            {
                "title": title,
                "folder": folder_name,
                "ext": rep.suffix.lower().lstrip("."),
                "relpath": str(rel).replace("\\", "/"),
                "url": make_link(str(rep), str(rel)),
                "key": haystack,
            }
        )
        seen_folders.add(str(d))

    entries.sort(key=lambda e: e["folder"])

    # index.json
    out_dir = Path(__file__).resolve().parent
    (out_dir / "index.json").write_text(
        json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 検索HTML（データ埋め込み）。テンプレは `const DATA = [/*__DATA__*/];` の形なので
    # 外側の [] を除いた中身だけを差し込む（entries が空でも const DATA = []; になる）。
    inner = json.dumps(entries, ensure_ascii=False)[1:-1]
    html = HTML_TEMPLATE.replace("/*__DATA__*/", inner)
    (out_dir / "index.html").write_text(html, encoding="utf-8")

    print(f"[完了] {len(entries)} 件のフォルダを索引化しました。")
    print(f"  - {out_dir / 'index.json'}")
    print(f"  - {out_dir / 'index.html'}")
    if not ONEDRIVE_BASE_URL:
        print("[注意] ONEDRIVE_BASE_URL が未設定です。リンクはローカルパス(file://)になります。")
        print("       Notion埋め込みからファイルを開くには OneDrive共有URL を設定してください。")

    # 公開コマンド（設定されていれば実行）
    if PUBLISH_CMD:
        import subprocess
        print(f"[公開] {PUBLISH_CMD}")
        rc = subprocess.call(PUBLISH_CMD, shell=True, cwd=str(out_dir))
        print("[公開] 完了" if rc == 0 else f"[公開] 失敗 (exit={rc})")

    return len(entries)


# HTML本体は別ファイル template.html を読み込んで使う
HTML_TEMPLATE = (Path(__file__).resolve().parent / "template.html").read_text(
    encoding="utf-8"
) if (Path(__file__).resolve().parent / "template.html").exists() else "/*__DATA__*/"


if __name__ == "__main__":
    build()
