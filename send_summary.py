"""Command-line: build the summary and send it to Telegram.

    python send_summary.py                 # write with Claude if available, send to Telegram
    python send_summary.py --dry-run       # print only
    python send_summary.py --no-claude     # template writer, no API call

Suitable for a daily cron job.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from salesinsight.data import load_sales
from salesinsight.metrics import Period
from salesinsight.summary import build_facts, write_summary
from salesinsight.telegram import TelegramError, send_message

ROOT = Path(__file__).parent


def main(argv: list[str] | None = None) -> int:
    load_dotenv(ROOT / ".env")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", default=ROOT / "data" / "sales.csv", type=Path)
    ap.add_argument("--dry-run", action="store_true", help="print the summary, do not send")
    ap.add_argument("--no-claude", action="store_true", help="use the template writer")
    args = ap.parse_args(argv)

    df, quality = load_sales(args.csv)
    facts = build_facts(df, quality, Period.latest(df))
    text, writer = write_summary(facts, use_claude=not args.no_claude)
    print(f"[ditulis oleh: {writer}]\n{text}\n")

    if args.dry_run:
        return 0
    try:
        msg = send_message(text)
    except TelegramError as exc:
        print(f"Gagal kirim: {exc}", file=sys.stderr)
        return 1
    print(f"Terkirim ke Telegram (message_id {msg['message_id']}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
