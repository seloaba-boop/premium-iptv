"""
Premium IPTV - Telegram Support Bot
Railway-optimiert mit Environment Variables
"""

import os
from anthropic import Anthropic
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes
)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ADMIN_CHAT_IDS = [int(os.getenv("ADMIN_CHAT_IDS", "0"))]

# Anthropic Client initialisieren
anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)

# Wissensdatenbank (FAQ)
KNOWLEDGE_BASE = """
Premium IPTV - Support Wissensdatenbank

BESTELLUNG & PREISE:
Q: Was kostet Premium IPTV?
A: Unser Jahresabonnement kostet 119,99€ für volle 12 Monate. Das sind nur 10€ pro Monat!

Q: Welche Zahlungsmethoden akzeptiert ihr?
A: Wir akzeptieren Kreditkarte, PayPal, Google Pay und Apple Pay über unsere sichere Stripe-Zahlung.

Q: Gibt es eine Testversion?
A: Ja! Du kannst Premium IPTV 24 Stunden lang kostenlos testen. Nutze den Befehl /test um eine anzufordern.

EINRICHTUNG & TECHNIK:
Q: Wie richte ich IPTV ein?
A: 1) Lade eine IPTV-App herunter (z.B. IPTV Smarters Pro)
   2) Öffne die App und wähle "Login with Xtream Codes API"
   3) Gib die Zugangsdaten ein, die du erhalten hast
   4) Fertig! Alle Kanäle werden automatisch geladen

Q: Welche App soll ich nutzen?
A: Empfohlene Apps: IPTV Smarters Pro, TiviMate, GSE Smart IPTV, VLC Media Player

Q: Auf welchen Geräten funktioniert es?
A: Smart TV, Fire TV Stick, Apple TV, Android TV, iOS, Android, Windows, Mac, Linux.

KANÄLE & INHALTE:
Q: Wie viele Kanäle gibt es?
A: Über 10.000 Live-TV-Kanäle aus aller Welt in HD und 4K-Qualität!

Q: Welche deutschen Kanäle sind verfügbar?
A: Alle deutschen Hauptsender: ARD, ZDF, RTL, ProSieben, Sat.1, VOX, Sport1, Sky Sport, DAZN, und viele mehr!
"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Command"""
    await update.message.reply_text(
        "👋 *Willkommen beim Premium IPTV Support!*\n\n"
        "Ich bin dein KI-Support-Agent und helfe dir gerne weiter.\n\n"
        "🎯 *Was kann ich für dich tun?*\n"
        "• Fragen zur Bestellung & Bezahlung\n"
        "• Hilfe bei der Einrichtung\n"
        "• Technischer Support\n"
        "• Informationen zu Features & Kanälen\n\n"
        "💡 *Schnellbefehle:*\n"
        "/start - Diese Nachricht\n"
        "/test - 24h Testversion anfragen\n"
        "/hilfe - Häufige Fragen\n\n"
        "Stelle mir einfach deine Frage! 😊",
        parse_mode='Markdown'
    )


async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test Command"""
    user_id = update.effective_user.id
    user_name = update.effective_user.username or update.effective_user.first_name
    
    await update.message.reply_text(
        "🧪 *24-Stunden-Testversion angefordert!*\n\n"
        "Ein Admin wird dir gleich deine Testdaten zusenden.\n\n"
        "Viel Spaß beim Testen! 🍿",
        parse_mode='Markdown'
    )
    
    # Benachrichtige Admins
    for admin_id in ADMIN_CHAT_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"🆕 *Neue Testanfrage*\n\nUser: @{user_name}\nUser ID: {user_id}",
                parse_mode='Markdown'
            )
        except:
            pass


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hilfe Command"""
    await update.message.reply_text(
        "❓ *Häufig gestellte Fragen*\n\n"
        "🎯 *Bestellung:*\n"
        "• Was kostet es?\n"
        "• Welche Zahlungsmethoden?\n\n"
        "🔧 *Einrichtung:*\n"
        "• Wie richte ich IPTV ein?\n"
        "• Welche App soll ich nutzen?\n\n"
        "📺 *Kanäle:*\n"
        "• Wie viele Kanäle?\n"
        "• Deutsche Kanäle?\n\n"
        "💬 Stelle mir einfach deine Frage!",
        parse_mode='Markdown'
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler für alle Text-Nachrichten - KI-Antworten"""
    user_message = update.message.text
    user_name = update.effective_user.first_name
    
    print(f"[{user_name}] {user_message}")
    
    try:
        # Sende Typing-Anzeige
        await update.message.chat.send_action(action="typing")
        
        # Claude API
        response = anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            system=f"""Du bist ein freundlicher Support-Agent für Premium IPTV.

Nutze diese Wissensdatenbank:
{KNOWLEDGE_BASE}

Regeln:
- Sei freundlich und hilfsbereit
- Antworte auf Deutsch
- Kurz und präzise (max. 200 Wörter)
- Nutze Emojis
- Der User heißt: {user_name}""",
            messages=[{"role": "user", "content": user_message}]
        )
        
        bot_reply = response.content[0].text
        print(f"[BOT] {bot_reply[:100]}...")
        
        await update.message.reply_text(bot_reply)
        
    except Exception as e:
        print(f"FEHLER: {e}")
        await update.message.reply_text(
            "😕 Entschuldigung, da ist etwas schiefgelaufen.\n"
            "Bitte versuche es erneut oder nutze /hilfe"
        )


def main():
    """Bot starten"""
    
    # Prüfe Environment Variables
    if not TELEGRAM_BOT_TOKEN or not ANTHROPIC_API_KEY:
        print("❌ ERROR: Environment Variables nicht gesetzt!")
        print("TELEGRAM_BOT_TOKEN:", "✓" if TELEGRAM_BOT_TOKEN else "✗")
        print("ANTHROPIC_API_KEY:", "✓" if ANTHROPIC_API_KEY else "✗")
        return
    
    print("🔑 Environment Variables geladen:")
    print(f"  Bot Token: {TELEGRAM_BOT_TOKEN[:20]}...")
    print(f"  API Key: {ANTHROPIC_API_KEY[:20]}...")
    print(f"  Admin IDs: {ADMIN_CHAT_IDS}")
    
    # Application erstellen
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(CommandHandler("hilfe", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Premium IPTV Support Bot gestartet...")
    print("🚀 Bot läuft auf Railway!")
    print("Bot ist online und wartet auf Nachrichten!")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
