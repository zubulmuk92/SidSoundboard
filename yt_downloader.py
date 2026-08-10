import yt_dlp
import static_ffmpeg
import os
import threading

def download_youtube_audio_async(url, output_dir, callback, progress_callback):
    def worker():
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            static_ffmpeg.add_paths()
            
            def yt_progress_hook(d):
                if d['status'] == 'downloading':
                    percent_str = d.get('_percent_str', '0%').strip()
                    # ANSI escape codes might be in percent_str, yt-dlp removes them in clean strings but just in case
                    import re
                    percent_str = re.sub(r'\x1b[^m]*m', '', percent_str)
                    
                    # Infos playlist
                    info = d.get('info_dict', {})
                    p_index = info.get('playlist_index')
                    p_count = info.get('playlist_count')
                    title = info.get('title', 'Unknown')
                    
                    progress_callback(percent_str, p_index, p_count, title)

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'no_warnings': True,
                'progress_hooks': [yt_progress_hook]
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                
                results = []
                # Gestion Single vs Playlist
                if 'entries' in info_dict:
                    entries = info_dict['entries']
                else:
                    entries = [info_dict]
                    
                for entry in entries:
                    if not entry: continue
                    file_path = ydl.prepare_filename(entry)
                    final_path = os.path.splitext(file_path)[0] + '.mp3'
                    title = entry.get('title', 'Unknown')
                    if os.path.exists(final_path):
                        results.append((final_path, title))
                        
                callback(True, results, "")
        except Exception as e:
            callback(False, None, str(e))
            
    threading.Thread(target=worker, daemon=True).start()
