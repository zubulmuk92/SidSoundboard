import os
import urllib.request
import zipfile
import tempfile
import ctypes
import threading
import time

VBCABLE_URL = "https://download.vb-audio.com/Download_CABLE/VBCABLE_Driver_Pack43.zip"

def install_vbcable_async(progress_callback, on_done_callback):
    def worker():
        try:
            progress_callback("Téléchargement du pilote VB-Cable...")
            
            temp_dir = tempfile.gettempdir()
            zip_path = os.path.join(temp_dir, "VBCABLE_Driver_Pack43.zip")
            extract_path = os.path.join(temp_dir, "VBCABLE_Setup")
            
            if not os.path.exists(extract_path):
                os.makedirs(extract_path)
            
            # Download
            req = urllib.request.Request(VBCABLE_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response, open(zip_path, 'wb') as out_file:
                out_file.write(response.read())
                
            progress_callback("Extraction des fichiers...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
                
            progress_callback("Installation (L'invite administrateur va s'ouvrir)...")
            setup_exe = os.path.join(extract_path, "VBCABLE_Setup_x64.exe")
            
            if not os.path.exists(setup_exe):
                raise Exception("Exécutable introuvable dans l'archive.")
            
            # Exécution admin silencieuse
            ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", setup_exe, "-i -h", extract_path, 0)
            
            if ret <= 32:
                raise Exception(f"L'installation a été refusée ou a échoué (Code {ret})")
                
            progress_callback("Finalisation... (patientez 5 secondes)")
            time.sleep(5)
            
            on_done_callback(True, "")
            
        except Exception as e:
            on_done_callback(False, str(e))
            
    threading.Thread(target=worker, daemon=True).start()
