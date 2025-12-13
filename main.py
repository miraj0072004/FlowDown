import webview
import threading
import yt_dlp
import os
import sys
import json
import time

class Api:
    def __init__(self):
        self._window = None
        # Default download folder
        self.download_folder = os.path.join(os.path.expanduser("~"), "Downloads", "FlowDown")
        
        # Load config if exists
        try:
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.abspath(__file__))
                
            config_file = os.path.join(app_dir, "config.json")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    cfg = json.load(f)
                    if 'download_folder' in cfg:
                        self.download_folder = cfg['download_folder']
        except Exception as e:
            print(f"Error loading config: {e}")

        if not os.path.exists(self.download_folder):
            os.makedirs(self.download_folder)


    def set_window(self, window):
        self._window = window

    def init(self):
        """Called by frontend on load to get initial state"""
        return {
            'download_folder': self.download_folder
        }

    def choose_directory(self):
        """Open a folder selection dialog and save the choice"""
        if not self._window:
            return None
        
        # Open dialog
        result = self._window.create_file_dialog(webview.FOLDER_DIALOG, directory=self.download_folder)
        
        if result and len(result) > 0:
            new_folder = result[0] # result is a tuple/list
            self.download_folder = new_folder
            
            # Save to config
            self._save_config()
            
            return new_folder
        
        return None

    def _save_config(self):
        try:
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.abspath(__file__))
            
            config_file = os.path.join(app_dir, "config.json")
            with open(config_file, 'w') as f:
                json.dump({'download_folder': self.download_folder}, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def download_video(self, url):
        # Run in a thread to keep UI responsive
        t = threading.Thread(target=self._download_process, args=(url,))
        t.start()
    
    def _download_process(self, url):
        try:
            ydl_opts = {
                'outtmpl': os.path.join(self.download_folder, '%(title)s.%(ext)s'),
                'progress_hooks': [self._progress_hook],
                'quiet': True,
                'no_warnings': True,
                # 'format': 'bestvideo+bestaudio/best', # High quality
            }
            
            if self._window:
                self._window.evaluate_js('updateStatus("Fetching video info...")')

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
            
            # Notify completion
            if self._window:
                # Escape backslashes for JS
                clean_path = filename.replace('\\', '\\\\')
                self._window.evaluate_js(f'downloadComplete("{clean_path}")')
            
            # Open folder
            os.startfile(self.download_folder)

        except Exception as e:
            error_msg = str(e).replace('"', "'").replace('\\', '\\\\')
            if self._window:
                 self._window.evaluate_js(f'downloadError("{error_msg}")')

    def _progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                total = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded = d.get('downloaded_bytes', 0)
                
                if total:
                    percent = (downloaded / total) * 100
                else:
                    percent = 0
                
                if self._window:
                    self._window.evaluate_js(f'updateProgress({percent:.1f})')
                    self._window.evaluate_js(f'updateStatus("Downloading... {percent:.1f}%")')
            except Exception as e:
                print(f"Error in progress hook: {e}")
        
        elif d['status'] == 'finished':
            if self._window:
                 self._window.evaluate_js('updateStatus("Processing...")')
                 self._window.evaluate_js('updateProgress(100)')


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

if __name__ == '__main__':
    api = Api()
    # Create window with slightly transparent effect if supported (not easy in pywebview standard, but we have CSS glass)
    # The 'js_api' exposes the class instance to window.pywebview.api
    html_path = resource_path('web/index.html')
    # Webview expects a URL or a path. Ensure it's absolute to be safe.
    if not os.path.exists(html_path):
        # Fallback if something is wrong, though resource_path should handle it
        html_path = os.path.join(os.getcwd(), 'web', 'index.html')

    window = webview.create_window('FlowDown', html_path, js_api=api, width=500, height=700, resizable=False, background_color='#0f0f13')
    api.set_window(window)
    webview.start(debug=False)


