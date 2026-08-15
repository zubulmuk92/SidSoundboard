import os
import sys
import json
import threading
import subprocess
import socket
from bottle import Bottle, request, response, static_file

from config_manager import load_config, save_config
from audio_manager import AudioManager
from hotkey_manager import HotkeyManager

app = Bottle()

# Configuration and State
config = load_config()
audio_manager = AudioManager()
hotkey_manager = HotkeyManager(audio_manager, config)
hotkey_manager.load_hotkeys(config)

# CORS Helper
def enable_cors(fn):
    def _enable_cors(*args, **kwargs):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'
        if request.method == 'OPTIONS':
            return {}
        return fn(*args, **kwargs)
    return _enable_cors

# --- API ENDPOINTS ---

@app.route('/api/sounds', method=['GET', 'OPTIONS'])
@enable_cors
def get_sounds():
    return {"sounds": config.get('sounds', [])}

@app.route('/api/play', method=['POST', 'OPTIONS'])
@enable_cors
def play_sound():
    data = request.json
    if not data: return {"status": "error"}
    
    filename = data.get('filename')
    volume = data.get('volume', 1.0)
    device_name = data.get('device_name')
    second_device = data.get('second_device')
    audio_ducking = data.get('audio_ducking', False)
    
    # Run in a thread so we don't block the HTTP request
    threading.Thread(target=audio_manager.toggle_play_pause, args=(
        filename, volume, device_name, second_device, audio_ducking
    ), daemon=True).start()
    
    return {"status": "playing"}

@app.route('/api/stop', method=['POST', 'OPTIONS'])
@enable_cors
def stop_all():
    audio_manager.stop_all()
    return {"status": "stopped"}

@app.route('/api/progress', method=['GET', 'OPTIONS'])
@enable_cors
def get_progress():
    progress = audio_manager.get_focused_progress()
    info = audio_manager.focused_info
    return {
        "progress": progress,
        "is_playing": info['is_playing'] if info else False,
        "total_time": info['total_time'] if info else 0,
        "current_time": progress * info['total_time'] if info and progress else 0
    }

# --- STATIC FILES ---
WEB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'v2-web', 'web'))

@app.route('/')
def index():
    return static_file('index.html', root=WEB_DIR)

@app.route('/<filepath:path>')
def serve_static(filepath):
    return static_file(filepath, root=WEB_DIR)

# --- START SERVER & UI ---
def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

if __name__ == '__main__':
    port = get_free_port()
    
    # Start server in background thread
    server_thread = threading.Thread(
        target=app.run,
        kwargs={'host': '127.0.0.1', 'port': port, 'quiet': True},
        daemon=True
    )
    server_thread.start()
    
    # Launch Default Browser
    url = f"http://127.0.0.1:{port}"
    print(f"Server running at {url}")
    
    import webbrowser
    webbrowser.open(url)
    
    # Keep main thread alive
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        hotkey_manager.shutdown()
        audio_manager.stop_all()
