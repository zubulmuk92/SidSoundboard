import sys

with open("gui_pyside.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "def _on_add_sound_done(" in line:
        start_idx = i
        break

# I will replace from start_idx up to def save_settings(self):
for i, line in enumerate(lines[start_idx:]):
    if "def save_settings(" in line:
        end_idx = start_idx + i
        break

new_code = """    def _on_add_sound_done(self, proc_path, new_s):
        if proc_path:
            new_s['filename'] = proc_path
            self.sounds.insert(0, new_s)
            self.config['sounds'] = self.sounds
            config_manager.save_config(self.config)
            self.update_sound_list()

    def download_youtube(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Télécharger YouTube")
        dlg.setFixedSize(400, 200)
        
        layout = QVBoxLayout(dlg)
        
        url_input = QLineEdit()
        url_input.setPlaceholderText("URL YouTube (https://...)")
        layout.addWidget(url_input)
        
        title_input = QLineEdit()
        title_input.setPlaceholderText("Nom du son (optionnel)")
        layout.addWidget(title_input)
        
        pb = QProgressBar()
        pb.setValue(0)
        layout.addWidget(pb)
        
        btn_dl = QPushButton("TÉLÉCHARGER")
        btn_dl.setProperty("class", "accent")
        layout.addWidget(btn_dl)
        
        class YTSignals(QObject):
            progress = Signal(int)
            done = Signal(bool, object, str)
            
        sigs = YTSignals()
        sigs.progress.connect(pb.setValue)
        
        def start_dl():
            url = url_input.text().strip()
            if not url: return
            btn_dl.setEnabled(False)
            
            def prog_cb(pct_str, curr, tot, t):
                try:
                    pct = float(pct_str.replace('%','').strip())
                    sigs.progress.emit(int(pct))
                except: pass
                
            def done_cb(succ, res, err):
                sigs.done.emit(succ, res, err)
                
            from yt_downloader import download_youtube_audio_async
            download_youtube_audio_async(url, "downloads", prog_cb, done_cb)
            
        def finish(succ, res, err):
            dlg.accept()
            if succ and res:
                for r in res:
                    sid = str(uuid.uuid4())[:8]
                    try:
                        from audio_processor import normalize_and_import_audio
                        pp = normalize_and_import_audio(r['filepath'], "downloads")
                    except Exception:
                        pp = r['filepath']
                    if pp:
                        new_s = {
                            "id": sid, "name": title_input.text() or r['title'],
                            "filename": pp, "hotkey": "None", "volume": 100, "color": "Musiques",
                            "device": self.config.get('default_device', 'Par défaut'),
                            "second_device": self.config.get('second_device', 'Aucun'),
                            "audio_ducking": self.config.get('audio_ducking_level', 'Léger (50%)') != "Aucun"
                        }
                        self.sounds.insert(0, new_s)
                self.config['sounds'] = self.sounds
                config_manager.save_config(self.config)
                self.update_sound_list()
            else:
                QMessageBox.critical(self, "Erreur", f"Échec: {err}")
                
        sigs.done.connect(finish)
        btn_dl.clicked.connect(start_dl)
        dlg.exec()

"""

lines = lines[:start_idx] + [new_code] + lines[end_idx:]

with open("gui_pyside.py", "w", encoding="utf-8") as f:
    f.writelines(lines)
