import os
import re
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


def is_tiktok_profile(text: str) -> bool:
    """Check if text is a TikTok profile URL or @username"""
    text = text.strip()
    # Check @username format
    if re.match(r'^@[\w.]+$', text):
        return True
    # Check profile URL format (no /video/ in it)
    if "tiktok.com/@" in text and "/video/" not in text:
        return True
    return False


def extract_username(text: str) -> str:
    """Extract username from profile URL or @username"""
    text = text.strip()
    # @username format
    if text.startswith('@'):
        return text[1:]
    # URL format: https://tiktok.com/@username or https://www.tiktok.com/@username
    match = re.search(r'tiktok\.com/@([\w.]+)', text)
    if match:
        return match.group(1)
    return text.replace('@', '')


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
        "📊 Lihat info video\n"
        "👤 Download semua video dari profil\n\n"
        "*Cara pakai:*\n"
        "• Kirim link video TikTok\n"
        "• Kirim @username atau link profil untuk bulk download\n\n"
        "*Commands:*\n"
        "/start - Tampilkan pesan ini\n"
        "/help - Bantuan penggunaan"
    )
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_msg = (
        "📖 *Bantuan Penggunaan*\n\n"
        "*Download Video:*\n"
        "Kirim link video TikTok → pilih opsi\n\n"
        "*Bulk Download Profil:*\n"
        "Kirim `@username` atau link profil TikTok\n"
        "Bot akan ambil semua video dari user tersebut\n\n"
        "*Format yang didukung:*\n"
        "• https://www.tiktok.com/@user/video/123456\n"
        "• https://vm.tiktok.com/abc123\n"
        "• https://www.tiktok.com/@username\n"
        "• @username\n\n"
        "Kalau ada error, coba kirim ulang ya! 😊"
    )
    await update.message.reply_text(help_msg, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages - detect video links or profile"""
    text = update.message.text.strip()

    # Check if it's a profile/username
    if is_tiktok_profile(text):
        await handle_profile(update, context, text)
        return

    # Check if it's a TikTok video link
    if is_tiktok_url(text):
        await handle_tiktok_link(update, context, text)
        return

    # Check if it's just @username without tiktok URL
    if text.startswith('@') and len(text) > 1:
        await handle_profile(update, context, text)
        return

    await update.message.reply_text(
        "❌ Itu bukan link TikTok atau username yang valid.\n\n"
        "Kirim:\n"
        "• Link video TikTok untuk download\n"
        "• @username atau link profil untuk bulk download 🎬"
    )


async def handle_tiktok_link(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle incoming TikTok video links"""
    url = extract_url(text)
    context.user_data["tiktok_url"] = url

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


async def handle_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle TikTok profile/username - fetch video list"""
    username = extract_username(text)
    context.user_data["profile_username"] = username
    context.user_data["profile_cursor"] = 0

    await update.message.reply_text(f"👤 Mengambil video dari @{username}...")

    try:
        response = requests.get(
            f"{API_BASE_URL}/api/user/videos",
            params={"username": username, "cursor": 0},
            timeout=30
        )
        data = response.json()

        if data.get("success") and data.get("data", {}).get("videos"):
            videos = data["data"]["videos"]
            has_more = data["data"].get("has_more", False)
            cursor = data["data"].get("cursor", 0)

            # Store videos in context
            context.user_data["profile_videos"] = videos
            context.user_data["profile_cursor"] = cursor
            context.user_data["profile_has_more"] = has_more
            context.user_data["profile_page"] = 1

            # Build video list message
            msg = f"👤 *Profil @{escape_md(username)}*\n"
            msg += f"📹 Ditemukan {escape_md(str(len(videos)))} video\n\n"

            for i, video in enumerate(videos[:10], 1):
                title = video.get('title', 'No caption')[:40]
                duration = video.get('duration', 0)
                plays = video.get('stats', {}).get('plays', 0)
                msg += f"{escape_md(str(i))}\\. {escape_md(title)}\n"
                msg += f"   ⏱ {escape_md(str(duration))}s \\| ▶️ {escape_md(f'{plays:,}')} views\n\n"

            if len(videos) > 10:
                msg += f"\\.\\.\\. dan {escape_md(str(len(videos) - 10))} video lainnya\n"

            # Build buttons
            buttons = [
                [InlineKeyboardButton("📥 Download Semua", callback_data="profile_download_all")],
                [InlineKeyboardButton("📋 Lihat Daftar Video", callback_data="profile_list_0")],
            ]
            if has_more:
                buttons.append([InlineKeyboardButton("➡️ Next Page", callback_data="profile_next")])

            reply_markup = InlineKeyboardMarkup(buttons)
            await update.message.reply_text(msg, parse_mode="MarkdownV2", reply_markup=reply_markup)
        else:
            await update.message.reply_text(
                f"❌ Tidak bisa mengambil video dari @{username}.\n"
                "Pastikan username benar dan akun tidak private."
            )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()

    action = query.data

    # === PROFILE ACTIONS ===
    if action == "profile_download_all":
        await handle_profile_download_all(query, context)
        return

    if action.startswith("profile_list_"):
        await handle_profile_list(query, context)
        return

    if action == "profile_next":
        await handle_profile_next(query, context)
        return

    if action.startswith("profile_dl_"):
        await handle_profile_download_single(query, context)
        return

    # === SINGLE VIDEO ACTIONS ===
    url = context.user_data.get("tiktok_url")
    if not url:
        await query.edit_message_text("❌ Link tidak ditemukan. Kirim ulang link TikTok ya!")
        return

    if action == "download_video":
        await query.edit_message_text("⏳ Sedang memproses video...")
        try:
            response = requests.get(f"{API_BASE_URL}/api/video/download", params={"url": url}, timeout=30)
            data = response.json()

            if data.get("success") and data.get("data", {}).get("download_url"):
                video_data = data["data"]
                download_url = video_data.get("download_url_hd") or video_data["download_url"]
                title = video_data.get('title', 'TikTok Video')
                author = video_data.get('author', 'unknown')

                await query.edit_message_text("📥 Mengirim video...")
                try:
                    await query.message.reply_video(
                        video=download_url,
                        caption=f"📝 {title}\n👤 @{author}",
                        supports_streaming=True
                    )
                    await query.delete_message()
                except Exception:
                    title_escaped = escape_md(title)
                    author_escaped = escape_md(author)
                    duration = escape_md(video_data.get('duration', 0))
                    msg = (
                        f"✅ *Video siap di\\-download\\!*\n\n"
                        f"📝 *Judul:* {title_escaped}\n"
                        f"👤 *Author:* @{author_escaped}\n"
                        f"⏱ *Durasi:* {duration} detik\n\n"
                        f"📥 [Download Video]({download_url})"
                    )
                    await query.edit_message_text(msg, parse_mode="MarkdownV2", disable_web_page_preview=True)
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
                download_url = audio_data['download_url']
                music_title = audio_data.get('music_title', 'TikTok Audio')
                music_author = audio_data.get('music_author', 'unknown')

                await query.edit_message_text("🎵 Mengirim audio...")
                try:
                    await query.message.reply_audio(
                        audio=download_url,
                        title=music_title,
                        performer=music_author
                    )
                    await query.delete_message()
                except Exception:
                    music_title_escaped = escape_md(music_title)
                    music_author_escaped = escape_md(music_author)
                    duration = escape_md(audio_data.get('duration', 0))
                    msg = (
                        f"✅ *Audio siap di\\-download\\!*\n\n"
                        f"🎵 *Musik:* {music_title_escaped}\n"
                        f"👤 *Artist:* {music_author_escaped}\n"
                        f"⏱ *Durasi:* {duration} detik\n\n"
                        f"🎵 [Download Audio]({download_url})"
                    )
                    await query.edit_message_text(msg, parse_mode="MarkdownV2", disable_web_page_preview=True)
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
            await query.edit_message_text(f"❌ Error: {str(e)}")


async def handle_profile_download_all(query, context: ContextTypes.DEFAULT_TYPE):
    """Download all videos from profile one by one"""
    videos = context.user_data.get("profile_videos", [])
    username = context.user_data.get("profile_username", "unknown")

    if not videos:
        await query.edit_message_text("❌ Tidak ada video untuk didownload.")
        return

    await query.edit_message_text(
        f"📥 Mengirim {len(videos)} video dari @{username}...\n"
        f"⏳ Mohon tunggu, ini mungkin butuh waktu."
    )

    success_count = 0
    fail_count = 0

    for i, video in enumerate(videos):
        download_url = video.get("download_url_hd") or video.get("download_url")
        title = video.get("title", f"Video {i+1}")[:50]

        if not download_url:
            fail_count += 1
            continue

        try:
            await query.message.reply_video(
                video=download_url,
                caption=f"📥 [{i+1}/{len(videos)}] {title}\n👤 @{username}",
                supports_streaming=True,
                read_timeout=60,
                write_timeout=60
            )
            success_count += 1
        except Exception:
            # Fallback: send as link
            try:
                await query.message.reply_text(
                    f"📥 [{i+1}/{len(videos)}] {title}\n"
                    f"👤 @{username}\n"
                    f"🔗 {download_url}",
                    disable_web_page_preview=True
                )
                success_count += 1
            except Exception:
                fail_count += 1

    # Summary
    await query.message.reply_text(
        f"✅ Selesai!\n\n"
        f"📊 Hasil download dari @{username}:\n"
        f"✅ Berhasil: {success_count}\n"
        f"❌ Gagal: {fail_count}\n"
        f"📹 Total: {len(videos)}"
    )


async def handle_profile_list(query, context: ContextTypes.DEFAULT_TYPE):
    """Show paginated video list with individual download buttons"""
    videos = context.user_data.get("profile_videos", [])
    username = context.user_data.get("profile_username", "unknown")

    # Get page offset from callback data
    offset = int(query.data.replace("profile_list_", ""))
    page_size = 5
    page_videos = videos[offset:offset + page_size]

    if not page_videos:
        await query.edit_message_text("❌ Tidak ada video lagi.")
        return

    msg = f"📋 *Daftar Video @{escape_md(username)}*\n"
    msg += f"📄 Halaman {escape_md(str(offset // page_size + 1))}\n\n"

    buttons = []
    for i, video in enumerate(page_videos):
        idx = offset + i
        title = video.get('title', 'No caption')[:35]
        duration = video.get('duration', 0)
        plays = video.get('stats', {}).get('plays', 0)
        msg += f"{escape_md(str(idx + 1))}\\. {escape_md(title)}\n"
        msg += f"   ⏱ {escape_md(str(duration))}s \\| ▶️ {escape_md(f'{plays:,}')}\n\n"
        buttons.append([InlineKeyboardButton(f"📥 Download #{idx + 1}", callback_data=f"profile_dl_{idx}")])

    # Navigation buttons
    nav_buttons = []
    if offset > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"profile_list_{offset - page_size}"))
    if offset + page_size < len(videos):
        nav_buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f"profile_list_{offset + page_size}"))
    if nav_buttons:
        buttons.append(nav_buttons)

    buttons.append([InlineKeyboardButton("📥 Download Semua", callback_data="profile_download_all")])

    reply_markup = InlineKeyboardMarkup(buttons)
    await query.edit_message_text(msg, parse_mode="MarkdownV2", reply_markup=reply_markup)


async def handle_profile_next(query, context: ContextTypes.DEFAULT_TYPE):
    """Load next page of videos from profile"""
    username = context.user_data.get("profile_username")
    cursor = context.user_data.get("profile_cursor", 0)

    if not username:
        await query.edit_message_text("❌ Username tidak ditemukan. Kirim ulang ya!")
        return

    await query.edit_message_text(f"⏳ Memuat video selanjutnya dari @{username}...")

    try:
        response = requests.get(
            f"{API_BASE_URL}/api/user/videos",
            params={"username": username, "cursor": cursor},
            timeout=30
        )
        data = response.json()

        if data.get("success") and data.get("data", {}).get("videos"):
            new_videos = data["data"]["videos"]
            has_more = data["data"].get("has_more", False)
            new_cursor = data["data"].get("cursor", 0)

            # Append to existing videos
            existing_videos = context.user_data.get("profile_videos", [])
            existing_videos.extend(new_videos)
            context.user_data["profile_videos"] = existing_videos
            context.user_data["profile_cursor"] = new_cursor
            context.user_data["profile_has_more"] = has_more

            page = context.user_data.get("profile_page", 1) + 1
            context.user_data["profile_page"] = page

            msg = f"👤 *@{escape_md(username)}* \\- Page {escape_md(str(page))}\n"
            msg += f"📹 \\+{escape_md(str(len(new_videos)))} video dimuat \\(total: {escape_md(str(len(existing_videos)))}\\)\n\n"

            for i, video in enumerate(new_videos[:10], 1):
                title = video.get('title', 'No caption')[:40]
                duration = video.get('duration', 0)
                plays = video.get('stats', {}).get('plays', 0)
                msg += f"{escape_md(str(i))}\\. {escape_md(title)}\n"
                msg += f"   ⏱ {escape_md(str(duration))}s \\| ▶️ {escape_md(f'{plays:,}')} views\n\n"

            buttons = [
                [InlineKeyboardButton("📥 Download Semua", callback_data="profile_download_all")],
                [InlineKeyboardButton("📋 Lihat Daftar Video", callback_data="profile_list_0")],
            ]
            if has_more:
                buttons.append([InlineKeyboardButton("➡️ Next Page", callback_data="profile_next")])

            reply_markup = InlineKeyboardMarkup(buttons)
            await query.edit_message_text(msg, parse_mode="MarkdownV2", reply_markup=reply_markup)
        else:
            await query.edit_message_text("❌ Tidak ada video lagi dari user ini.")
    except Exception as e:
        await query.edit_message_text(f"❌ Error: {str(e)}")


async def handle_profile_download_single(query, context: ContextTypes.DEFAULT_TYPE):
    """Download a single video from the profile list"""
    videos = context.user_data.get("profile_videos", [])
    username = context.user_data.get("profile_username", "unknown")

    idx = int(query.data.replace("profile_dl_", ""))

    if idx >= len(videos):
        await query.answer("❌ Video tidak ditemukan", show_alert=True)
        return

    video = videos[idx]
    download_url = video.get("download_url_hd") or video.get("download_url")
    title = video.get("title", f"Video {idx + 1}")[:50]

    if not download_url:
        await query.answer("❌ Link download tidak tersedia", show_alert=True)
        return

    await query.answer(f"📥 Mendownload video #{idx + 1}...")

    try:
        await query.message.reply_video(
            video=download_url,
            caption=f"📥 {title}\n👤 @{username}",
            supports_streaming=True,
            read_timeout=60,
            write_timeout=60
        )
    except Exception:
        # Fallback: send as link
        await query.message.reply_text(
            f"📥 {title}\n"
            f"👤 @{username}\n"
            f"🔗 {download_url}",
            disable_web_page_preview=True
        )


async def main():
    """Start the bot"""
    print("🤖 Starting TikTok Downloader Bot...")

    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot is running!")

    async with app:
        await app.start()
        await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
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
