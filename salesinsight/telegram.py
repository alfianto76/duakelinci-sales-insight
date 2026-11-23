"""Send a message through the Telegram Bot API (standard library only)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_LEN = 4096  # Telegram's limit per message


class TelegramError(RuntimeError):
    pass


def config_from_env() -> tuple[str | None, str | None]:
    return os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")


def send_message(text: str, token: str | None = None, chat_id: str | None = None, timeout: float = 15) -> dict:
    env_token, env_chat = config_from_env()
    token, chat_id = token or env_token, chat_id or env_chat
    if not token or not chat_id:
        raise TelegramError("TELEGRAM_BOT_TOKEN dan TELEGRAM_CHAT_ID belum diisi di .env.")
    if len(text) > MAX_LEN:
        text = text[: MAX_LEN - 1] + "…"

    body = json.dumps({"chat_id": chat_id, "text": text, "disable_web_page_preview": True}).encode()
    req = urllib.request.Request(
        API.format(token=token), data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as exc:
        try:
            detail = json.load(exc).get("description", "")
        except Exception:
            detail = ""
        # Never echo the URL: it contains the bot token.
        raise TelegramError(f"Telegram menolak pesan (HTTP {exc.code}): {detail}") from None
    except urllib.error.URLError as exc:
        raise TelegramError(f"Tidak bisa menghubungi Telegram: {exc.reason}") from None
    if not payload.get("ok"):
        raise TelegramError(f"Telegram menolak pesan: {payload.get('description', 'tanpa keterangan')}")
    return payload["result"]
