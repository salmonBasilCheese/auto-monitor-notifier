import json
import os
from pathlib import Path
import time
from dotenv import load_dotenv
import requests
import schedule

# .env ファイルから環境変数をロード
load_dotenv()

# 設定定数
CACHE_FILE = Path("seen_cache.json")
WEBHOOK_URL = os.getenv("WEBHOOOK_URL", "")
TARGET_API_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
ITEM_API_URL = "https://hacker-news.firebaseio.com/v0/item/{item_id}.json"


def load_seen_ids(cache_path: Path) -> set[int]:
    """過去に通知済みのIDリストをJSONファイルから読み込む。"""
    if not cache_path.exists():
        return set()
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("seen_ids", []))
    except Exception as e:
        print(f"[Warning] キャッシュ読み込み失敗（初期化します）: {e}")
        return set()


def save_seen_ids(cache_path: Path, seen_ids: set[int]) -> None:
    """通知済みのIDリストをJSONファイルに永続化保存する。"""
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump({"seen_ids": list(seen_ids)}, f, indent=2)
    except Exception as e:
        print(f"[Error] キャッシュ書き込み失敗: {e}")


def send_notification(title: str, url: str, webhook_url: str) -> None:
    """Webhook 経由で通知を送信する（Discord / Slack 汎用形式）。"""
    payload = {
        "content": f"📢 **新着トピック検知**\n**タイトル:** {title}\n**URL:** {url}"
    }

    if not webhook_url:
        print(f"[Dry-Run 通知]\n{payload['content']}\n" + "-" * 40)
        return

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        print(f"[Success] 通知送信完了: {title}")
    except requests.exceptions.RequestException as e:
        print(f"[Error] Webhook送信失敗: {e}")


def check_updates() -> None:
    """監視対象をチェックし、新規差分のみを通知する。"""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 監視チェックを実行中...")

    seen_ids = load_seen_ids(CACHE_FILE)

    try:
        # 最新のTop 5件のIDを取得
        res = requests.get(TARGET_API_URL, timeout=10)
        res.raise_for_status()
        top_ids = res.json()[:5]

        new_items_found = False

        for item_id in top_ids:
            if item_id not in seen_ids:
                # 新規IDの詳細情報を取得
                item_res = requests.get(
                    ITEM_API_URL.format(item_id=item_id), timeout=10
                )
                if item_res.status_code == 200:
                    item_data = item_res.json()
                    title = item_data.get("title", "No Title")
                    url = item_data.get(
                        "url",
                        f"https://news.ycombinator.com/item?id={item_id}",
                    )

                    # 通知実行
                    send_notification(title, url, WEBHOOK_URL)
                    seen_ids.add(item_id)
                    new_items_found = True

        if new_items_found:
            save_seen_ids(CACHE_FILE, seen_ids)
        else:
            print("[Info] 新規差分はありませんでした。")

    except Exception as e:
        print(f"[Error] 監視処理中にエラー発生: {e}")


def main():
    print("=== 定期監視・通知システム起動 ===")

    # 起動時に初回実行
    check_updates()

    # 1分ごとに定期実行するスケジュール登録
    schedule.every(1).minutes.do(check_updates)

    print("定期スケジューラ待機中 (Ctrl+C で停止)...")
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
