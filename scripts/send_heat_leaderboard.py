#!/usr/bin/env python3
"""One-off: notify last-week frontend projects about Ecosystem Heat Leaderboard."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from telethon import TelegramClient
from telethon.errors import FloodWaitError

from bot.workflow_form_dispatch import match_project_to_chat

MSG = (
    "Hi team — your project can now join the BOT Chain Ecosystem Heat Leaderboard.\n\n"
    "Take part in the ranking for a chance to share the rewards. Full details:\n"
    "https://www.botchain.ai/en/ecosystem-ranking/"
)

PROJECTS_FILE = Path("/tmp/frontend_week_projects.txt")
RESULT_FILE = Path("/tmp/heat_leaderboard_send_result.json")


def load_titles(path: str) -> dict[int, str]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    block = raw.get("titles") if isinstance(raw, dict) else raw
    out: dict[int, str] = {}
    for key, value in (block or {}).items():
        try:
            chat_id = int(key)
        except (TypeError, ValueError):
            continue
        if isinstance(value, dict):
            title = str(value.get("title") or "").strip()
        else:
            title = str(value or "").strip()
        if title:
            out[chat_id] = title
    return out


async def main() -> None:
    api_id = int(
        os.environ.get("TELEGRAM_API_ID") or os.environ.get("TG_API_ID") or ""
    )
    api_hash = (
        os.environ.get("TELEGRAM_API_HASH") or os.environ.get("TG_API_HASH") or ""
    )
    session = os.environ.get("TG_SESSION", "botchain_session")
    titles = {
        **load_titles("/opt/delivery-agent/data/folder_title_cache.json"),
        **load_titles("/opt/botchain-qa-tg-bot/data/folder_title_cache.json"),
    }
    names = [
        line.strip()
        for line in PROJECTS_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    targets: list[dict] = []
    skipped: list[dict] = []
    for name in names:
        chat_id, reason = match_project_to_chat(name, titles)
        if chat_id is None:
            skipped.append({"project": name, "reason": reason})
        else:
            targets.append(
                {
                    "project": name,
                    "chat_id": chat_id,
                    "title": titles.get(chat_id, ""),
                }
            )

    client = TelegramClient(session, api_id, api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        print("NOT_AUTHORIZED")
        return

    sent: list[dict] = []
    failed: list[dict] = []
    for index, row in enumerate(targets, start=1):
        try:
            await client.send_message(row["chat_id"], MSG)
            sent.append(row)
            print(f"SENT {index}/{len(targets)} {row['project']} -> {row['chat_id']}")
        except FloodWaitError as exc:
            wait = int(getattr(exc, "seconds", 30)) + 2
            print(f"FLOOD wait {wait}s at {row['project']}")
            await asyncio.sleep(wait)
            try:
                await client.send_message(row["chat_id"], MSG)
                sent.append(row)
                print(f"SENT retry {row['project']}")
            except Exception as err:  # noqa: BLE001
                failed.append({**row, "error": str(err)[:200]})
                print(f"FAIL {row['project']}: {err}")
        except Exception as err:  # noqa: BLE001
            failed.append({**row, "error": str(err)[:200]})
            print(f"FAIL {row['project']}: {err}")
        await asyncio.sleep(1.2)

    await client.disconnect()
    summary = {
        "sent": len(sent),
        "failed": len(failed),
        "skipped": skipped,
        "failed_rows": failed,
        "sent_projects": [item["project"] for item in sent],
    }
    RESULT_FILE.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        "SUMMARY",
        json.dumps(
            {
                "sent": len(sent),
                "failed": len(failed),
                "skipped": len(skipped),
            }
        ),
    )


if __name__ == "__main__":
    asyncio.run(main())
