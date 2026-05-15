const express = require('express');
const cors = require('cors');
const axios = require('axios');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// Helper: Extract TikTok video ID from URL
async function getVideoId(url) {
  try {
    // Follow redirects for short URLs (vm.tiktok.com)
    const response = await axios.get(url, {
      maxRedirects: 5,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      }
    });
    const finalUrl = response.request.res.responseUrl || url;
    const match = finalUrl.match(/\/video\/(\d+)/);
    return match ? match[1] : null;
  } catch (error) {
    const match = url.match(/\/video\/(\d+)/);
    return match ? match[1] : null;
  }
}

// Helper: Get TikTok video data using unofficial API
async function getVideoData(url) {
  try {
    const videoId = await getVideoId(url);
    if (!videoId) {
      throw new Error('Could not extract video ID from URL');
    }

    // Use TikTok's oEmbed API for basic info
    const oembedUrl = `https://www.tiktok.com/oembed?url=${encodeURIComponent(url)}`;
    const oembedRes = await axios.get(oembedUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      }
    });

    // Use tikwm.com API for download links
    const tikwmRes = await axios.get(`https://www.tikwm.com/api/?url=${encodeURIComponent(url)}`, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      }
    });

    if (tikwmRes.data && tikwmRes.data.data) {
      return {
        success: true,
        videoId,
        oembed: oembedRes.data,
        data: tikwmRes.data.data
      };
    }

    throw new Error('Failed to fetch video data');
  } catch (error) {
    throw error;
  }
}

// ============ ROUTES ============

// GET / - Welcome
app.get('/', (req, res) => {
  res.json({
    status: 'ok',
    message: 'TikTok Bot API',
    endpoints: {
      '/api/video/info': 'GET - Get video info (query: url)',
      '/api/video/download': 'GET - Download video no watermark (query: url)',
      '/api/audio/download': 'GET - Download audio (query: url)'
    }
  });
});

// GET /api/video/info - Get video information
app.get('/api/video/info', async (req, res) => {
  try {
    const { url } = req.query;
    if (!url) {
      return res.status(400).json({ success: false, error: 'URL parameter is required' });
    }

    const videoData = await getVideoData(url);
    const data = videoData.data;

    res.json({
      success: true,
      data: {
        id: videoData.videoId,
        title: data.title || videoData.oembed.title,
        author: {
          username: data.author?.unique_id || videoData.oembed.author_name,
          nickname: data.author?.nickname || '',
          avatar: data.author?.avatar || ''
        },
        stats: {
          plays: data.play_count || 0,
          likes: data.digg_count || 0,
          comments: data.comment_count || 0,
          shares: data.share_count || 0
        },
        duration: data.duration || 0,
        cover: data.cover || videoData.oembed.thumbnail_url,
        created_at: data.create_time || null
      }
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// GET /api/video/download - Download video without watermark
app.get('/api/video/download', async (req, res) => {
  try {
    const { url } = req.query;
    if (!url) {
      return res.status(400).json({ success: false, error: 'URL parameter is required' });
    }

    const videoData = await getVideoData(url);
    const data = videoData.data;

    res.json({
      success: true,
      data: {
        id: videoData.videoId,
        title: data.title || '',
        author: data.author?.unique_id || '',
        download_url: data.play ? (data.play.startsWith('http') ? data.play : `https://www.tikwm.com${data.play}`) : null,
        download_url_hd: data.hdplay ? (data.hdplay.startsWith('http') ? data.hdplay : `https://www.tikwm.com${data.hdplay}`) : null,
        duration: data.duration || 0
      }
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// GET /api/audio/download - Download audio from video
app.get('/api/audio/download', async (req, res) => {
  try {
    const { url } = req.query;
    if (!url) {
      return res.status(400).json({ success: false, error: 'URL parameter is required' });
    }

    const videoData = await getVideoData(url);
    const data = videoData.data;

    res.json({
      success: true,
      data: {
        id: videoData.videoId,
        title: data.title || '',
        author: data.author?.unique_id || '',
        music_title: data.music_info?.title || data.music || '',
        music_author: data.music_info?.author || '',
        download_url: data.music ? (data.music.startsWith('http') ? data.music : `https://www.tikwm.com${data.music}`) : null,
        duration: data.duration || 0
      }
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`TikTok Bot API running on port ${PORT}`);
});
