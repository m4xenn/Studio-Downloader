import webview
import sys
import os

# app.py'den Flask uygulamamızı içe aktarıyoruz
from app import app

def start_window():
    # Uygulama başlığını ve başlangıç sayfası özelliklerini ayarlıyoruz
    window = webview.create_window(
        'YoutubePro Downloader', 
        app, 
        width=900, 
        height=750, 
        resizable=True,
        min_size=(600, 500)
    )
    
    # Masaüstü penceresi başlatılıyor
    webview.start()

if __name__ == '__main__':
    # freeze support
    import multiprocessing
    multiprocessing.freeze_support()
    
    start_window()
