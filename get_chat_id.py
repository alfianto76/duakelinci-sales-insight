"""Find the TELEGRAM_CHAT_ID for your bot.

1. Put TELEGRAM_BOT_TOKEN in .env
2. Send any message to the bot (or add it to a group and send a message there)
3. Run: python get_chat_id.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
token = os.getenv("TELEGRAM_BOT_TOKEN")
if not token:
    sys.exit("Isi TELEGRAM_BOT_TOKEN di .env dulu.")

try:
    with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/getUpdates", timeout=15) as r:
        data = json.load(r)
except urllib.error.HTTPError as e:
    sys.exit(f"Telegram menolak token (HTTP {e.code}). Cek lagi tokennya.")

chats = {}
for u in data.get("result", []):
    msg = u.get("message") or u.get("channel_post") or u.get("my_chat_member") or {}
    chat = msg.get("chat")
    if chat:
        name = chat.get("title") or " ".join(filter(None, [chat.get("first_name"), chat.get("last_name")]))
        chats[chat["id"]] = f"{chat['type']}: {name}"

if not chats:
    sys.exit("Belum ada pesan. Kirim pesan apa saja ke bot (atau di grup yang ada botnya), lalu jalankan lagi.")
for cid, label in chats.items():
    print(f"TELEGRAM_CHAT_ID={cid}    # {label}")
