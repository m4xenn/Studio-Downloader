import sys
import os

# --- DINAMIK MODUL YUKLEME ---
BIN_DIR = os.path.join(os.environ.get('APPDATA', ''), 'YoutubePro', 'bin')
YTDLP_ZIP = os.path.join(BIN_DIR, 'yt-dlp.zip')
if os.path.exists(YTDLP_ZIP):
    sys.path.insert(0, YTDLP_ZIP)
# -----------------------------

from flask import Flask, render_template, request, jsonify
import threading
import subprocess
import platform
import time
import tkinter as tk
from tkinter import filedialog
import updater

if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    # If static folder exists in the future, it can be passed here as well
    # static_folder = os.path.join(sys._MEIPASS, 'static')
    app = Flask(__name__, template_folder=template_folder)
else:
    app = Flask(__name__)


# Varsayılan yol boş
current_download_path = ""
current_lang = "tr"
# İndirme Durumu
download_status = {
    "percent": 0, 
    "status": "idle", 
    "error": "", 
    "current_item": 0, 
    "total_items": 0
}

# Çeviriler (Python tarafı)
py_i18n = {
    "tr": {
        "success": "İndirme işlemi başarıyla tamamlandı!",
        "err_link": "Link hatalı, kilitli veya yayın şu anda çevrimdışı.",
        "err_folder": "Klasör Seçilmedi!",
        "err_empty": "Liste boş!",
        "unknown_vid": "Bilinmeyen Video/Liste",
        "unknown_link": "Bilinmeyen Bağlantı (İndirilebilir)"
    },
    "en": {
        "success": "Download completed successfully!",
        "err_link": "Invalid link, locked, or stream offline.",
        "err_folder": "No folder selected!",
        "err_empty": "Queue is empty!",
        "unknown_vid": "Unknown Video/Playlist",
        "unknown_link": "Unknown Link (Downloadable)"
    },
    "es": { "success": "¡Descarga completada con éxito!", "err_link": "Enlace inválido, bloqueado o transmisión fuera de línea.", "err_folder": "¡No se seleccionó ninguna carpeta!", "err_empty": "¡La cola está vacía!", "unknown_vid": "Video/Lista Desconocida", "unknown_link": "Enlace Desconocido" },
    "fr": { "success": "Téléchargement terminé avec succès !", "err_link": "Lien invalide, verrouillé ou flux hors ligne.", "err_folder": "Aucun dossier sélectionné !", "err_empty": "La file d'attente est vide !", "unknown_vid": "Vidéo/Playlist inconnue", "unknown_link": "Lien Inconnu" },
    "de": { "success": "Download erfolgreich abgeschlossen!", "err_link": "Ungültiger Link, gesperrt oder Stream offline.", "err_folder": "Kein Ordner ausgewählt!", "err_empty": "Warteschlange ist leer!", "unknown_vid": "Unbekanntes Video/Playlist", "unknown_link": "Unbekannter Link" },
    "ru": { "success": "Скачивание успешно завершено!", "err_link": "Неверная ссылка, заблокирована или трансляция оффлайн.", "err_folder": "Папка не выбрана!", "err_empty": "Очередь пуста!", "unknown_vid": "Неизвестное видео/плейлист", "unknown_link": "Неизвестная ссылка" },
    "pt": { "success": "Download concluído com sucesso!", "err_link": "Link inválido, bloqueado ou stream offline.", "err_folder": "Nenhuma pasta selecionada!", "err_empty": "A fila está vazia!", "unknown_vid": "Vídeo/Playlist Desconhecido", "unknown_link": "Link Desconhecido" },
    "zh": { "success": "下载成功完成！", "err_link": "链接无效、被锁定或直播离线。", "err_folder": "未选择文件夹！", "err_empty": "队列为空！", "unknown_vid": "未知的视频/播放列表", "unknown_link": "未知的链接" },
    "ja": { "success": "ダウンロードが正常に完了しました！", "err_link": "無効なリンク、ロックされている、またはストリームがオフラインです。", "err_folder": "フォルダが選択されていません！", "err_empty": "キューが空です！", "unknown_vid": "不明なビデオ/プレイリスト", "unknown_link": "不明なリンク" },
    "hi": { "success": "डाउनलोड सफलतापूर्वक पूरा हुआ!", "err_link": "अवैध लिंक, लॉक किया गया, या स्ट्रीम ऑफ़लाइन।", "err_folder": "कोई फ़ोल्डर नहीं चुना गया!", "err_empty": "कतार खाली है!", "unknown_vid": "अज्ञात वीडियो/प्लेलिस्ट", "unknown_link": "अज्ञात लिंक" }
}

def get_i18n(key):
    lang = current_lang if current_lang in py_i18n else "en"
    return py_i18n[lang].get(key, py_i18n["en"].get(key, key))

# --- AKILLI KLASÖR SEÇİCİ ---
def open_folder_dialog():
    system_name = platform.system()
    if system_name == "Darwin": # macOS
        try:
            script = 'choose folder with prompt "Lütfen İndirme Konumunu Seçin"'
            proc = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
            if proc.returncode == 0:
                mac_path = proc.stdout.strip().replace("alias ", "")
                posix_script = f'POSIX path of "{mac_path}"'
                proc_posix = subprocess.run(['osascript', '-e', posix_script], capture_output=True, text=True)
                return proc_posix.stdout.strip()
        except Exception as e:
            print(f"Mac Dialog Hatası: {e}")
            return None
    else: # Windows
        try:
            root = tk.Tk()
            root.withdraw()
            root.wm_attributes('-topmost', 1)
            folder_selected = filedialog.askdirectory()
            root.destroy()
            return folder_selected
        except Exception as e:
            print(f"Windows Dialog Hatası: {e}")
            return None
    return None

def show_notification(title, message):
    if platform.system() != "Windows": return
    import threading
    def _notify():
        try:
            import win32gui, win32con, win32api
            wc = win32gui.WNDCLASS()
            hinst = wc.hInstance = win32api.GetModuleHandle(None)
            wc.lpszClassName = "YoutubeProNotifyTaskbar"
            
            def wndproc(hwnd, msg, wparam, lparam):
                if msg == win32con.WM_DESTROY:
                    win32gui.PostQuitMessage(0)
                elif msg == win32con.WM_TIMER:
                    win32gui.DestroyWindow(hwnd)
                return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
                
            wc.lpfnWndProc = wndproc
            try: win32gui.RegisterClass(wc)
            except: pass
            
            hwnd = win32gui.CreateWindow(wc.lpszClassName, "Taskbar", win32con.WS_OVERLAPPED, 0, 0, 0, 0, 0, 0, hinst, None)
            
            try: hicon = win32gui.LoadIcon(hinst, 1)
            except: hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
            
            flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP
            nid = (hwnd, 0, flags, win32con.WM_USER+20, hicon, "YoutubePro")
            win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
            win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, (hwnd, 0, win32gui.NIF_INFO, win32con.WM_USER+20, hicon, "Tooltip", message, 200, title, 1))
            
            # Start a timer to kill it securely instead of blocking
            try:
                import win32ui
                win32gui.SetTimer(hwnd, 1, 6000, 0)
            except:
                import time
                threading.Thread(target=lambda: (time.sleep(6), win32gui.DestroyWindow(hwnd))).start()
                
            win32gui.PumpMessages()
            
            try: win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (hwnd, 0))
            except: pass
        except Exception as e:
            print("Native Notify Error:", e)
    
    threading.Thread(target=_notify, daemon=True).start()

def progress_hook(d):
    global download_status
    if d['status'] == 'downloading':
        try:
            playlist_index = d.get('playlist_index')
            playlist_count = d.get('playlist_count')
            if playlist_index and playlist_count:
                download_status["current_item"] = playlist_index
                download_status["total_items"] = playlist_count

            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            if total:
                percent = (downloaded / total) * 100
                download_status["percent"] = round(percent, 1)
                download_status["status"] = "downloading"
        except: pass
    elif d['status'] == 'finished':
        download_status["percent"] = 100
        download_status["status"] = "converting"

def run_download(urls, format_type, quality, save_path, is_playlist):
    global download_status
    download_status = {"percent": 0, "status": "starting", "error": "", "current_item": 0, "total_items": len(urls)}
    
    if len(urls) > 1 and not is_playlist:
        save_path = os.path.join(save_path, "Toplu_Indirmeler")
        os.makedirs(save_path, exist_ok=True)

    try:
        from yt_dlp import YoutubeDL
        
        ydl_opts = {
            'progress_hooks': [progress_hook],
            'ignoreerrors': True,
            'verbose': False,
            'nocheckcertificate': True,
            'extract_flat': False,
            'concurrent_fragment_downloads': 10,
            'ffmpeg_location': BIN_DIR,
            'writethumbnail': True,
        }

        if is_playlist:
            ydl_opts['outtmpl'] = os.path.join(save_path, '%(playlist_title)s', '%(title)s.%(ext)s')
            ydl_opts['noplaylist'] = False
        else:
            ydl_opts['outtmpl'] = os.path.join(save_path, '%(title)s.%(ext)s')
            ydl_opts['noplaylist'] = True

        if format_type == 'audio':
            target_codec = quality if quality in ['mp3', 'm4a', 'wav', 'opus'] else 'mp3'
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': target_codec,
                    'preferredquality': '192',
                },
                {'key': 'FFmpegMetadata'},
            ]
            # WAV dosyaları Resim/ID3 Kapak Fotoğrafı desteklemediği için FFmpeg çöker ve resimleri asılı bırakır!
            if target_codec in ['mp3', 'm4a', 'opus']:
                ydl_opts['postprocessors'].append({'key': 'FFmpegThumbnailsConvertor', 'format': 'png'})
                ydl_opts['postprocessors'].append({'key': 'EmbedThumbnail'})
                ydl_opts['postprocessor_args'] = {
                    'embedthumbnail+ffmpeg_o': [
                        '-c:v', 'mjpeg',
                        '-vf', "crop='if(gt(ih,iw),iw,ih)':'if(gt(iw,ih),ih,iw)'"
                    ]
                }
            else:
                ydl_opts['writethumbnail'] = False
        else:
            if quality == '8k': ydl_opts['format'] = 'bestvideo[height<=4320]+bestaudio/best'
            elif quality == '4k': ydl_opts['format'] = 'bestvideo[height<=2160]+bestaudio/best'
            elif quality == '1080p': ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best'
            else: ydl_opts['format'] = 'bestvideo+bestaudio/best'
            
            # --- AFTER EFFECTS UYUMLULUK GÜNCELLEMESİ ---
            # Önce birleştirmeyi MP4 olarak dener. 
            ydl_opts['merge_output_format'] = 'mp4'
            
            # Eğer video VP9 gibi After Effects'in açamadığı bir formatta gelmişse,
            # FFmpeg'e "Bunu zorla standart bir MP4 (H.264) yap" emrini verir.
            if 'postprocessors' not in ydl_opts:
                ydl_opts['postprocessors'] = []
                
            ydl_opts['postprocessors'].append({
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            })
            
            ydl_opts['postprocessors'].append({'key': 'FFmpegMetadata'})
            # Thumbnail embedding for video is removed to prevent mp4 ffmpeg errors
            # --------------------------------------------

        for index, url in enumerate(urls):
            if not is_playlist:
                download_status["current_item"] = index + 1
            
            download_status["percent"] = 0
            download_status["status"] = "starting"
            
            with YoutubeDL(ydl_opts) as ydl:
                retcode = ydl.download([url])
                if retcode != 0:
                    raise Exception(get_i18n("err_link"))
                
            time.sleep(0.5)

        download_status["status"] = "finished_all"
        show_notification("YoutubePro", get_i18n("success"))
            
    except Exception as e:
        print(f"HATA: {e}")
        download_status["status"] = "error"
        download_status["error"] = str(e)

@app.route('/get-info', methods=['POST'])
def get_info():
    url = request.json.get('url')
    try:
        from yt_dlp import YoutubeDL
        
        opts = {'quiet': True, 'extract_flat': True, 'nocheckcertificate': True}
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', get_i18n("unknown_vid"))
            
            thumbs = info.get('thumbnails', [])
            thumb_url = "https://via.placeholder.com/120x68/2c2c2e/86868b?text=Video"
            if thumbs:
                thumb_url = thumbs[-1].get('url', thumb_url)
                
            return jsonify({"status": "success", "title": title, "thumbnail": thumb_url, "url": url})
    except Exception as e:
        return jsonify({"status": "success", "title": get_i18n("unknown_link"), "thumbnail": "https://via.placeholder.com/120x68/2c2c2e/86868b?text=Link", "url": url})

@app.route('/set-lang', methods=['POST'])
def set_lang():
    global current_lang
    lang = request.json.get('lang')
    if lang:
        current_lang = lang
    return jsonify({"status": "success"})

@app.route('/')
def home():
    return render_template('index.html', default_path="Lütfen Klasör Seçiniz...")

@app.route('/select-folder', methods=['POST'])
def select_folder():
    global current_download_path
    path = open_folder_dialog()
    if path:
        current_download_path = path
        return jsonify({"status": "success", "path": path})
    return jsonify({"status": "cancel", "path": current_download_path if current_download_path else "Lütfen Klasör Seçiniz..."})

@app.route('/progress')
def get_progress():
    return jsonify(download_status)

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    urls = data.get('urls')
    
    if not current_download_path: return jsonify({"status": "error", "message": get_i18n("err_folder")}), 400
    if not urls or len(urls) == 0: return jsonify({"status": "error", "message": get_i18n("err_empty")}), 400

    thread = threading.Thread(target=run_download, args=(
        urls, 
        data.get('format'), 
        data.get('quality'), 
        current_download_path, 
        data.get('is_playlist')
    ))
    thread.daemon = True
    thread.start()
    return jsonify({"status": "success"})

@app.route('/check-components')
def get_check_components():
    return jsonify({"ready": updater.check_components()})

@app.route('/update-components', methods=['POST'])
def post_update_components():
    success = updater.update_components()
    return jsonify({"status": "success" if success else "error"})

if __name__ == '__main__':
    app.run(debug=True)