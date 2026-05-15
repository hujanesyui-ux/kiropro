import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8904333919:AAF_BpXXXGCLGH7xwE8f3IfOUS0tbLoiqTo")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:3000")


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
                msg = (
                    f"✅ *Video siap di-download!*\n\n"
                    f"📝 *Judul:* {video_data.get('title', 'N/A')}\n"
                    f"👤 *Author:* @{video_data.get('author', 'N/A')}\n"
                    f"⏱ *Durasi:* {video_data.get('duration', 0)} detik\n\n"
                    f"📥 [Download Video (Normal)]({video_data['download_url']})\n"
                )
                if video_data.get("download_url_hd"):
                    msg += f"📥 [Download Video (HD)]({video_data['download_url_hd']})\n"

                await query.edit_message_text(msg, parse_mode="Markdown", disable_web_page_preview=True)
            else:
                await query.edit_message_text("❌ Gagal mendapatkan link download. Coba lagi nanti.")
        except Exception as e:
            await query.edit_message_text(f"❌ Error: {str(e)}")

    elif action == "download_audio":
        await query.edit_message_text("⏳ Sedang memproses audio...")
        try:
            response = requests.get(f"{API_BASE_URL}/api/audio/download", params={"url": url}, timeout=30)
            data = response.json()

            if data.get("success") and data.get("data", {}).get("download_url"):
                audio_data = data["data"]
                msg = (
                    f"✅ *Audio siap di-download!*\n\n"
                    f"🎵 *Musik:* {audio_data.get('music_title', 'N/A')}\n"
                    f"👤 *Artist:* {audio_data.get('music_author', 'N/A')}\n"
                    f"⏱ *Durasi:* {audio_data.get('duration', 0)} detik\n\n"
                    f"🎵 [Download Audio]({audio_data['download_url']})"
                )
                await query.edit_message_text(msg, parse_mode="Markdown", disable_web_page_preview=True)
            else:
                await query.edit_message_text("❌ Gagal mendapatkan link audio. Coba lagi nanti.")
        except Exception as e:
            await query.edit_message_text(f"❌ Error: {str(e)}")

    elif action == "video_info":
        await query.edit_message_text("⏳ Mengambil info video...")
        try:
            response = requests.get(f"{API_BASE_URL}/api/video/info", params={"url": url}, timeout=30)
            data = response.json()

            if data.get("success"):
                info = data["data"]
                stats = info.get("stats", {})
                author = info.get("author", {})
                msg = (
                    f"📊 *Info Video TikTok*\n\n"
                    f"📝 *Judul:* {info.get('title', 'N/A')}\n"
                    f"👤 *Author:* @{author.get('username', 'N/A')} ({author.get('nickname', '')})\n"
                    f"⏱ *Durasi:* {info.get('duration', 0)} detik\n\n"
                    f"📈 *Statistik:*\n"
                    f"   ▶️ Views: {stats.get('plays', 0):,}\n"
                    f"   ❤️ Likes: {stats.get('likes', 0):,}\n"
                    f"   💬 Comments: {stats.get('comments', 0):,}\n"
                    f"   🔄 Shares: {stats.get('shares', 0):,}"
                )
                await query.edit_message_text(msg, parse_mode="Markdown")
            else:
                await query.edit_message_text("❌ Gagal mendapatkan info video. Coba lagi nanti.")
        except Exception as e:
            await query.edit_message_text(f"❌ Error: {str(e)}")


def main():
    """Start the bot"""
    print("🤖 Starting TikTok Downloader Bot...")

    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tiktok_link))

    print("✅ Bot is running!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
