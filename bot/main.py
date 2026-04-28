"""Telegram bot wrapping iNotWiki.

Members of the configured Telegram group(s) can run a wikiblitz against an
iNaturalist project; the bot replies with a short summary plus the full
report rendered as a PDF.

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
import html
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
from bot.pdf import md_to_pdf  # noqa: E402

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
        return None, DEFAULT_LANGS, set(), f"invalid project_id: {project!r}"
    langs = DEFAULT_LANGS[:]
    accept: set[str] = set()
    for kv in args[1:]:
        if "=" not in kv:
            return project, langs, accept, f"expected key=value, got {kv!r}"
        k, v = kv.split("=", 1)
        k = k.strip().lower()
        if k == "lang":
            langs = [x.strip() for x in v.split(",") if x.strip()]
            if not langs:
                return project, DEFAULT_LANGS, accept, "lang= without values"
        elif k == "accept":
            accept = {x.strip().lower() for x in v.split(",") if x.strip()}
        else:
            return project, langs, accept, f"unknown option {k!r}"
    return project, langs, accept, None


def format_summary(summary: dict[str, Any]) -> str:
    """Build a Telegram HTML message summarising the report."""
    missing = summary["missing_by_lang"]
    miss_lines = "\n".join(
        f"  • {html.escape(lang)}: {count}" for lang, count in missing.items()
    )
    top_species = "\n".join(
        f"  {i+1}. {html.escape(str(name))} ({n})"
        for i, (name, n) in enumerate(summary["top_species"][:5])
    ) or "  (none)"
    return (
        f"📊 <b>iNaturalist project</b>: <code>{html.escape(str(summary['search_value']))}</code>\n"
        f"• Observations: <b>{summary['total_observations']}</b>\n"
        f"• Unique species: <b>{summary['unique_species']}</b>\n"
        f"• Observers: <b>{summary['unique_observers']}</b>\n"
        f"• Not on Wikidata: <b>{summary['not_on_wikidata']}</b>\n"
        f"\n<b>Missing Wikipedia articles:</b>\n{miss_lines}\n"
        f"\n<b>Most observed:</b>\n{top_species}"
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
        "🌱 <b>iNotListed bot</b> — finds missing Wikipedia articles for an "
        "iNaturalist project, so a WikiProject Biodiversity wikiblitz can target "
        "what's actually missing.\n\n"
        "<b>What it does</b>\n"
        "Given an iNaturalist project (slug or numeric id), the bot:\n"
        "  1. fetches every observation,\n"
        "  2. looks up each taxon on Wikidata,\n"
        "  3. checks whether a Wikipedia article exists in your chosen languages,\n"
        "  4. replies with a summary + a PDF report listing the gaps.\n\n"
        "<b>How to use</b> (members of the configured Telegram group(s)):\n"
        "<code>/wikiblitz &lt;project&gt; [lang=en,nl,…] [accept=wikidata,gbif]</code>\n\n"
        "<b>Examples</b>\n"
        "  <code>/wikiblitz biohackathon-2025</code>\n"
        "  <code>/wikiblitz datos-vivos-gb32-bogota-2025 lang=en,es,pt</code>\n\n"
        "<b>Arguments</b>\n"
        "• <code>project</code> — iNaturalist project slug or numeric id\n"
        "• <code>lang=</code> — comma-separated Wikipedia language codes "
        "(default: en,es,ja,ar,nl,pt,fr)\n"
        "• <code>accept=</code> — reserved for upcoming filters\n\n"
        "Big projects can take a few minutes. You'll get a ⏳ ack first; "
        "the summary + PDF follow when the run finishes.\n\n"
        "Source &amp; issues: "
        "https://codeberg.org/wikiproject-biodiversity/iNotListed",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


async def cmd_wikiblitz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user is None:
        return
    if not await is_member(context, user.id):
        await update.message.reply_text(
            "Sorry, this bot is only available to members of the configured "
            "Telegram group(s)."
        )
        return

    project, langs, accept, err = parse_args(context.args or [])
    if err:
        await update.message.reply_text(f"❌ {err}")
        return
    if not project:
        await update.message.reply_text(
            "Provide a project_id or slug: /wikiblitz <project_id> [lang=en,nl]"
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
        f"⏳ Working on <code>{html.escape(project)}</code> "
        f"(languages: {html.escape(','.join(langs))}). "
        "This may take a few minutes.",
        parse_mode=ParseMode.HTML,
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
        await ack.edit_text(f"❌ Error: {exc}")
        return

    if summary.get("total_observations", 0) == 0:
        await ack.edit_text(
            f"⚠️ <b>No observations found</b> for <code>{html.escape(project)}</code>.\n\n"
            "Possible causes:\n"
            "• the project_id / slug is misspelled,\n"
            "• the project doesn't exist on iNaturalist,\n"
            "• the project exists but currently has no observations.\n\n"
            "Open <code>https://www.inaturalist.org/projects/" + html.escape(project) + "</code> "
            "in a browser to verify.",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        return

    try:
        await ack.edit_text(format_summary(summary), parse_mode=ParseMode.HTML)
    except Exception:  # noqa: BLE001 - last-ditch fallback
        log.exception("HTML render failed; falling back to plain text")
        plain = format_summary(summary)
        for tag in ("<b>", "</b>", "<code>", "</code>"):
            plain = plain.replace(tag, "")
        await ack.edit_text(plain)

    # Render the markdown to PDF for Telegram (which previews PDFs nicely).
    pdf_path: str | None = None
    try:
        pdf_path = await asyncio.to_thread(md_to_pdf, report_path)
    except Exception:  # noqa: BLE001 - fall back to .md
        log.exception("PDF rendering failed; sending markdown instead")

    attachment_path = pdf_path or report_path
    with open(attachment_path, "rb") as fh:
        await update.message.reply_document(
            document=fh,
            filename=os.path.basename(attachment_path),
            caption=f"Full report for {project}",
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
