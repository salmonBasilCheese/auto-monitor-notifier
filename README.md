# Auto Monitor & Notifier

APIおよびWebリソースを定期監視し、新着差分のみを検知してWebhook（Discord/Slack等）へ通知する自動化スクリプトです。

## 主な特徴
- **差分検知機能:** 過去に通知済みのIDをローカルJSON（ステート）に永続化し、二重通知を防止
- **スケジューリング:** `schedule` ライブラリによる一定間隔（デフォルト1分）でのバックグラウンド自動実行
- **セキュリティ設計:** `python-dotenv` を採用し、Webhook URL等の機密情報をコードから完全分離
- **フォールバック機能:** Webhook未設定時でもコンソールへのDry-Run出力で安全に動作確認可能

## 必要環境
- Python 3.10+
- requests, schedule, python-dotenv

## セットアップ
```
# bash
python -m venv .venv

# Windows
.venv\Scripts\activate
pip install requests schedule python-dotenv