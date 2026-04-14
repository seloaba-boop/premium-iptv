"""
Premium IPTV — Auto-Poster für @premium_tv_deutschland

Was er macht:
- Postet 2x täglich (12:30 + 21:00 Europe/Berlin) einen Post aus posts_queue.json
- Rotiert durch die Queue, wiederholt ab Ende
- Schickt dir (Admin) jeden Morgen 09:00 ein Briefing
- Admin-Commands: /pause /resume /skip /status /queue /post <text> /next

Deployment: Railway als eigener Worker neben telegram_bot.py

Environment Variables:
    CHANNEL_BOT_TOKEN  — Bot-Token (derselbe Bot muss Admin im Kanal sein mit Post-Rechten)
    CHANNEL_ID         — @premium_tv_deutschland  (oder numerische ID)
    ADMIN_CHAT_ID      — Deine Telegram-User-ID (z.B. via @userinfobot)
"""

import json
import os
import logging
from datetime import time as dtime, datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger("poster")

BASE = Path(__file__).parent
QUEUE_FILE = BASE / "posts_queue.json"
STATE_FILE = BASE / "poster_state.json"

TZ = ZoneInfo("Europe/Berlin")
POST_TIMES = [dtime(12, 30, tzinfo=TZ), dtime(21, 0, tzinfo=TZ)]
BRIEFING_TIME = dtime(9, 0, tzinfo=TZ)


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"index": 0, "paused": False, "posted_log": []}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def load_queue():
    return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))["posts"]


async def post_to_channel(context: ContextTypes.DEFAULT_TYPE):
    state = load_state()
    if state["paused"]:
        log.info("Paused — skipping scheduled post")
        return

    queue = load_queue()
    post = queue[state["index"] % len(queue)]

    try:
        msg = await context.bot.send_message(
            chat_id=os.environ["CHANNEL_ID"],
            text=post["text"],
            parse_mode=None,
            disable_web_page_preview=False,
        )
        if post.get("pin"):
            try:
                await context.bot.pin_chat_message(
                    chat_id=os.environ["CHANNEL_ID"],
                    message_id=msg.message_id,
                    disable_notification=True,
                )
            except Exception as e:
                log.warning(f"Pin failed: {e}")

        state["index"] += 1
        state["posted_log"].append({
            "ts": datetime.now(TZ).isoformat(),
            "id": post["id"],
            "type": post["type"],
        })
        state["posted_log"] = state["posted_log"][-50:]
        save_state(state)

        await notify_admin(
            context,
            f"✅ Post #{post['id']} ({post['type']}) live im Kanal."
        )
    except Exception as e:
        log.error(f"Post failed: {e}")
        await notify_admin(context, f"❌ Auto-Post fehlgeschlagen: {e}")


async def notify_admin(context, text):
    admin = os.environ.get("ADMIN_CHAT_ID")
    if not admin:
        return
    try:
        await context.bot.send_message(chat_id=admin, text=text)
    except Exception as e:
        log.warning(f"Admin notify failed: {e}")


async def daily_briefing(context: ContextTypes.DEFAULT_TYPE):
    state = load_state()
    queue = load_queue()

    yesterday_cutoff = datetime.now(TZ) - timedelta(hours=24)
    posted_24h = [
        p for p in state["posted_log"]
        if datetime.fromisoformat(p["ts"]) > yesterday_cutoff
    ]

    next_idx = state["index"] % len(queue)
    next_post = queue[next_idx]

    preview = next_post["text"][:200] + ("..." if len(next_post["text"]) > 200 else "")

    status_emoji = "⏸️" if state["paused"] else "▶️"
    text = (
        f"☀️ *Guten Morgen Selo!*\n\n"
        f"Status: {status_emoji} {'Pausiert' if state['paused'] else 'Aktiv'}\n"
        f"Queue-Position: {next_idx + 1}/{len(queue)}\n"
        f"Posts in letzten 24h: {len(posted_24h)}\n\n"
        f"📣 *Heute geplant:*\n"
        f"• 12:30 — {next_post['type']} (#{next_post['id']})\n"
        f"• 21:00 — {queue[(next_idx + 1) % len(queue)]['type']} "
        f"(#{queue[(next_idx + 1) % len(queue)]['id']})\n\n"
        f"*Preview 12:30:*\n{preview}\n\n"
        f"Commands: /status /pause /resume /skip /next /queue"
    )
    await notify_admin(context, text)


# --- Admin-Commands ---

def admin_only(func):
    async def wrapper(update: Update, context):
        admin = os.environ.get("ADMIN_CHAT_ID")
        if not admin or str(update.effective_user.id) != str(admin):
            await update.message.reply_text("⛔ Nur für Admin.")
            return
        return await func(update, context)
    return wrapper


@admin_only
async def cmd_status(update: Update, context):
    state = load_state()
    queue = load_queue()
    await update.message.reply_text(
        f"{'⏸️ Pausiert' if state['paused'] else '▶️ Aktiv'}\n"
        f"Nächster Post: #{queue[state['index'] % len(queue)]['id']} "
        f"({queue[state['index'] % len(queue)]['type']})\n"
        f"Position: {state['index'] % len(queue) + 1}/{len(queue)}\n"
        f"Posts insgesamt: {state['index']}"
    )


@admin_only
async def cmd_pause(update: Update, context):
    state = load_state()
    state["paused"] = True
    save_state(state)
    await update.message.reply_text("⏸️ Auto-Posting pausiert.")


@admin_only
async def cmd_resume(update: Update, context):
    state = load_state()
    state["paused"] = False
    save_state(state)
    await update.message.reply_text("▶️ Auto-Posting aktiv.")


@admin_only
async def cmd_skip(update: Update, context):
    state = load_state()
    state["index"] += 1
    save_state(state)
    queue = load_queue()
    await update.message.reply_text(
        f"⏭️ Übersprungen. Nächster: #{queue[state['index'] % len(queue)]['id']}"
    )


@admin_only
async def cmd_next(update: Update, context):
    """Postet JETZT den nächsten Post aus der Queue."""
    await update.message.reply_text("📤 Poste jetzt...")
    await post_to_channel(context)


@admin_only
async def cmd_queue(update: Update, context):
    state = load_state()
    queue = load_queue()
    lines = []
    for i in range(min(10, len(queue))):
        idx = (state["index"] + i) % len(queue)
        p = queue[idx]
        lines.append(f"{i+1}. #{p['id']} — {p['type']}")
    await update.message.reply_text("Nächste 10:\n" + "\n".join(lines))


@admin_only
async def cmd_post(update: Update, context):
    """Ad-hoc Post: /post <text>"""
    if not context.args:
        await update.message.reply_text("Nutze: /post <dein Text>")
        return
    text = " ".join(context.args)
    try:
        await context.bot.send_message(
            chat_id=os.environ["CHANNEL_ID"],
            text=text,
        )
        await update.message.reply_text("✅ Gepostet.")
    except Exception as e:
        await update.message.reply_text(f"❌ Fehler: {e}")


@admin_only
async def cmd_briefing(update: Update, context):
    await daily_briefing(context)


def main():
    token = os.environ.get("CHANNEL_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("CHANNEL_BOT_TOKEN nicht gesetzt!")
    if not os.environ.get("CHANNEL_ID"):
        raise SystemExit("CHANNEL_ID nicht gesetzt! (z.B. @premium_tv_deutschland)")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("pause", cmd_pause))
    app.add_handler(CommandHandler("resume", cmd_resume))
    app.add_handler(CommandHandler("skip", cmd_skip))
    app.add_handler(CommandHandler("next", cmd_next))
    app.add_handler(CommandHandler("queue", cmd_queue))
    app.add_handler(CommandHandler("post", cmd_post))
    app.add_handler(CommandHandler("briefing", cmd_briefing))

    jq = app.job_queue
    for t in POST_TIMES:
        jq.run_daily(post_to_channel, time=t)
    jq.run_daily(daily_briefing, time=BRIEFING_TIME)

    log.info("Auto-Poster gestartet. Post-Zeiten: %s", POST_TIMES)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
