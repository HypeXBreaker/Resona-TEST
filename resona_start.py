from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import threading
import yt_dlp
import os

app = Flask(__name__, static_folder='.')
CORS(app)

# =========================
# GLOBAL STATE
# =========================
queue = []
now_playing = None
thumbnail = None
lock = threading.Lock()

# =========================
# YT-DLP OPTIONS (SEARCH ONLY)
# =========================
YDL_OPTS = {
    'quiet': True,
    'noplaylist': True,
    'extract_flat': True  # 🔥 VERY IMPORTANT (no streaming)
}

def search_song(song_name):
    """Search YouTube and return video info (NO AUDIO STREAMING)"""
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        info = ydl.extract_info(f"ytsearch1:{song_name}", download=False)
        entry = info['entries'][0]

        return {
            "title": entry.get("title"),
            "video_id": entry.get("id"),
            "thumbnail": entry.get("thumbnail")
        }

def play_next():
    global now_playing, thumbnail

    with lock:
        if queue:
            song = queue.pop(0)
            result = search_song(song)
            now_playing = result
            thumbnail = result["thumbnail"]
        else:
            now_playing = None
            thumbnail = None

# =========================
# ROUTES
# =========================
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/add', methods=['POST'])
def add_song():
    global now_playing, thumbnail   # 🔥 THIS WAS MISSING

    data = request.json
    song = data.get('song')

    if not song:
        return jsonify(success=False)

    with lock:
        if now_playing is None:
            result = search_song(song)
            now_playing = result
            thumbnail = result["thumbnail"]
        else:
            queue.append(song)

    return jsonify(success=True)

@app.route('/next', methods=['POST'])
def next_song():
    play_next()
    return jsonify(success=True)

@app.route('/queue')
def get_queue():
    return jsonify({
        "now_playing": now_playing,
        "queue": queue,
        "thumbnail": thumbnail
    })

# =========================
# START SERVER
# =========================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
