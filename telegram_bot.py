"""
Premium IPTV - KI Support Bot für Telegram
Verwendet Claude AI für intelligenten Kundensupport
"""

import os
from anthropic import Anthropic
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Konfiguration
TELEGRAM_BOT_TOKEN = "8384260643:AAFiOQD8qUDuy-svzdG0p-jwi6TtYZkI3P0"  # Von @BotFather
ANTHROPIC_API_KEY = "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"   # Von console.anthropic.com
ADMIN_CHAT_IDS = [1436567386]  # Liste mit Admin User IDs für Eskalation

# Claude Client initialisieren
anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)

# Wissensdatenbank für den Bot
KNOWLEDGE_BASE = """
# Premium IPTV Support Wissensdatenbank

## PRODUKT INFORMATION
- **Name**: Premium IPTV
- **Preis**: 119,99€ pro Jahr (Jahresabonnement)
- **Testversion**: 24 Stunden kostenlos testen
- **Geräte**: 1 Gerät gleichzeitig
- **Verfügbarkeit**: 99,9% Uptime-Garantie

## FEATURES
- Über 10.000 HD & 4K Kanäle
- Deutsche und internationale Sender
- Alle Sportevents live (Bundesliga, Champions League, NFL, NBA)
- Filme und Serien on Demand
- EPG (Elektronischer Programmführer)
- Dolby Digital Audio Support
- Kein Buffering, keine Verzögerungen

## HÄUFIGE FRAGEN (FAQ)

### Bestellung & Bezahlung
Q: Wie kann ich bestellen?
A: Kontaktiere uns direkt in dieser Telegram-Gruppe. Ein Admin wird dir die Zahlungsdetails zusenden.

Q: Welche Zahlungsmethoden akzeptiert ihr?
A: Wir akzeptieren PayPal, Banküberweisung und Kryptowährungen (Bitcoin, USDT).

Q: Bekomme ich eine Rechnung?
A: Ja, nach der Zahlung erhältst du automatisch eine Rechnung per E-Mail.

### Test & Aktivierung
Q: Wie funktioniert die 24h Testversion?
A: Schreibe "Test" in die Gruppe. Du erhältst Login-Daten, die 24 Stunden gültig sind.

Q: Wie lange dauert die Aktivierung?
A: Nach Zahlungseingang wird dein Account innerhalb von 1-2 Stunden aktiviert.

Q: Was passiert nach der Testphase?
A: Die Testversion endet automatisch nach 24h. Für die Vollversion musst du das Jahresabo buchen.

### Technische Fragen
Q: Auf welchen Geräten funktioniert es?
A: Smart TV, Amazon Fire TV Stick, Android Box, iPhone, iPad, Android Smartphone/Tablet, PC, Mac.

Q: Welche App brauche ich?
A: Wir empfehlen IPTV Smarters Pro (kostenlos). Alternativ: TiviMate, GSE Smart IPTV.

Q: Wie richte ich es ein?
A: 1) App installieren 2) M3U-Link oder Xtream-Codes Login eingeben 3) Fertig!

Q: Kann ich mehrere Geräte nutzen?
A: Nein, das Paket ist für 1 Gerät gleichzeitig. Bei Bedarf können Multi-Device-Pakete angefragt werden.

### Probleme & Troubleshooting
Q: Der Stream ruckelt oder buffert
A: 1) Prüfe deine Internetverbindung (mindestens 20 Mbit/s empfohlen)
    2) Wechsle auf einen anderen Server in der App
    3) Starte dein Gerät neu
    4) Kontaktiere den Support für individuelle Hilfe

Q: Login funktioniert nicht
A: 1) Überprüfe, ob Login-Daten korrekt eingegeben wurden
    2) Prüfe, ob dein Abonnement aktiv ist
    3) Kontaktiere den Support

Q: Bestimmte Kanäle fehlen
A: Die Kanalliste wird regelmäßig aktualisiert. Sende uns den Namen des gewünschten Kanals.

Q: EPG zeigt keine Daten
A: 1) Aktualisiere die EPG-Daten in der App
    2) Stelle sicher, dass du die neueste App-Version hast

### Kündigung & Verlängerung
Q: Wie kündige ich?
A: Das Abo verlängert sich automatisch. Für eine Kündigung schreibe uns spätestens 7 Tage vor Ablauf.

Q: Bekomme ich eine Erinnerung vor Verlängerung?
A: Ja, du erhältst 14 Tage vor Ablauf eine Erinnerung per Telegram.

Q: Gibt es eine Geld-zurück-Garantie?
A: Ja, innerhalb der ersten 7 Tage nach Aktivierung kannst du kündigen und bekommst dein Geld zurück.

## SUPPORT RICHTLINIEN
- Sei immer freundlich und professionell
- Antworte auf Deutsch
- Bei technischen Problemen: Step-by-Step Anleitung geben
- Bei Zahlungsfragen: An Admin weiterleiten
- Bei Beschwerden: Verständnis zeigen und Lösung anbieten
- Eskaliere komplexe Fälle an menschliche Admins

## WICHTIG
- Niemals Login-Daten öffentlich in der Gruppe teilen
- Bei Verdacht auf Account-Sharing: Admin informieren
- Keine illegalen Inhalte diskutieren
- Bei Abuse-Verdacht: Sofort Admin informieren
"""

# System Prompt für den Bot
SYSTEM_PROMPT = f"""Du bist ein KI-Support-Agent für Premium IPTV, einen IPTV-Streaming-Service.

DEINE ROLLE:
- Beantworte Kundenfragen professionell und freundlich auf Deutsch
- Nutze die Wissensdatenbank unten für akkurate Antworten
- Halte Antworten präzise und hilfreich
- Bei technischen Problemen: Gib klare Schritt-für-Schritt-Anleitungen
- Wenn du etwas nicht weißt: Sei ehrlich und leite an einen Admin weiter

KOMMUNIKATIONSSTIL:
- Freundlich aber professionell
- Verwende Emojis sparsam (nur zur Auflockerung)
- Kurze, klare Sätze
- Persönlich ansprechen mit "du"

WICHTIGE REGELN:
- Gib NIEMALS Login-Daten oder Links öffentlich bekannt
- Bei Zahlungsfragen → Leite an Admin weiter
- Bei Beschwerden → Zeige Verständnis und biete Lösungen
- Bei technischen Problemen → Frage nach Details (Gerät, App, Fehlermeldung)

ESKALATION:
Leite an einen menschlichen Admin weiter bei:
- Zahlungsproblemen
- Beschwerden über Service-Qualität
- Komplexen technischen Problemen
- Account-Sperrungen
- Rechtlichen Fragen

WISSENSDATENBANK:
{KNOWLEDGE_BASE}
"""

# Konversationshistorie pro User speichern (In Production: Datenbank verwenden)
conversation_history = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Command Handler"""
    user_id = update.effective_user.id
    conversation_history[user_id] = []
    
    welcome_message = """
👋 Willkommen beim Premium IPTV Support!

Ich bin dein KI-Support-Agent und helfe dir gerne weiter.

🎯 **Was kann ich für dich tun?**
• Fragen zur Bestellung & Bezahlung
• Hilfe bei der Einrichtung
• Technischer Support
• Informationen zu Features & Kanälen

💡 **Schnellbefehle:**
/start - Diese Nachricht
/test - 24h Testversion anfragen
/hilfe - Häufige Fragen
/status - Account-Status prüfen

Stelle mir einfach deine Frage! 😊
"""
    
    await update.message.reply_text(welcome_message)


async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test Command - Testversion anfragen"""
    await update.message.reply_text(
        "🎉 **24-Stunden-Testversion**\n\n"
        "Super! Du möchtest Premium IPTV testen.\n\n"
        "Ein Admin wird sich gleich bei dir melden und dir deine "
        "persönlichen Zugangsdaten zusenden.\n\n"
        "⏰ Die Testversion ist 24 Stunden gültig.\n"
        "📱 Du kannst auf 1 Gerät gleichzeitig streamen.\n\n"
        "Viel Spaß beim Testen! 🍿"
    )
    
    # Benachrichtige Admins
    for admin_id in ADMIN_CHAT_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"🆕 **Neue Testanfrage**\n\n"
                     f"User: {update.effective_user.first_name} "
                     f"({update.effective_user.username})\n"
                     f"User ID: {update.effective_user.id}"
            )
        except:
            pass


async def hilfe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hilfe Command - FAQ anzeigen"""
    faq_message = """
📚 **Häufig gestellte Fragen**

**Bestellung:**
• Preis: 119,99€ pro Jahr
• Zahlungsmethoden: PayPal, Überweisung, Krypto
• Aktivierung: 1-2 Stunden nach Zahlung

**Einrichtung:**
• App: IPTV Smarters Pro (empfohlen)
• Login: Xtream-Codes oder M3U-Link
• Geräte: 1 gleichzeitig

**Support:**
• 24/7 KI-Support in dieser Gruppe
• Bei Problemen: Einfach schreiben!

❓ Hast du eine spezielle Frage? Stell sie mir einfach!
"""
    
    await update.message.reply_text(faq_message)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Status Command - Account Status (Mock)"""
    await update.message.reply_text(
        "🔍 **Account-Status Prüfung**\n\n"
        "Um deinen Account-Status zu prüfen, benötige ich:\n"
        "• Deine E-Mail-Adresse oder\n"
        "• Deine Benutzer-ID\n\n"
        "Bitte sende diese Daten direkt an einen Admin (nicht öffentlich in der Gruppe!).\n\n"
        "💬 Schreibe: @AdminUsername"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hauptnachrichtenhandler mit Claude AI"""
    user_id = update.effective_user.id
    user_message = update.message.text
    user_name = update.effective_user.first_name
    
    # Initialisiere Konversationshistorie wenn nötig
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    
    # Füge Nutzernachricht zur Historie hinzu
    conversation_history[user_id].append({
        "role": "user",
        "content": user_message
    })
    
    # Begrenze Historie auf letzte 10 Nachrichten (Performance)
    if len(conversation_history[user_id]) > 10:
        conversation_history[user_id] = conversation_history[user_id][-10:]
    
    try:
        # "Tippt..." Indikator
        await update.message.chat.send_action("typing")
        
        # Claude API Anfrage
        response = anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=conversation_history[user_id]
        )
        
        bot_response = response.content[0].text
        
        # Füge Bot-Antwort zur Historie hinzu
        conversation_history[user_id].append({
            "role": "assistant",
            "content": bot_response
        })
        
        # Sende Antwort
        await update.message.reply_text(bot_response)
        
        # Log für Monitoring (In Production: In Datenbank loggen)
        print(f"[{user_name}] {user_message}")
        print(f"[BOT] {bot_response}\n")
        
    except Exception as e:
        error_message = (
            "❌ Entschuldigung, es gab einen technischen Fehler.\n\n"
            "Bitte versuche es erneut oder kontaktiere einen Admin: @AdminUsername"
        )
        await update.message.reply_text(error_message)
        print(f"ERROR: {str(e)}")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Error Handler"""
    print(f"Update {update} caused error {context.error}")


def main():
    """Hauptfunktion - Bot starten"""
    
    # Bot Application erstellen
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(CommandHandler("hilfe", hilfe_command))
    application.add_handler(CommandHandler("status", status_command))
    
    # Message Handler (für alle Text-Nachrichten)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Error Handler
    application.add_error_handler(error_handler)
    
    # Bot starten
    print("🤖 Premium IPTV Support Bot gestartet...")
    print("Bot ist online und wartet auf Nachrichten!\n")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
