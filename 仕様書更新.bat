@echo off
chcp 65001 >nul
title 書籍仕様書 検索の更新
echo ============================================
echo    書籍仕様書 検索を更新します
echo ============================================
echo.
cd /d "C:\Users\moto8\Documents\GitHub\chumonsho-search"
echo [1/3] Excelから検索データを作成中...
python -m pip install openpyxl -q
python make_spec.py
echo.
echo [2/3] 公開中...
git add -A
git commit -m "仕様更新"
git push
echo.
echo ============================================
echo    完了しました。数十秒でNotionに反映されます。
echo    このウィンドウは閉じてOKです。
echo ============================================
pause
