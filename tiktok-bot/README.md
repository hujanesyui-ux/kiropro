# 🎬 TikTok Bot

Bot untuk download video TikTok tanpa watermark, download audio, dan lihat info video.

Terdiri dari:
- **REST API** (Node.js/Express) - Backend endpoints
- **Telegram Bot** (Python) - Interface chat di Telegram

---

## 📁 Struktur Project

```
tiktok-bot/
├── api/                    # REST API (Node.js)
│   ├── index.js           # Main server
│   ├── package.json       # Dependencies
│   └── .env.example       # Environment variables
├── telegram-bot/           # Telegram Bot (Python)
│   ├── bot.py             # Main bot
│   ├── requirements.txt   # Dependencies
│   └── .env.example       # Environment variables
└── README.md              # Dokumentasi ini
```

---

## 🚀 Setup & Menjalankan

### 1. REST API (Node.js)

```bash
cd api

# Install dependencies
npm install

# Jalankan server
npm start

# Atau development mode
npm run dev
```

API akan berjalan di `http://localhost:3000`

### 2. Telegram Bot (Python)

```bash
cd telegram-bot

# Install dependencies
pip install -r requirements.txt

# Set environment variable (opsional, sudah ada default)
export TELEGRAM_BOT_TOKEN=your_token_here
export API_BASE_URL=http://localhost:3000

# Jalankan bot
python bot.py
```

---

## 📡 API Endpoints

### GET `/`
Welcome message dan daftar endpoint.

### GET `/api/video/info?url=TIKTOK_URL`
Mendapatkan informasi video (judul, author, statistik).

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "video_id",
    "title": "Video title",
    "author": {
      "username": "user123",
      "nickname": "User Name"
    },
    "stats": {
      "plays": 1000000,
      "likes": 50000,
      "comments": 1000,
      "shares": 500
    },
    "duration": 30
  }
}
```

### GET `/api/video/download?url=TIKTOK_URL`
Mendapatkan link download video tanpa watermark.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "video_id",
    "title": "Video title",
    "author": "user123",
    "download_url": "https://...",
    "download_url_hd": "https://...",
    "duration": 30
  }
}
```

### GET `/api/audio/download?url=TIKTOK_URL`
Mendapatkan link download audio dari video.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "video_id",
    "title": "Video title",
    "music_title": "Song Name",
    "music_author": "Artist",
    "download_url": "https://...",
    "duration": 30
  }
}
```

---

## 🤖 Telegram Bot Commands

| Command | Deskripsi |
|---------|-----------|
| `/start` | Tampilkan pesan welcome |
| `/help` | Bantuan penggunaan |

**Cara pakai:** Cukup kirim link TikTok, lalu pilih opsi yang diinginkan!

---

## ⚠️ Catatan

- API menggunakan layanan pihak ketiga (tikwm.com) untuk mendapatkan link download
- Pastikan REST API sudah berjalan sebelum menjalankan Telegram Bot
- Bot token yang disertakan harus diganti jika dipublish ke publik

---

## 📝 License

MIT
