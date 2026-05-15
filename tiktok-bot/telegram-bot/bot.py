import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8904333919:AAF_BpXXXGCLGH7xwE8f3IfOUS0tbLoiqTo")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:3000")


def escape_md(text) -> str:
    """Escape special Markdown characters to prevent parse errors"""
    if text is None:
        return "N/A"
    text = str(text)
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def is_tiktok_url(text: str) -> bool:
    """Check if text contains a TikTok URL"""
    tiktok_domains = ["tiktok.com", "vm.tiktok.com", "vt.tiktok.com"]
    return any(domain in text for domain in tiktok_domains)


def extract_url(text: str) -> str:
    """Extract URL from message text"""
    words = text.split()
    for word in words:
        if "tiktok.com" in word:
            return word
    return text.strip()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_msg = (
        "🎬 *TikTok Downloader Bot*\n\n"
        "Kirim link TikTok dan saya akan bantu kamu:\n\n"
        "📥 Download video tanpa watermark\n"
        "🎵 Download audio/musik\n"
        "📊 Lihat info video\n\n"
        "*Cara pakai:*\n"
        "Cukup kirim/paste link TikTok ke sini!\n\n"
        "*Commands:*\n"
        "/start - Tampilkan pesan ini\n"
        "/help - Bantuan penggunaan"
    )
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_msg = (
        "📖 *Bantuan Penggunaan*\n\n"
        "1. Copy link video TikTok\n"
        "2. Paste/kirim ke bot ini\n"
        "3. Pilih opsi yang kamu mau:\n"
        "   • 📥 Download Video (tanpa watermark)\n"
        "   • 🎵 Download Audio\n"
        "   • 📊 Info Video\n\n"
        "*Format link yang didukung:*\n"
        "• https://www.tiktok.com/@user/video/123456\n"
        "• https://vm.tiktok.com/abc123\n"
        "• https://vt.tiktok.com/abc123\n\n"
        "Kalau ada error, coba kirim ulang linknya ya! 😊"
    )
    await update.message.reply_text(help_msg, parse_mode="Markdown")


async def handle_tiktok_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming TikTok links"""
    text = update.message.text

    if not is_tiktok_url(text):
        await update.message.reply_text(
            "❌ Itu bukan link TikTok yang valid.\n"
            "Kirim link TikTok untuk download video! 🎬"
        )
        return

    url = extract_url(text)

    # Store URL in context for callback
    context.user_data["tiktok_url"] = url

    # Show options
    keyboard = [
        [
            InlineKeyboardButton("📥 Download Video", callback_data="download_video"),
            InlineKeyboardButton("🎵 Download Audio", callback_data="download_audio"),
        ],
        [
            InlineKeyboardButton("📊 Info Video", callback_data="video_info"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🎬 *Link TikTok terdeteksi!*\n\nPilih yang mau kamu lakukan:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()

    url = context.user_data.get("tiktok_url")
    if not url:
        await query.edit_message_text("❌ Link tidak ditemukan. Kirim ulang link TikTok ya!")
        return

    action = query.data

    if action == "download_video":
        await query.edit_message_text("⏳ Sedang memproses video...")
        try:
            response = requests.get(f"{API_BASE_URL}/api/video/download", params={"url": url}, timeout=30)
            data = response.json()

            if data.get("success") and data.get("data", {}).get("download_url"):
                video_data = data["data"]
                title = escape_md(video_data.get('title', 'N/A'))
                author = escape_md(video_data.get('author', 'N/A'))
                duration = escape_md(video_data.get('duration', 0))
                download_url = video_data['download_url']
                msg = (
                    f"✅ *Video siap di\\-download\\!*\n\n"
                    f"📝 *Judul:* {title}\n"
                    f"👤 *Author:* @{author}\n"
                    f"⏱ *Durasi:* {duration} detik\n\n"
                    f"📥 [Download Video \\(Normal\\)]({download_url})\n"
                )
                if video_data.get("download_url_hd"):
                    msg += f"📥 [Download Video \\(HD\\)]({video_data['download_url_hd']})\n"

                await query.edit_message_text(msg, parse_mode="MarkdownV2", disable_web_page_preview=True)
            else:
                await query.edit_message_text("❌ Gagal mendapatkan link download. Coba lagi nanti.")
        except Exception as e:
            await query.edit_message_text(f"❌ Error: {escape_md(str(e))}", parse_mode=None)

    elif action == "download_audio":
        await query.edit_message_text("⏳ Sedang memproses audio...")
        try:
            response = requests.get(f"{API_BASE_URL}/api/audio/download", params={"url": url}, timeout=30)
            data = response.json()

            if data.get("success") and data.get("data", {}).get("download_url"):
                audio_data = data["data"]
                music_title = escape_md(audio_data.get('music_title', 'N/A'))
                music_author = escape_md(audio_data.get('music_author', 'N/A'))
                duration = escape_md(audio_data.get('duration', 0))
                download_url = audio_data['download_url']
                msg = (
                    f"✅ *Audio siap di\\-download\\!*\n\n"
                    f"🎵 *Musik:* {music_title}\n"
                    f"👤 *Artist:* {music_author}\n"
                    f"⏱ *Durasi:* {duration} detik\n\n"
                    f"🎵 [Download Audio]({download_url})"
                )
                await query.edit_message_text(msg, parse_mode="MarkdownV2", disable_web_page_preview=True)
            else:
                await query.edit_message_text("❌ Gagal mendapatkan link audio. Coba lagi nanti.")
        except Exception as e:
            await query.edit_message_text(f"❌ Error: {escape_md(str(e))}", parse_mode=None)

    elif action == "video_info":
        await query.edit_message_text("⏳ Mengambil info video...")
        try:
            response = requests.get(f"{API_BASE_URL}/api/video/info", params={"url": url}, timeout=30)
            data = response.json()

            if data.get("success"):
                info = data["data"]
                stats = info.get("stats", {})
                author = info.get("author", {})
                title = escape_md(info.get('title', 'N/A'))
                username = escape_md(author.get('username', 'N/A'))
                nickname = escape_md(author.get('nickname', ''))
                duration = escape_md(info.get('duration', 0))
                plays = escape_md(f"{stats.get('plays', 0):,}")
                likes = escape_md(f"{stats.get('likes', 0):,}")
                comments = escape_md(f"{stats.get('comments', 0):,}")
                shares = escape_md(f"{stats.get('shares', 0):,}")
                msg = (
                    f"📊 *Info Video TikTok*\n\n"
                    f"📝 *Judul:* {title}\n"
                    f"👤 *Author:* @{username} \\({nickname}\\)\n"
                    f"⏱ *Durasi:* {duration} detik\n\n"
                    f"📈 *Statistik:*\n"
                    f"   ▶️ Views: {plays}\n"
                    f"   ❤️ Likes: {likes}\n"
                    f"   💬 Comments: {comments}\n"
                    f"   🔄 Shares: {shares}"
                )
                await query.edit_message_text(msg, parse_mode="MarkdownV2")
            else:
                await query.edit_message_text("❌ Gagal mendapatkan info video. Coba lagi nanti.")
        except Exception as e:
            await query.edit_message_text(f"❌ Error: {escape_md(str(e))}", parse_mode=None)


async def main():
    """Start the bot"""
    print("🤖 Starting TikTok Downloader Bot...")

    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tiktok_link))

    print("✅ Bot is running!")

    async with app:
        await app.start()
        await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        # Keep running until interrupted
        import asyncio
        stop_event = asyncio.Event()
        try:
            await stop_event.wait()
        except (KeyboardInterrupt, SystemExit):
            pass
        finally:
            await app.updater.stop()
            await app.stop()


if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n👋 Bot stopped.")
