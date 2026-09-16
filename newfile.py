import asyncio, json, logging, uuid, requests, html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, filters

TOKEN = "8490205113:AAHKG7Bpg4iHTTVf3ahyZvHpbGRNVbp5xaE" #توكن بوتك 
OWNER = 1928255357 # ايديك 
DEV_USERNAME = "@j49_c"

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

class Core:
    def __init__(self):
        self.users = {}
        self.endpoints = {
            "tiktok": "https://www.tikvault.app/api/download",
            "ai": "https://qudata.com/ru/includes/sendmail/chat.php",
            "crypto": "https://api.coingecko.com/api/v3/coins/markets",
            "fx": "https://open.er-api.com/v6/latest/USD",
            "yt": "https://api.vidssave.net/api/yt",
            "short": "https://clck.ru/--",
            "proxy": "https://raw.githubusercontent.com/ALIILAPRO/MTProtoProxy/main/mtproto.txt"
        }
        self.coins = {
            "bitcoin": ("BTC", "Bitcoin", "₿"),
            "solana": ("SOL", "Solana", "◎"),
            "the-open-network": ("TON", "Toncoin", "💎")
        }

    def get_user(self, uid):
        if uid not in self.users:
            self.users[uid] = {"points": 0, "invites": 0}
        return self.users[uid]

    def tiktok_download(self, url):
        try:
            r = requests.post(self.endpoints["tiktok"], json={"url": url}, headers={"content-type": "application/json", "user-agent": "Mozilla/5.0"}, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.error(f"TikTok error: {e}")
            return None

    def ai_chat(self, message):
        try:
            payload = {
                "message": message,
                "dialogs[0][role]": "user",
                "dialogs[0][content]": message,
                "userid": uuid.uuid4().hex
            }
            r = requests.post(self.endpoints["ai"], data=payload, timeout=30)
            r.raise_for_status()
            return r.text
        except Exception as e:
            logger.error(f"AI error: {e}")
            return None

    def crypto_data(self):
        try:
            fx = requests.get(self.endpoints["fx"], timeout=10).json()
            iqd = fx["rates"]["IQD"]
            params = {"vs_currency": "usd", "ids": ",".join(self.coins.keys())}
            r = requests.get(self.endpoints["crypto"], params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            lines = []
            for c in data:
                k = c["id"]
                sym, name, icon = self.coins[k]
                p = c["current_price"]
                ch = c["price_change_percentage_24h"] or 0
                mc = c["market_cap"]
                vol = c["total_volume"]
                emoji = "🟢" if ch > 0 else "🔴" if ch < 0 else "⚪"
                lines.append(f"{icon} {name} ({sym})\nPrice: ${p:,.2f} | {p*iqd:,.0f} IQD\n24h: {emoji} {ch:.2f}%\nCap: ${mc:,.0f}\nVol: ${vol:,.0f}")
            return "\n\n".join(lines)
        except Exception as e:
            logger.error(f"Crypto error: {e}")
            return None

    def youtube_download(self, url):
        try:
            r = requests.get(f"{self.endpoints['yt']}?url={url}", timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.error(f"YouTube error: {e}")
            return None

    def shorten_url(self, url):
        try:
            r = requests.get(self.endpoints["short"], params={"url": url}, timeout=10)
            r.raise_for_status()
            return r.text
        except Exception as e:
            logger.error(f"Shorten error: {e}")
            return None

    def get_proxies(self):
        try:
            r = requests.get(self.endpoints["proxy"], timeout=10)
            r.raise_for_status()
            return r.text
        except Exception as e:
            logger.error(f"Proxy error: {e}")
            return None

C = Core()

def main_kb():
    return ReplyKeyboardMarkup([
        ["🎬 TikTok", "🤖 AI"],
        ["📥 YouTube", "🔗 Shorten"],
        ["💰 Crypto", "🌐 Proxies"],
        ["📊 My Info", "ℹ️ About"]
    ], resize_keyboard=True)

def cancel_kb():
    return ReplyKeyboardMarkup([["❌ Cancel"]], resize_keyboard=True)

TIKTOK, YOUTUBE, SHORTEN = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    C.get_user(u.id)
    text = f"Welcome {u.mention_html()}!\n\nI am your all-in-one assistant bot.\nDeveloped by {DEV_USERNAME}"
    await update.message.reply_html(text, reply_markup=main_kb())

async def my_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    info = C.get_user(u.id)
    text = f"Your Info:\nID: <code>{u.id}</code>\nPoints: {info['points']}\nInvites: {info['invites']}"
    await update.message.reply_html(text)

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"Bot Developer: {DEV_USERNAME}\nVersion: 2.0\nFeatures: TikTok, YouTube, AI, Crypto, URL Shortener, MTProto Proxies"
    await update.message.reply_text(text)

async def tiktok_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send TikTok link:", reply_markup=cancel_kb())
    return TIKTOK

async def tiktok_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "❌ Cancel":
        await update.message.reply_text("Cancelled.", reply_markup=main_kb())
        return ConversationHandler.END
    wait = await update.message.reply_text("⏳ Processing your TikTok link...")
    data = C.tiktok_download(text)
    if not data or not data.get("success"):
        await wait.edit_text("❌ Failed to fetch TikTok video.\nPlease check the link and try again.")
        return TIKTOK
    try:
        d = data["data"]
        caption = f"<b>{html.escape(d['title'])}</b>\nBy: {html.escape(d['author']['username'])}\n👁 {d['stats']['plays']:,} | ❤️ {d['stats']['likes']:,} | 💬 {d['stats']['comments']:,}"
        video_url = d["downloads"]["videoHD"] or d["downloads"]["videoSD"]
        audio_url = d["downloads"]["audio"]
        await update.message.reply_video(video=video_url, caption=caption, parse_mode="HTML")
        await update.message.reply_audio(audio=audio_url, title=d["title"])
        await wait.delete()
    except Exception as e:
        logger.error(f"TikTok send error: {e}")
        await wait.edit_text("❌ Error sending media. Try again later.")
    return TIKTOK

async def youtube_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send YouTube link:", reply_markup=cancel_kb())
    return YOUTUBE

async def youtube_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "❌ Cancel":
        await update.message.reply_text("Cancelled.", reply_markup=main_kb())
        return ConversationHandler.END
    wait = await update.message.reply_text("⏳ Processing your YouTube link...")
    data = C.youtube_download(text)
    if not data or data.get("error"):
        await wait.edit_text("❌ Failed to fetch YouTube video.\nPlease check the link and try again.")
        return YOUTUBE
    try:
        medias = data.get("medias", [])
        best = None
        for m in medias:
            if m.get("type") == "video" and m.get("extension") == "mp4":
                if not best or (m.get("height", 0) > best.get("height", 0)):
                    best = m
        if best:
            url = best.get("url_proxy") or best.get("url")
            title = html.escape(data.get("title", "YouTube Video"))
            await update.message.reply_video(video=url, caption=f"{title}\n\nQuality: {best.get('quality','')}", parse_mode="HTML")
            await wait.delete()
        else:
            await wait.edit_text("⚠️ No MP4 video found in this link.")
    except Exception as e:
        logger.error(f"YouTube send error: {e}")
        await wait.edit_text("❌ Error sending video. Try again later.")
    return YOUTUBE

async def shorten_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send URL to shorten:", reply_markup=cancel_kb())
    return SHORTEN

async def shorten_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "❌ Cancel":
        await update.message.reply_text("Cancelled.", reply_markup=main_kb())
        return ConversationHandler.END
    wait = await update.message.reply_text("⏳ Shortening URL...")
    result = C.shorten_url(text)
    if not result:
        await wait.edit_text("❌ Failed to shorten URL.\nPlease check the link and try again.")
        return SHORTEN
    await wait.edit_text(f"✅ Shortened URL:\n<code>{result}</code>", parse_mode="HTML")
    return SHORTEN

async def ai_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 AI Mode ON.\nSend your message or press Cancel.", reply_markup=cancel_kb())
    context.user_data["ai_mode"] = True

async def crypto_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wait = await update.message.reply_text("⏳ Fetching crypto prices...")
    data = C.crypto_data()
    if not data:
        await wait.edit_text("❌ Failed to fetch crypto data.\nPlease try again later.")
        return
    await wait.edit_text(data[:4096])

async def proxies_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wait = await update.message.reply_text("⏳ Fetching proxy list...")
    text = C.get_proxies()
    if not text:
        await wait.edit_text("❌ Failed to fetch proxies.\nPlease try again later.")
        return
    lines = [l.strip() for l in text.splitlines() if l.strip().startswith("https://t.me/")]
    if not lines:
        await wait.edit_text("⚠️ No proxies found in the source.")
        return
    chunks = [lines[i:i+10] for i in range(0, len(lines), 10)]
    sent = 0
    for chunk in chunks[:5]:
        try:
            await update.message.reply_text("\n\n".join(chunk))
            sent += 1
        except Exception as e:
            logger.error(f"Proxy send error: {e}")
            break
    if sent == 0:
        await wait.edit_text("❌ Error sending proxies.")
    else:
        await wait.delete()

async def cancel_and_route(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.user_data.pop("ai_mode", None)
    await update.message.reply_text("Operation cancelled.", reply_markup=main_kb())
    if text == "🎬 TikTok":
        return await tiktok_entry(update, context)
    elif text == "📥 YouTube":
        return await youtube_entry(update, context)
    elif text == "🔗 Shorten":
        return await shorten_entry(update, context)
    elif text == "🤖 AI":
        return await ai_trigger(update, context)
    elif text == "💰 Crypto":
        return await crypto_cmd(update, context)
    elif text == "🌐 Proxies":
        return await proxies_cmd(update, context)
    elif text == "📊 My Info":
        return await my_info(update, context)
    elif text == "ℹ️ About":
        return await about(update, context)
    return ConversationHandler.END

async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "❌ Cancel":
        context.user_data.pop("ai_mode", None)
        await update.message.reply_text("Cancelled.", reply_markup=main_kb())
        return
    if text == "🎬 TikTok":
        context.user_data.pop("ai_mode", None)
        return await tiktok_entry(update, context)
    elif text == "📥 YouTube":
        context.user_data.pop("ai_mode", None)
        return await youtube_entry(update, context)
    elif text == "🔗 Shorten":
        context.user_data.pop("ai_mode", None)
        return await shorten_entry(update, context)
    elif text == "🤖 AI":
        return await ai_trigger(update, context)
    elif text == "💰 Crypto":
        context.user_data.pop("ai_mode", None)
        return await crypto_cmd(update, context)
    elif text == "🌐 Proxies":
        context.user_data.pop("ai_mode", None)
        return await proxies_cmd(update, context)
    elif text == "📊 My Info":
        context.user_data.pop("ai_mode", None)
        return await my_info(update, context)
    elif text == "ℹ️ About":
        context.user_data.pop("ai_mode", None)
        return await about(update, context)
    elif context.user_data.get("ai_mode"):
        wait = await update.message.reply_text("🤖 Thinking...")
        res = C.ai_chat(text)
        if not res:
            await wait.edit_text("❌ AI service is unavailable.\nPlease try again later.")
            return
        await wait.edit_text(res[:4096])
        return
    else:
        await update.message.reply_text("Use the buttons below.", reply_markup=main_kb())

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("ai_mode", None)
    await update.message.reply_text("Cancelled.", reply_markup=main_kb())
    return ConversationHandler.END

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text("⚠️ An unexpected error occurred. Please try again.")
        except:
            pass

def main():
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🎬 TikTok$"), tiktok_entry),
            MessageHandler(filters.Regex("^📥 YouTube$"), youtube_entry),
            MessageHandler(filters.Regex("^🔗 Shorten$"), shorten_entry),
        ],
        states={
            TIKTOK: [MessageHandler(filters.TEXT & ~filters.COMMAND, tiktok_handler)],
            YOUTUBE: [MessageHandler(filters.TEXT & ~filters.COMMAND, youtube_handler)],
            SHORTEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, shorten_handler)],
        },
        fallbacks=[
            MessageHandler(filters.Regex("^❌ Cancel$"), cancel),
            MessageHandler(filters.Regex("^(🎬 TikTok|📥 YouTube|🔗 Shorten|🤖 AI|💰 Crypto|🌐 Proxies|📊 My Info|ℹ️ About)$"), cancel_and_route),
            CommandHandler("cancel", cancel)
        ],
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))
    app.add_error_handler(error_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
