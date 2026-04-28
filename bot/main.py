"""Telegram bot wrapping iNotWiki.

Members of the configured Telegram channel can run a wikiblitz against an
iNaturalist project; the bot replies with a short summary plus the full
Markdown report as an attachment.

Configured via environment:
    TELEGRAM_BOT_TOKEN   token from @BotFather
    TELEGRAM_CHANNEL     comma-separated list of channel/group identifiers
                         (each one a @username or a numeric chat-id);
                         a user is allowed if they are a member of ANY of them.
                         If empty, the bot is unrestricted (development).
    INOTLISTED_WORKDIR   directory to write reports (default: ./reports/telegram)
"""

from __future__ import annotations

import asyncio
import logging
import os
import pathlib
import re
import sys
from typing import Any

from telegram import Update
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

# Make the sibling iNotWiki.py importable when running from /home/inotbot/iNotListed.
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from iNotWiki import generate_markdown_report  # noqa: E402

DEFAULT_LANGS = ["en", "es", "ja", "ar", "nl", "pt", "fr"]
PROJECT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{1,80}$")
ALLOWED_MEMBER_STATUSES = {
    ChatMemberStatus.OWNER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.MEMBER,
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
# httpx logs the full URL of every Telegram API call, and python-telegram-bot
# embeds the bot token in the URL path (`/bot<token>/getMe`). Silence it so the
# token never leaks into journald / log files.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
log = logging.getLogger("inotbot")


def parse_args(args: list[str]) -> tuple[str | None, list[str], set[str], str | None]:
    """First positional = project; remaining = key=value (lang=, accept=)."""
    if not args:
        return None, DEFAULT_LANGS, set(), None
    project = args[0].strip()
    if not PROJECT_RE.match(project):
        return None, DEFAULT_LANGS, set(), f"ongeldig project_id: {project!r}"
    langs = DEFAULT_LANGS[:]
    accept: set[str] = set()
    for kv in args[1:]:
        if "=" not in kv:
            return project, langs, accept, f"verwachtte key=value, kreeg {kv!r}"
        k, v = kv.split("=", 1)
        k = k.strip().lower()
        if k == "lang":
            langs = [x.strip() for x in v.split(",") if x.strip()]
            if not langs:
                return project, DEFAULT_LANGS, accept, "lang= zonder waardes"
        elif k == "accept":
            accept = {x.strip().lower() for x in v.split(",") if x.strip()}
        else:
            return project, langs, accept, f"onbekende optie {k!r}"
    return project, langs, accept, None


def format_summary(summary: dict[str, Any]) -> str:
    missing = summary["missing_by_lang"]
    miss_lines = "\n".join(
        f"  • {lang}: {count}" for lang, count in missing.items()
    )
    top_species = "\n".join(
        f"  {i+1}. {name} ({n})"
        for i, (name, n) in enumerate(summary["top_species"][:5])
    ) or "  (geen)"
    return (
        f"📊 *iNaturalist project*: `{summary['search_value']}`\n"
        f"• Observaties: *{summary['total_observations']}*\n"
        f"• Unieke soorten: *{summary['unique_species']}*\n"
        f"• Waarnemers: *{summary['unique_observers']}*\n"
        f"• Niet op Wikidata: *{summary['not_on_wikidata']}*\n"
        f"\n*Ontbrekende Wikipedia-artikelen:*\n{miss_lines}\n"
        f"\n*Meest waargenomen:*\n{top_species}"
    )


def _configured_channels() -> list[str]:
    raw = os.environ.get("TELEGRAM_CHANNEL", "")
    return [c.strip() for c in raw.split(",") if c.strip()]


async def is_member(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    channels = _configured_channels()
    if not channels:
        return True  # no gate configured (dev mode)
    for channel in channels:
        try:
            member = await context.bot.get_chat_member(channel, user_id)
        except Exception as exc:  # noqa: BLE001
            log.warning("membership check failed in %s for %s: %s", channel, user_id, exc)
            continue
        if member.status in ALLOWED_MEMBER_STATUSES:
            return True
    return False


async def cmd_start(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "iNotListed bot.\n\n"
        "Gebruik:\n"
        "  /wikiblitz <project_id_of_slug> [lang=en,nl] [accept=wikidata,gbif]\n\n"
        "Voorbeeld:\n"
        "  /wikiblitz biohackathon-2025 lang=en,nl\n\n"
        "Toegang: leden van het kanaal *WikiProject Biodiversity*.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_wikiblitz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user is None:
        return
    if not await is_member(context, user.id):
        await update.message.reply_text(
            "Sorry, deze bot is alleen voor leden van het kanaal "
            "WikiProject Biodiversity."
        )
        return

    project, langs, accept, err = parse_args(context.args or [])
    if err:
        await update.message.reply_text(f"❌ {err}")
        return
    if not project:
        await update.message.reply_text(
            "Geef een project_id of slug: /wikiblitz <project_id> [lang=en,nl]"
        )
        return

    if accept:
        log.info("accept= filter received but not yet applied: %s", sorted(accept))

    workdir = pathlib.Path(
        os.environ.get("INOTLISTED_WORKDIR", _REPO_ROOT / "reports" / "telegram")
    )
    output_folder = workdir / project
    output_folder.mkdir(parents=True, exist_ok=True)

    ack = await update.message.reply_text(
        f"⏳ Bezig met `{project}` (talen: {','.join(langs)}). "
        "Dit kan een paar minuten duren.",
        parse_mode=ParseMode.MARKDOWN,
    )

    try:
        report_path, summary = await asyncio.to_thread(
            generate_markdown_report,
            project,
            search_type="project",
            languages=langs,
            output_folder=str(output_folder),
        )
    except Exception as exc:  # noqa: BLE001
        log.exception("report failed for %s", project)
        await ack.edit_text(f"❌ Fout: {exc}")
        return

    try:
        await ack.edit_text(format_summary(summary), parse_mode=ParseMode.MARKDOWN)
    except Exception:  # noqa: BLE001 - markdown can fail on weird names
        await ack.edit_text(format_summary(summary))

    with open(report_path, "rb") as fh:
        await update.message.reply_document(
            document=fh,
            filename=os.path.basename(report_path),
            caption=f"Volledig rapport voor {project}",
        )


def main() -> int:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("TELEGRAM_BOT_TOKEN not set", file=sys.stderr)
        return 1

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler(["start", "help"], cmd_start))
    app.add_handler(CommandHandler("wikiblitz", cmd_wikiblitz))

    channels = _configured_channels()
    log.info("inotbot starting (allowed channels=%s)", channels or "(none — open mode)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
    return 0


if __name__ == "__main__":
    sys.exit(main())
