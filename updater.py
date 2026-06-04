import os
import urllib.request
import zipfile
import tempfile

BIN_DIR = os.path.join(os.environ.get('APPDATA', ''), 'YoutubePro', 'bin')
YTDLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"
FFMPEG_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"

def check_components():
    yt_dlp_path = os.path.join(BIN_DIR, 'yt-dlp.zip')
    ffmpeg_path = os.path.join(BIN_DIR, 'ffmpeg.exe')
    return os.path.exists(yt_dlp_path) and os.path.exists(ffmpeg_path)

def update_components():
    os.makedirs(BIN_DIR, exist_ok=True)
    
    # 1. yt-dlp indiriyoruz
    yt_dlp_path = os.path.join(BIN_DIR, 'yt-dlp.zip')
    try:
        urllib.request.urlretrieve(YTDLP_URL, yt_dlp_path)
    except Exception as e:
        print(f"yt-dlp indirme hatasi: {e}")
        return False

    # 2. FFmpeg indirip exe'leri çıkartıyoruz
    try:
        temp_zip_path = os.path.join(tempfile.gettempdir(), "ffmpeg_temp.zip")
        urllib.request.urlretrieve(FFMPEG_URL, temp_zip_path)
        
        with zipfile.ZipFile(temp_zip_path, 'r') as z:
            for file_info in z.infolist():
                if file_info.filename.endswith('ffmpeg.exe'):
                    with z.open(file_info) as sf, open(os.path.join(BIN_DIR, 'ffmpeg.exe'), 'wb') as df:
                        df.write(sf.read())
                elif file_info.filename.endswith('ffprobe.exe'):
                    with z.open(file_info) as sf, open(os.path.join(BIN_DIR, 'ffprobe.exe'), 'wb') as df:
                        df.write(sf.read())
                        
        os.remove(temp_zip_path)
    except Exception as e:
        print(f"FFmpeg indirme hatasi: {e}")
        return False
        
    return True
