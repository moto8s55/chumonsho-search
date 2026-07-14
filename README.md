# 既刊注文書 検索（Notion埋め込み用・公開ページ）

`既刊注文書` フォルダ内のPDF/HTMLを **タイトル（ファイル名）で曖昧検索** し、
ヒットしたファイルを **OneDriveリンク** で開ける検索ページです。
このリポジトリは **GitHub Pages で自動公開**され、そのURLをNotionに埋め込んで使います。

- 各サブフォルダに複数ファイルがある場合は **代表1件（PDF優先）** を検索対象にします。
- 全角半角・カタカナ/ひらがな・スペースの違いを無視してヒットします（曖昧検索）。

> 公開直後はサンプルデータが表示されます。下記手順で自分のPCから実データを反映してください。

---

## 公開URL

`main` に push すると GitHub Actions が自動で Pages に公開します（設定画面の操作は不要）。
公開URL:

    https://moto8s55.github.io/chumonsho-search/

このURLをNotionの `/embed`（埋め込み）に貼り付けます。

---

## 実データを反映する手順（初回セットアップ）

### 1. このリポジトリをPCにクローン
```bash
git clone https://github.com/moto8s55/chumonsho-search.git
cd chumonsho-search
```

### 2. OneDrive共有URLを用意
エクスプローラーで `既刊注文書` フォルダを右クリック →「OneDrive」→「リンクをコピー」。

### 3. `build_index.py` を編集
```python
ROOT = r"C:\Users\moto8\OneDrive\...\既刊注文書"   # 対象フォルダ（既定で設定済み）
ONEDRIVE_BASE_URL = "（手順2でコピーしたフォルダURL）"
PUBLISH_CMD = 'git add index.html index.json && git commit -m "index更新" && git push'
```

### 4. 実行
```bash
python build_index.py
```
`index.html` が実データで再生成され、`PUBLISH_CMD` により自動で push →
GitHub Actions が Pages を更新 → Notionに反映されます。

### 5. Notionに埋め込む（初回のみ）
1. Notionで `/embed`（`/埋め込み`）と入力
2. 上の公開URLを貼り付け →「リンクを埋め込む」
3. 枠をドラッグして高さ調整

---

## 自動更新（フォルダを変えたら自動反映）

`watch.py` が `既刊注文書` フォルダを監視し、変更を検知したら自動で再生成＋push します
（追加インストール不要のポーリング方式）。`PUBLISH_CMD` を設定しておけば、
**フォルダ変更 → 自動再生成 → 自動push → Pages更新 → Notion反映** まで全自動です。

- `install_task.ps1` … ログオン時に自動監視を起動するタスクを登録（右クリック→PowerShellで実行）
- `watch.bat` … 監視をワンクリックで開始
- `update.bat` … 今すぐ1回だけ更新

---

## ファイル構成

| ファイル | 役割 |
|---|---|
| `build_index.py` | フォルダ走査＋検索ページ生成（＋任意で公開push） |
| `template.html` | 検索ページの雛形 |
| `index.html` | 生成物（＝公開ページ本体）。Pagesのトップに表示 |
| `index.json` | 生成物（索引データ） |
| `watch.py` | フォルダ自動監視。依存ライブラリ不要 |
| `update.bat` / `watch.bat` | 更新・監視のワンクリック起動 |
| `install_task.ps1` | ログオン時に自動監視するタスクを登録 |
| `.github/workflows/deploy-pages.yml` | push時にPagesへ自動デプロイ |

---

## ⚠️ セキュリティ上の注意
このリポジトリと公開ページは **公開（誰でも閲覧可能）** です。ページには
**注文書のファイル名一覧**が載ります（タイトルが外部から見える）。
ただし **ファイルの中身はOneDriveの権限で保護**され、リンクを踏んでも権限の無い人は開けません。
ファイル名も外部に見せたくない場合は、社内限定の別ホスティングをご検討ください。
