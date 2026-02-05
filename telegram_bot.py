"""
Premium IPTV - Telegram Support Bot mit Länder-Auswahl & 18+ Option
Railway-optimiert mit interaktiven Menüs
"""

import os
from anthropic import Anthropic
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters, ContextTypes
)

# Konfiguration via Environment Variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ADMIN_CHAT_IDS = [int(os.getenv("ADMIN_CHAT_IDS", "0"))]

# Anthropic Client
anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)

# Länder-Definitionen mit Kanal-Anzahl
LAENDER = {
    "de": {"name": "🇩🇪 Deutschland", "kanäle": 500, "emoji": "🇩🇪"},
    "tr": {"name": "🇹🇷 Türkei", "kanäle": 350, "emoji": "🇹🇷"},
    "uk": {"name": "🇬🇧 Großbritannien", "kanäle": 400, "emoji": "🇬🇧"},
    "us": {"name": "🇺🇸 USA", "kanäle": 600, "emoji": "🇺🇸"},
    "fr": {"name": "🇫🇷 Frankreich", "kanäle": 300, "emoji": "🇫🇷"},
    "es": {"name": "🇪🇸 Spanien", "kanäle": 250, "emoji": "🇪🇸"},
    "it": {"name": "🇮🇹 Italien", "kanäle": 280, "emoji": "🇮🇹"},
    "nl": {"name": "🇳🇱 Niederlande", "kanäle": 200, "emoji": "🇳🇱"},
    "ar": {"name": "🇸🇦 Arabisch", "kanäle": 450, "emoji": "🇸🇦"},
    "pl": {"name": "🇵🇱 Polen", "kanäle": 180, "emoji": "🇵🇱"},
}

# Preisberechnung
def berechne_preis(laender_anzahl, adult_addon=False):
    """Berechnet Preis basierend auf Länder-Anzahl"""
    if laender_anzahl == 1:
        basis_preis = 79.99
    elif laender_anzahl == 2:
        basis_preis = 99.99
    elif laender_anzahl == 3:
        basis_preis = 119.99
    else:  # 4+ = Alle
        basis_preis = 149.99
    
    # 18+ Addon
    if adult_addon:
        basis_preis += 19.99
    
    return basis_preis


# User-Konfiguration speichern (in-memory, später DB!)
user_configs = {}


async def firetv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fire TV Setup Anleitung"""
    keyboard = [
        [InlineKeyboardButton("📖 Komplette Anleitung", url="https://premiumip-tv.de/fire-tv-anleitung.html")],
        [InlineKeyboardButton("🎬 Video-Tutorial", url="https://www.youtube.com/watch?v=XeMAkuzPZyc")],
        [InlineKeyboardButton("💬 Support", url="https://t.me/premiumiptv_support_bot")],
        [InlineKeyboardButton("« Hauptmenü", callback_data="back_to_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔥 *Fire TV Stick Installation*\n\n"
        "**Quick-Setup in 4 Schritten:**\n\n"
        "1️⃣ *Entwickleroptionen aktivieren*\n"
        "Einstellungen → Mein Fire TV → Entwickleroptionen\n"
        "→ Apps aus unbekannten Quellen: EIN ✅\n\n"
        "2️⃣ *Downloader installieren*\n"
        "Suche → \"Downloader\" → Installieren\n\n"
        "3️⃣ *IBO Player laden*\n"
        "In Downloader Code eingeben: `511693`\n"
        "→ Installieren → Datei löschen!\n\n"
        "4️⃣ *Zugangsdaten eingeben*\n"
        "IBO Player → M3U URL oder Xtream Codes\n"
        "→ Deine Daten eingeben (nach Kauf)\n\n"
        "💡 *PRO-TIPP:*\n"
        "Nutze `keyboard.amazonfiretvapp.com` auf deinem Handy\n"
        "zum einfacheren Eingeben! ⚡\n\n"
        "⏱️ *Dauer:* 5-10 Minuten\n"
        "📱 *App:* IBO Player (kostenlos)\n"
        "🔑 *Code:* 511693\n\n"
        "📖 Für die komplette Anleitung mit Screenshots\n"
        "und Video klicke auf die Buttons unten! 👇",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Command - Hauptmenü"""
    user_id = update.effective_user.id
    
    # Reset user config
    user_configs[user_id] = {
        "laender": [],
        "adult": False,
        "geraete": 1
    }
    
    keyboard = [
        [InlineKeyboardButton("🌍 Länder auswählen", callback_data="select_countries")],
        [InlineKeyboardButton("📦 Fertige Pakete", callback_data="show_packages")],
        [InlineKeyboardButton("🧪 24h Testversion", callback_data="request_test")],
        [InlineKeyboardButton("❓ Hilfe & FAQ", callback_data="show_faq")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 *Willkommen bei Premium IPTV!*\n\n"
        "🎬 Über 10.000 Kanäle in HD & 4K\n"
        "📺 50+ Länder verfügbar\n"
        "💰 Flexibel konfigurierbar\n\n"
        "🎯 *Wie möchtest du starten?*",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def select_countries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Länder-Auswahl Menü"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    selected = user_configs.get(user_id, {}).get("laender", [])
    
    keyboard = []
    
    # Länder in 2er-Reihen
    laender_items = list(LAENDER.items())
    for i in range(0, len(laender_items), 2):
        row = []
        for j in range(2):
            if i + j < len(laender_items):
                land_id, land_data = laender_items[i + j]
                # Checkmark wenn ausgewählt
                check = "✅ " if land_id in selected else ""
                row.append(
                    InlineKeyboardButton(
                        f"{check}{land_data['emoji']} {land_data['name'].split(' ')[1]}",
                        callback_data=f"toggle_country_{land_id}"
                    )
                )
        keyboard.append(row)
    
    # Alle Länder Option
    all_selected = "✅ " if len(selected) >= 10 else ""
    keyboard.append([
        InlineKeyboardButton(
            f"{all_selected}🌎 ALLE Länder (50+)",
            callback_data="toggle_country_all"
        )
    ])
    
    # Weiter-Button wenn mind. 1 Land ausgewählt
    if selected:
        keyboard.append([
            InlineKeyboardButton("➡️ Weiter zur Konfiguration", callback_data="config_devices")
        ])
    
    keyboard.append([
        InlineKeyboardButton("« Zurück", callback_data="back_to_start")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Berechne Gesamt-Kanalzahl
    total_kanäle = sum(LAENDER[l]["kanäle"] for l in selected if l in LAENDER)
    if len(selected) >= 10:
        total_kanäle = 10000
    
    selected_text = "\n".join([
        f"{LAENDER[l]['emoji']} {LAENDER[l]['name'].split(' ')[1]}"
        for l in selected if l in LAENDER
    ]) if selected and len(selected) < 10 else ""
    
    if len(selected) >= 10:
        selected_text = "🌎 ALLE Länder ausgewählt!"
    
    await query.edit_message_text(
        "🌍 *Wähle deine Länder*\n\n"
        f"Du kannst beliebig viele Länder kombinieren!\n\n"
        f"*Aktuell ausgewählt:*\n{selected_text or '_(Noch keine Auswahl)_'}\n\n"
        f"📺 Kanäle gesamt: *~{total_kanäle:,}*",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def toggle_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Länder an/abwählen"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Extrahiere Land-ID
    land_id = query.data.replace("toggle_country_", "")
    
    if user_id not in user_configs:
        user_configs[user_id] = {"laender": [], "adult": False, "geraete": 1}
    
    selected = user_configs[user_id]["laender"]
    
    if land_id == "all":
        # Alle an/aus
        if len(selected) >= 10:
            user_configs[user_id]["laender"] = []
        else:
            user_configs[user_id]["laender"] = list(LAENDER.keys())
    else:
        # Einzelnes Land togglen
        if land_id in selected:
            selected.remove(land_id)
        else:
            selected.append(land_id)
    
    # Menü neu anzeigen
    await select_countries(update, context)


async def config_devices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Geräte-Anzahl wählen"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    config = user_configs.get(user_id, {"laender": [], "adult": False, "geraete": 1})
    
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ 1 Gerät" if config["geraete"] == 1 else "1 Gerät",
                callback_data="set_devices_1"
            ),
            InlineKeyboardButton(
                "✅ 2 Geräte" if config["geraete"] == 2 else "2 Geräte",
                callback_data="set_devices_2"
            )
        ],
        [InlineKeyboardButton("➡️ Weiter", callback_data="config_adult")],
        [InlineKeyboardButton("« Zurück", callback_data="select_countries")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📱 *Wie viele Geräte gleichzeitig?*\n\n"
        "💰 *Preise:*\n"
        "• 1 Gerät: 100€/Jahr\n"
        "• 2 Geräte: 150€/Jahr\n\n"
        "_(Länder-Anzahl beeinflusst den Preis nicht!)_",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def set_devices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Geräte-Anzahl setzen"""
    query = update.callback_query
    user_id = query.from_user.id
    
    devices = int(query.data.replace("set_devices_", ""))
    
    if user_id not in user_configs:
        user_configs[user_id] = {"laender": [], "adult": False, "geraete": 1}
    
    user_configs[user_id]["geraete"] = devices
    
    await config_devices(update, context)


async def config_adult(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """18+ Addon konfigurieren"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    config = user_configs.get(user_id, {"laender": [], "adult": False, "geraete": 1})
    
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Nein" if not config["adult"] else "Nein",
                callback_data="toggle_adult_no"
            ),
            InlineKeyboardButton(
                "✅ Ja (+9,99€)" if config["adult"] else "Ja (+9,99€)",
                callback_data="toggle_adult_yes"
            )
        ],
        [InlineKeyboardButton("➡️ Zusammenfassung anzeigen", callback_data="show_summary")],
        [InlineKeyboardButton("« Zurück", callback_data="config_devices")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔞 *18+ Inhalte hinzufügen?*\n\n"
        "📺 Zusätzliche Sender:\n"
        "• 500+ Adult-Kanäle\n"
        "• Verschiedene Kategorien\n"
        "• Diskret & sicher\n\n"
        "💰 Nur +9,99€/Jahr extra\n\n"
        "⚠️ _Nur für Erwachsene (18+)_",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def toggle_adult(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """18+ Option an/ausschalten"""
    query = update.callback_query
    user_id = query.from_user.id
    
    choice = "yes" in query.data
    
    if user_id not in user_configs:
        user_configs[user_id] = {"laender": [], "adult": False, "geraete": 1}
    
    user_configs[user_id]["adult"] = choice
    
    await config_adult(update, context)


async def show_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Zeige Zusammenfassung & Preis"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    config = user_configs.get(user_id, {"laender": [], "adult": False, "geraete": 1})
    
    # Berechne Details
    laender = config["laender"]
    adult = config["adult"]
    geraete = config["geraete"]
    
    # Länder-Text
    if len(laender) >= 10:
        laender_text = "🌎 ALLE Länder (50+)\n📺 ~10.000 Kanäle"
    else:
        laender_namen = [f"{LAENDER[l]['emoji']} {LAENDER[l]['name'].split(' ')[1]}" for l in laender if l in LAENDER]
        total_kanäle = sum(LAENDER[l]["kanäle"] for l in laender if l in LAENDER)
        laender_text = "\n".join(laender_namen) + f"\n\n📺 ~{total_kanäle:,} Kanäle"
    
    # Preis berechnen (LAUNCH SPECIAL: 20% Rabatt!)
    # Gültig für erste 50 Kunden oder ersten Monat
    if geraete == 1:
        basis_preis = 63.99  # Basic Launch (statt 79,99€)
    else:
        basis_preis = 79.99  # Premium Launch (statt 99,99€)
    
    adult_preis = 9.99 if adult else 0  # 18+ Addon
    gesamt_preis = basis_preis + adult_preis
    
    # Zusammenfassung
    summary_text = (
        "📋 *Deine Konfiguration*\n\n"
        f"*Länder:*\n{laender_text}\n\n"
        f"*Geräte:* {geraete} {'Gerät' if geraete == 1 else 'Geräte'}\n"
        f"*18+ Inhalte:* {'✅ Ja' if adult else '❌ Nein'}\n\n"
        "💰 *Preis-Übersicht:*\n"
        f"• Basis ({geraete} {'Gerät' if geraete == 1 else 'Geräte'}): {basis_preis:.2f}€\n"
    )
    
    if adult:
        summary_text += f"• 18+ Addon: {adult_preis:.2f}€\n"
    
    summary_text += (
        f"━━━━━━━━━━━━━━\n"
        f"*Gesamt: {gesamt_preis:.2f}€/Jahr*\n\n"
        "✅ HD & 4K Qualität\n"
        "✅ Alle Geräte unterstützt\n"
        "✅ 24/7 Support\n"
        "✅ Sofortiger Zugang"
    )
    
    keyboard = [
        [InlineKeyboardButton("💳 Jetzt kaufen", callback_data="checkout")],
        [InlineKeyboardButton("🧪 Erst 24h testen", callback_data="request_test")],
        [InlineKeyboardButton("✏️ Ändern", callback_data="select_countries")],
        [InlineKeyboardButton("« Zurück", callback_data="config_adult")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        summary_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Zur Zahlung weiterleiten"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    config = user_configs.get(user_id, {"laender": [], "adult": False, "geraete": 1})
    
    # Berechne Preis
    geraete = config["geraete"]
    adult = config["adult"]
    
    if geraete == 1:
        basis_preis = 63.99  # Basic Launch
    else:
        basis_preis = 79.99  # Premium Launch
    
    gesamt_preis = basis_preis + (9.99 if adult else 0)
    
    # Stripe Links basierend auf Preis (LAUNCH SPECIAL!)
    stripe_links = {
        63.99: "https://buy.stripe.com/LINK_BASIC_LAUNCH",         # Basic Launch
        73.98: "https://buy.stripe.com/LINK_BASIC_18_LAUNCH",      # Basic + 18+ Launch
        79.99: "https://buy.stripe.com/LINK_PREMIUM_LAUNCH",       # Premium Launch
        89.98: "https://buy.stripe.com/LINK_PREMIUM_18_LAUNCH"     # Premium + 18+ Launch
    }
    
    stripe_link = stripe_links.get(gesamt_preis, "https://buy.stripe.com/7sY00lbe02cU2Vr9vWa7C00")
    
    # Benachrichtige Admin mit Config
    laender_text = ", ".join([LAENDER[l]["name"].split()[1] for l in config["laender"] if l in LAENDER])
    if len(config["laender"]) >= 10:
        laender_text = "ALLE Länder"
    
    # User-Info sammeln
    user = query.from_user
    user_info = []
    user_info.append(f"👤 Name: {user.first_name}" + (f" {user.last_name}" if user.last_name else ""))
    if user.username:
        user_info.append(f"📱 Username: @{user.username}")
    user_info.append(f"🆔 User ID: `{user_id}`")
    if user.language_code:
        user_info.append(f"🌍 Sprache: {user.language_code.upper()}")
    
    # Direktlink zum Chat
    user_link = f"tg://user?id={user_id}"
    
    for admin_id in ADMIN_CHAT_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"💳 *Neue Bestellung*\n\n"
                     f"{''.join([line + chr(10) for line in user_info])}\n"
                     f"[👉 Chat öffnen]({user_link})\n\n"
                     f"*Konfiguration:*\n"
                     f"Länder: {laender_text}\n"
                     f"Geräte: {geraete}\n"
                     f"18+: {'Ja' if adult else 'Nein'}\n\n"
                     f"*Preis: {gesamt_preis:.2f}€/Jahr*",
                parse_mode='Markdown'
            )
        except:
            pass
    
    keyboard = [
        [InlineKeyboardButton("💳 Mit Kreditkarte zahlen (Stripe)", url=stripe_link)],
        [InlineKeyboardButton("💰 Mit PayPal zahlen", callback_data="pay_paypal")],
        [InlineKeyboardButton("« Zurück", callback_data="show_summary")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"💳 *Zur Zahlung*\n\n"
        f"Gesamtpreis: *{gesamt_preis:.2f}€/Jahr*\n\n"
        f"Wähle deine Zahlungsmethode:\n\n"
        f"Nach erfolgreicher Zahlung erhältst du:\n"
        f"✅ Sofortigen Zugang\n"
        f"✅ Login-Daten per Telegram\n"
        f"✅ Setup-Anleitung\n"
        f"✅ 24/7 Support",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def pay_paypal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """PayPal Zahlung"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    config = user_configs.get(user_id, {"laender": [], "adult": False, "geraete": 1})
    
    # Berechne Preis
    geraete = config["geraete"]
    adult = config["adult"]
    
    if geraete == 1:
        basis_preis = 63.99  # Basic Launch
    else:
        basis_preis = 79.99  # Premium Launch
    
    gesamt_preis = basis_preis + (9.99 if adult else 0)
    
    keyboard = [
        [InlineKeyboardButton("« Zurück", callback_data="checkout")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"💰 *PayPal Zahlung*\n\n"
        f"Gesamtbetrag: *{gesamt_preis:.2f}€*\n\n"
        f"Sende den Betrag hier:\n"
        f"https://paypal.me/DEIN_PAYPAL_LINK/{int(gesamt_preis)}\n\n"
        f"_Trage deinen PayPal.me Link oben ein!_\n\n"
        f"Nach Zahlung schreib mir bitte:\n"
        f"✅ \"Habe {gesamt_preis:.2f}€ gezahlt\"\n"
        f"📧 Deine PayPal Email-Adresse\n\n"
        f"Dann aktiviere ich deinen Account sofort! ⚡",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def show_packages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fertige Pakete anzeigen"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🇩🇪 Nur Deutschland (100€)", callback_data="pkg_de")],
        [InlineKeyboardButton("🇹🇷 Nur Türkei (100€)", callback_data="pkg_tr")],
        [InlineKeyboardButton("🇩🇪🇹🇷 DE + TR (100€)", callback_data="pkg_de_tr")],
        [InlineKeyboardButton("🌎 Alle Länder (100€)", callback_data="pkg_all")],
        [InlineKeyboardButton("🎨 Eigene Auswahl", callback_data="select_countries")],
        [InlineKeyboardButton("« Zurück", callback_data="back_to_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📦 *Fertige Pakete*\n\n"
        "Schnell & einfach - wähle ein Paket!\n\n"
        "💡 Oder stelle dein eigenes Paket zusammen!",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def request_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """24h Test anfragen"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    keyboard = [[InlineKeyboardButton("« Zurück", callback_data="back_to_start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🧪 *Testversion angefordert!*\n\n"
        "Ein Admin wird dir gleich deine 24h-Testversion zusenden.\n\n"
        "📺 Du bekommst:\n"
        "✓ Voller Zugang zu allen Kanälen\n"
        "✓ 24 Stunden gültig\n"
        "✓ 1 Gerät gleichzeitig\n\n"
        "⏰ Dauert ca. 5-10 Minuten",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    # User-Info sammeln
    user_info = []
    user_info.append(f"👤 Name: {user.first_name}" + (f" {user.last_name}" if user.last_name else ""))
    if user.username:
        user_info.append(f"📱 Username: @{user.username}")
    user_info.append(f"🆔 User ID: `{user.id}`")
    if user.language_code:
        user_info.append(f"🌍 Sprache: {user.language_code.upper()}")
    
    # Direktlink zum Chat
    user_link = f"tg://user?id={user.id}"
    
    for admin_id in ADMIN_CHAT_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"🆕 *Neue Testanfrage*\n\n"
                     f"{''.join([line + chr(10) for line in user_info])}\n"
                     f"[👉 Chat öffnen]({user_link})",
                parse_mode='Markdown'
            )
        except:
            pass


async def show_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """FAQ anzeigen"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔥 Fire TV Stick Setup", callback_data="faq_firetv")],
        [InlineKeyboardButton("📱 Welche Apps?", callback_data="faq_apps")],
        [InlineKeyboardButton("🔧 Wie einrichten?", callback_data="faq_setup")],
        [InlineKeyboardButton("📺 Welche Kanäle?", callback_data="faq_channels")],
        [InlineKeyboardButton("« Zurück", callback_data="back_to_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "❓ *Häufig gestellte Fragen*\n\nWähle ein Thema:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def faq_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Zeige spezifische FAQ-Antworten"""
    query = update.callback_query
    await query.answer()
    
    faq_type = query.data.replace("faq_", "")
    
    keyboard = [[InlineKeyboardButton("« Zurück zu FAQ", callback_data="show_faq")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if faq_type == "firetv":
        text = (
            "🔥 *Fire TV Stick Installation*\n\n"
            "**App:** IBO Player (kostenlos!)\n"
            "**Dauer:** 5-10 Minuten\n"
            "**Code:** 511693\n\n"
            "📋 *Quick-Anleitung:*\n\n"
            "1️⃣ Entwickleroptionen aktivieren\n"
            "→ Einstellungen → Mein Fire TV\n"
            "→ Apps aus unbekannten Quellen: EIN\n\n"
            "2️⃣ Downloader App installieren\n"
            "→ In Suche \"Downloader\" eingeben\n\n"
            "3️⃣ IBO Player laden\n"
            "→ Code eingeben: *511693*\n"
            "→ Installieren\n"
            "→ Datei löschen (Speicher sparen!)\n\n"
            "4️⃣ Zugangsdaten eingeben\n"
            "→ M3U URL oder Xtream Codes\n"
            "→ Deine Daten (bekommst du nach Kauf)\n\n"
            "💡 *PRO-TIPP:*\n"
            "Nutze keyboard.amazonfiretvapp.com\n"
            "auf deinem Handy zum einfacheren\n"
            "Eingeben der URL!\n\n"
            "📖 *Komplette Anleitung mit Video:*\n"
            "premiumip-tv.de/fire-tv-anleitung.html\n\n"
            "🎬 *Video-Tutorial:*\n"
            "youtube.com/watch?v=XeMAkuzPZyc\n"
            "(Code im Video ist alt - nutze 511693!)"
        )
    
    elif faq_type == "apps":
        text = (
            "📱 *Empfohlene Apps*\n\n"
            "**Android/Fire TV:**\n"
            "• IBO Player (⭐ Empfohlen für Fire TV!)\n"
            "• IPTV Smarters Pro\n"
            "• TiviMate\n"
            "• GSE Smart IPTV\n\n"
            "**iOS/Apple TV:**\n"
            "• IPTV Smarters Pro\n"
            "• GSE Smart IPTV\n"
            "• iPlayTV\n\n"
            "**Smart TV (Samsung/LG):**\n"
            "• Smart IPTV\n"
            "• SS IPTV\n\n"
            "**PC/Mac:**\n"
            "• VLC Media Player\n"
            "• IPTV Smarters Pro\n"
            "• Perfect Player"
        )
    
    elif faq_type == "setup":
        text = (
            "🔧 *Einrichtung in 4 Schritten*\n\n"
            "**1. App herunterladen**\n"
            "Lade deine gewählte App herunter\n"
            "(im App Store / Play Store)\n\n"
            "**2. App öffnen**\n"
            "Wähle: \"Login with Xtream Codes\"\n"
            "oder \"M3U URL\" (je nach App)\n\n"
            "**3. Daten eingeben**\n"
            "• Server URL (bekommst du von uns)\n"
            "• Username (bekommst du von uns)\n"
            "• Password (bekommst du von uns)\n\n"
            "**4. Fertig!**\n"
            "Alle Kanäle laden automatisch! 🎉\n\n"
            "🔥 *Fire TV Stick Anleitung:*\n"
            "premiumip-tv.de/fire-tv-anleitung.html\n\n"
            "Bei Problemen einfach hier schreiben!"
        )
    
    elif faq_type == "channels":
        text = (
            "📺 *Verfügbare Kanäle*\n\n"
            "**Deutschland (~500):**\n"
            "ARD, ZDF, RTL, ProSieben, Sat.1, VOX,\n"
            "Sport1, Sky Sport DE, DAZN DE, uvm.\n\n"
            "**Türkei (~350):**\n"
            "TRT, Show TV, Star TV, ATV, Kanal D,\n"
            "Fox TR, beIN Sports TR, uvm.\n\n"
            "**UK (~400):**\n"
            "BBC, ITV, Channel 4, Sky Sports UK,\n"
            "BT Sport, Premier League, uvm.\n\n"
            "**USA (~600):**\n"
            "ESPN, HBO, CNN, Fox News, NBC,\n"
            "Discovery, National Geographic, uvm.\n\n"
            "**+ 46 weitere Länder!**\n"
            "Frankreich, Spanien, Italien, Arabisch,\n"
            "Polen, Niederlande, und viele mehr!\n\n"
            "💡 Insgesamt über 10.000 Kanäle!"
        )
    
    else:
        text = "Diese FAQ-Seite ist noch in Arbeit! 🔧"
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Zurück zum Hauptmenü"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🌍 Länder auswählen", callback_data="select_countries")],
        [InlineKeyboardButton("📦 Fertige Pakete", callback_data="show_packages")],
        [InlineKeyboardButton("🧪 24h Testversion", callback_data="request_test")],
        [InlineKeyboardButton("❓ Hilfe & FAQ", callback_data="show_faq")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "👋 *Willkommen bei Premium IPTV!*\n\n"
        "🎬 Über 10.000 Kanäle in HD & 4K\n"
        "📺 50+ Länder verfügbar\n"
        "💰 Flexibel konfigurierbar\n\n"
        "🎯 *Wie möchtest du starten?*",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def quick_package(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler für fertige Pakete"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    package_type = query.data.replace("pkg_", "")
    
    # Initialize user config
    if user_id not in user_configs:
        user_configs[user_id] = {"laender": [], "adult": False, "geraete": 1}
    
    # Setze Länder basierend auf Paket
    if package_type == "de":
        user_configs[user_id]["laender"] = ["de"]
    elif package_type == "tr":
        user_configs[user_id]["laender"] = ["tr"]
    elif package_type == "de_tr":
        user_configs[user_id]["laender"] = ["de", "tr"]
    elif package_type == "all":
        user_configs[user_id]["laender"] = list(LAENDER.keys())
    
    # Standard: 1 Gerät, kein 18+
    user_configs[user_id]["geraete"] = 1
    user_configs[user_id]["adult"] = False
    
    # Zeige Geräte-Auswahl
    await config_devices(update, context)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler für alle Button-Clicks"""
    query = update.callback_query
    
    # Country Selection
    if query.data == "select_countries":
        await select_countries(update, context)
    elif query.data.startswith("toggle_country_"):
        await toggle_country(update, context)
    
    # Device Config
    elif query.data == "config_devices":
        await config_devices(update, context)
    elif query.data.startswith("set_devices_"):
        await set_devices(update, context)
    
    # Adult Config
    elif query.data == "config_adult":
        await config_adult(update, context)
    elif query.data.startswith("toggle_adult_"):
        await toggle_adult(update, context)
    
    # Summary & Checkout
    elif query.data == "show_summary":
        await show_summary(update, context)
    elif query.data == "checkout":
        await checkout(update, context)
    elif query.data == "pay_paypal":
        await pay_paypal(update, context)
    
    # Packages
    elif query.data == "show_packages":
        await show_packages(update, context)
    elif query.data.startswith("pkg_"):
        await quick_package(update, context)
    
    # Other
    elif query.data == "request_test":
        await request_test(update, context)
    elif query.data == "show_faq":
        await show_faq(update, context)
    elif query.data.startswith("faq_"):
        await faq_handler(update, context)
    elif query.data == "back_to_start":
        await back_to_start(update, context)
    
    else:
        await query.answer("Diese Funktion kommt bald!")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler für Textnachrichten - KI-Antworten"""
    user_message = update.message.text
    user_name = update.effective_user.first_name
    
    print(f"[{user_name}] {user_message}")
    
    try:
        await update.message.chat.send_action(action="typing")
        
        response = anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            system=f"""Du bist ein freundlicher Support-Agent für Premium IPTV.

Wichtige Info:
- Pakete: 1 Gerät = 100€, 2 Geräte = 150€
- 50+ Länder verfügbar (Deutschland, Türkei, UK, USA, etc.)
- 18+ Addon: +9,99€
- Alle Geräte unterstützt
- HD & 4K Qualität

Bei Fragen zu Preisen oder Paketen → Empfehle /start für interaktive Auswahl!

Antworte kurz (max 150 Wörter), freundlich, auf Deutsch. Der User heißt {user_name}.""",
            messages=[{"role": "user", "content": user_message}]
        )
        
        bot_reply = response.content[0].text
        print(f"[BOT] {bot_reply[:100]}...")
        
        # Füge Menü-Button hinzu
        if any(word in user_message.lower() for word in ['preis', 'kosten', 'paket', 'kaufen', 'länder']):
            keyboard = [[InlineKeyboardButton("🌍 Länder auswählen", callback_data="select_countries")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(bot_reply, reply_markup=reply_markup)
        else:
            await update.message.reply_text(bot_reply)
        
    except Exception as e:
        print(f"FEHLER: {e}")
        await update.message.reply_text(
            "😕 Entschuldigung, da ist etwas schiefgelaufen.\n"
            "Nutze /start für das Hauptmenü!"
        )


def main():
    """Bot starten"""
    
    if not TELEGRAM_BOT_TOKEN or not ANTHROPIC_API_KEY:
        print("❌ ERROR: Environment Variables nicht gesetzt!")
        return
    
    print("🔑 Environment Variables geladen")
    
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .pool_timeout(30.0)
        .build()
    )
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("firetv", firetv_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Premium IPTV Support Bot gestartet...")
    print("🌍 Mit Länder-Auswahl aktiviert!")
    print("🔞 Mit 18+ Option aktiviert!")
    print("Bot ist online und wartet auf Nachrichten!")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
