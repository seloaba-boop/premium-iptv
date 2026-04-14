# 🤖 Auto-Poster Setup — Schritt für Schritt

Der Auto-Poster (`channel_auto_poster.py`) postet automatisch 2x täglich in deinen Telegram-Kanal und schickt dir morgens ein Briefing.

## ⏱️ Setup dauert: 10 Minuten

---

## Schritt 1 — Bot zum Kanal als Admin hinzufügen (2 Min)

1. Öffne Telegram → gehe zu **@premium_tv_deutschland**
2. Klicke auf den Kanal-Namen oben → **Administratoren** → **Administrator hinzufügen**
3. Suche: **@premiumiptv_support_bot** (oder dein Bot-Username)
4. Aktiviere diese Rechte:
   - ✅ **Nachrichten posten**
   - ✅ **Nachrichten bearbeiten**
   - ✅ **Nachrichten löschen**
   - ✅ **Nachrichten anpinnen**
5. Speichern.

---

## Schritt 2 — Deine Telegram-User-ID rausfinden (1 Min)

Du brauchst deine numerische User-ID damit NUR du die Admin-Commands ausführen kannst.

1. Öffne Telegram → suche **@userinfobot**
2. Sende `/start`
3. Er antwortet mit deiner ID (z.B. `Your ID: 123456789`)
4. Notiere die Zahl.

---

## Schritt 3 — Railway konfigurieren (5 Min)

1. Gehe zu [railway.app/dashboard](https://railway.app/dashboard) → dein `premium-iptv`-Projekt
2. Klicke **"+ New"** → **"Empty Service"** → nenne es **`poster`**
3. Verbinde es mit demselben GitHub-Repo (`seloaba-boop/premium-iptv`)
4. **Settings** → **Start Command:** `python channel_auto_poster.py`
5. **Variables** → füge hinzu:

| Variable | Wert |
|---|---|
| `CHANNEL_BOT_TOKEN` | (derselbe Bot-Token wie beim Haupt-Bot) |
| `CHANNEL_ID` | `@premium_tv_deutschland` |
| `ADMIN_CHAT_ID` | (deine User-ID aus Schritt 2) |

6. **Deploy** drücken.
7. Nach ~1 Min solltest du in den Logs sehen: `Auto-Poster gestartet. Post-Zeiten: ...`

---

## Schritt 4 — Testen (2 Min)

Schreibe dem **@premiumiptv_support_bot** (deinem Haupt-Bot) eine Privatnachricht — aber halt, der Auto-Poster nutzt DENSELBEN Bot.

**Wichtig:** Da beide Services (Haupt-Bot + Poster) mit demselben Token laufen, gibt es einen Konflikt! Zwei `run_polling` auf demselben Token = Error.

### Lösung: 2 Optionen

**Option A (empfohlen):** Zweiten Bot erstellen
1. Telegram → **@BotFather** → `/newbot`
2. Name: z.B. "Premium IPTV Poster"
3. Username: z.B. `premiumiptv_poster_bot`
4. Token kopieren → in Railway als `CHANNEL_BOT_TOKEN` eintragen
5. Diesen neuen Bot als Admin zum Kanal hinzufügen (Schritt 1)

**Option B:** Haupt-Bot umbauen (komplexer — fragen falls nötig)

---

## Schritt 5 — Ersten Post auslösen (1 Min)

Sobald der Poster läuft, schreibe ihm:

- `/next` → postet sofort den nächsten Post aus der Queue
- `/status` → zeigt Queue-Position, Pause-Status
- `/queue` → zeigt nächste 10 geplanten Posts

Du solltest sofort Post #1 in @premium_tv_deutschland sehen — angepinnt.

---

## 📋 Alle Admin-Commands

| Command | Wirkung |
|---|---|
| `/status` | Aktueller Status + nächster Post |
| `/pause` | Auto-Posting stoppen |
| `/resume` | Auto-Posting wieder starten |
| `/skip` | Nächsten Post aus Queue überspringen |
| `/next` | Jetzt sofort den nächsten Post senden |
| `/queue` | Nächste 10 Posts in Queue |
| `/post <text>` | Ad-hoc Post (nicht aus Queue) |
| `/briefing` | Morgen-Briefing jetzt anfordern |

---

## 🕐 Automatische Schedule

- **12:30 Uhr** → Post aus Queue
- **21:00 Uhr** → Post aus Queue (anderer)
- **09:00 Uhr** → Tagesbriefing an dich (DM)
- Zeitzone: Europe/Berlin
- Queue rotiert — nach Post #20 geht's zurück zu #1

---

## 🛠️ Posts bearbeiten oder erweitern

`posts_queue.json` ist eine JSON-Datei mit allen Posts.

Neuen Post hinzufügen:
```json
{
  "id": 21,
  "type": "sport",
  "text": "Dein neuer Post-Text hier..."
}
```

Einfach committen + pushen → beim nächsten Deploy aktiv.

---

## ❓ Troubleshooting

**"Nothing happens"** → Railway-Logs prüfen. Meistens fehlt eine Env-Variable.

**"Bot kann nicht posten"** → Bot ist nicht Admin im Kanal mit Post-Rechten.

**"Briefing kommt nicht"** → `ADMIN_CHAT_ID` falsch gesetzt oder du hast den Poster-Bot noch nie angeschrieben (sende `/start` damit Telegram dich kennt).

**"Doppelter Post"** → Timezone-Problem. Stelle sicher `tzdata` ist installiert (steht in requirements.txt).
