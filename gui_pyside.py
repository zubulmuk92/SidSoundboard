import sys
import os
import uuid
import threading
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QScrollArea, QFrame, QGridLayout,
    QComboBox, QSlider, QDialog, QMessageBox, QFileDialog, QProgressBar, QStackedWidget
)
from PySide6.QtCore import Qt, QTimer, QSize, Signal, Slot, QThread
from PySide6.QtGui import QFont, QIcon, QColor, QPalette

import config_manager
from yt_downloader import download_youtube_audio_async
from audio_processor import normalize_and_import_audio
import keyboard

def get_icon(name):
    # Resolves icon path properly in PyInstaller or dev mode
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return QIcon(os.path.join(base_path, 'icons', name))

# --- THEME STUDIO EDITION ---
BG_APP = "#0f172a"
BG_CARD = "#1e293b"
BG_CARD_HOVER = "#334155"
TEXT_MAIN = "#f8fafc"
TEXT_MUTED = "#94a3b8"
ACCENT_COLOR = "#3b82f6"
ACCENT_HOVER = "#2563eb"
DANGER_COLOR = "#ef4444"

COLOR_MAP = {
    "Sons Troll": "#FF3366",
    "Musiques": "#33CCFF",
    "SFX": "#33FF99",
    "Voix": "#FFCC00",
    "Ambiance": "#B829FF",
    "Gris": "#94a3b8"
}

QSS = f"""
QMainWindow, QDialog {{ background-color: {BG_APP}; }}
QWidget {{ color: {TEXT_MAIN}; font-family: 'Segoe UI', 'Inter'; font-size: 13px; }}

QScrollArea {{ border: none; background-color: transparent; }}
QScrollArea > QWidget > QWidget {{ background-color: transparent; }}

QScrollBar:vertical {{
    border: none; background: {BG_APP}; width: 10px; margin: 0px 0px 0px 0px;
}}
QScrollBar::handle:vertical {{
    background: {BG_CARD_HOVER}; min-height: 20px; border-radius: 5px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ border: none; background: none; }}

QPushButton {{
    background-color: {BG_CARD}; color: {TEXT_MAIN}; border: 1px solid {BG_APP};
    border-radius: 6px; padding: 6px 12px; font-weight: bold;
}}
QPushButton:hover {{ background-color: {BG_CARD_HOVER}; border: 1px solid {ACCENT_COLOR}; }}

QPushButton.accent {{ background-color: {ACCENT_COLOR}; color: white; border: none; }}
QPushButton.accent:hover {{ background-color: {ACCENT_HOVER}; }}
QPushButton.danger {{ background-color: transparent; border: 1px solid {DANGER_COLOR}; color: {DANGER_COLOR}; }}
QPushButton.danger:hover {{ background-color: {DANGER_COLOR}; color: white; }}

QLineEdit, QComboBox {{
    background-color: {BG_CARD}; color: {TEXT_MAIN}; border: 1px solid {BG_CARD_HOVER};
    border-radius: 6px; padding: 6px 10px;
}}
QLineEdit:focus, QComboBox:focus {{ border: 1px solid {ACCENT_COLOR}; }}

QComboBox::drop-down {{ border: none; }}
QComboBox QAbstractItemView {{
    background-color: {BG_CARD}; color: {TEXT_MAIN}; selection-background-color: {ACCENT_COLOR};
}}

QSlider::groove:horizontal {{
    border: 1px solid {BG_CARD}; background: {BG_APP}; height: 6px; border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {ACCENT_COLOR}; width: 14px; margin-top: -4px; margin-bottom: -4px; border-radius: 7px;
}}

/* Sidebar */
#Sidebar {{ background-color: {BG_CARD}; border-right: 1px solid {BG_APP}; }}
#Sidebar QPushButton {{ background-color: transparent; border: none; text-align: left; padding-left: 20px; font-size: 14px; }}
#Sidebar QPushButton:hover {{ background-color: {BG_CARD_HOVER}; }}
#Sidebar QPushButton:checked {{ background-color: {BG_APP}; color: {ACCENT_COLOR}; border-left: 3px solid {ACCENT_COLOR}; border-radius: 0px; }}

/* Card */
#SoundCard {{
    background-color: {BG_CARD}; border: 1px solid {BG_APP}; border-radius: 8px;
}}
#SoundCard:hover {{ background-color: {BG_CARD_HOVER}; border: 1px solid {ACCENT_COLOR}; }}

/* ProgressBar */
QProgressBar {{ border: 1px solid {BG_APP}; border-radius: 4px; text-align: center; color: white; background: {BG_CARD}; }}
QProgressBar::chunk {{ background-color: {ACCENT_COLOR}; width: 1px; }}
"""

class WorkerThread(QThread):
    finished_signal = Signal(bool, list, str)
    progress_signal = Signal(str, int, int, str)
    
    def __init__(self, target, *args, **kwargs):
        super().__init__()
        self.target = target
        self.args = args
        self.kwargs = kwargs
        
    def run(self):
        try:
            self.target(*self.args, **self.kwargs)
        except Exception as e:
            self.finished_signal.emit(False, [], str(e))

class AppGUI(QMainWindow):
    add_sound_done = Signal(str, dict)
    
    def __init__(self, audio_manager, hotkey_manager):
        super().__init__()
        self.add_sound_done.connect(self._on_add_sound_done)
        self.audio_manager = audio_manager
        self.hotkey_manager = hotkey_manager
        self.config = config_manager.load_config()
        self.sounds = self.config.get('sounds', [])
        
        self.setWindowTitle("SidSoundboard - Studio Edition")
        self.resize(1050, 750)
        self.setMinimumSize(950, 650)
        self.setStyleSheet(QSS)
        
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._filter_sounds)
        
        self.timeline_timer = QTimer()
        self.timeline_timer.timeout.connect(self.update_timeline)
        self.timeline_timer.start(100)
        
        self._build_ui()
        self.update_sound_list()

    def _build_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(220)
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(0, 20, 0, 20)
        
        title = QLabel("SidSoundboard")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {TEXT_MAIN}; padding-left: 20px;")
        side_layout.addWidget(title)
        side_layout.addSpacing(30)
        
        self.btn_lib = QPushButton(" Bibliothèque")
        self.btn_lib.setIcon(get_icon('lib.svg'))
        self.btn_lib.setCheckable(True)
        self.btn_lib.setChecked(True)
        self.btn_lib.clicked.connect(lambda: self._switch_tab(0))
        
        self.btn_set = QPushButton(" Réglages")
        self.btn_set.setIcon(get_icon('settings.svg'))
        self.btn_set.setCheckable(True)
        self.btn_set.clicked.connect(lambda: self._switch_tab(1))
        
        side_layout.addWidget(self.btn_lib)
        side_layout.addWidget(self.btn_set)
        side_layout.addStretch()
        
        self.btn_stop = QPushButton(" STOP AUDIO")
        self.btn_stop.setIcon(get_icon('stop.svg'))
        self.btn_stop.setProperty("class", "danger")
        self.btn_stop.clicked.connect(self.audio_manager.stop_all)
        side_layout.addWidget(self.btn_stop)
        
        main_layout.addWidget(self.sidebar)
        
        # Main Content
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.addWidget(self.content_area)
        
        self.stacked_widget = QStackedWidget()
        self.content_layout.addWidget(self.stacked_widget)
        
        self._build_sounds_view()
        self._build_settings_view()
        
        # Player bottom bar
        self.player_bar = QFrame()
        self.player_bar.setObjectName("SoundCard")
        self.player_bar.setFixedHeight(60)
        p_layout = QHBoxLayout(self.player_bar)
        
        self.lbl_playing = QLabel("Aucun son en cours")
        self.lbl_playing.setFixedWidth(250)
        p_layout.addWidget(self.lbl_playing)
        
        self.lbl_time_cur = QLabel("0:00")
        self.lbl_time_cur.setFixedWidth(40)
        p_layout.addWidget(self.lbl_time_cur)
        
        self.timeline = QSlider(Qt.Horizontal)
        self.timeline.setRange(0, 1000)
        self.timeline.sliderReleased.connect(self.on_timeline_seek)
        p_layout.addWidget(self.timeline)
        
        self.lbl_time_tot = QLabel("0:00")
        self.lbl_time_tot.setFixedWidth(40)
        p_layout.addWidget(self.lbl_time_tot)
        
        self.content_layout.addWidget(self.player_bar)
        
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self._rebuild_grid)

    def _switch_tab(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.btn_lib.setChecked(index == 0)
        self.btn_set.setChecked(index == 1)

    def _build_sounds_view(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        
        topbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher un son (Titre, Touche, Catégorie)...")
        self.search_input.setFixedHeight(36)
        self.search_input.textChanged.connect(lambda t: self.search_timer.start(300))
        topbar.addWidget(self.search_input)
        
        self.btn_add = QPushButton(" IMPORT LOCAL")
        self.btn_add.setIcon(get_icon('add.svg'))
        self.btn_add.setFixedHeight(36)
        self.btn_add.clicked.connect(self.add_sound)
        topbar.addWidget(self.btn_add)
        
        self.btn_yt = QPushButton(" YT DOWNLOAD")
        self.btn_yt.setIcon(get_icon('download.svg'))
        self.btn_yt.setProperty("class", "accent")
        self.btn_yt.setFixedHeight(36)
        self.btn_yt.clicked.connect(self.download_youtube)
        topbar.addWidget(self.btn_yt)
        
        layout.addLayout(topbar)
        layout.addSpacing(10)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.grid_layout = QGridLayout(self.scroll_widget)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(15)
        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area)
        
        self.stacked_widget.addWidget(page)

    def _build_settings_view(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        title = QLabel("Réglages Audio")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {TEXT_MAIN};")
        layout.addWidget(title)
        
        form = QFrame()
        form.setObjectName("SoundCard")
        form_layout = QGridLayout(form)
        form_layout.setSpacing(20)
        
        devices = self.audio_manager.get_output_devices()
        dev_list = ["Par défaut"] + [d['name'] for d in devices]
        
        self.cb_main_device = QComboBox()
        self.cb_main_device.addItems(dev_list)
        self.cb_main_device.setCurrentText(self.config.get('default_device', 'Par défaut'))
        
        self.cb_second_device = QComboBox()
        self.cb_second_device.addItems(["Aucun"] + dev_list)
        self.cb_second_device.setCurrentText(self.config.get('second_device', 'Aucun'))
        
        form_layout.addWidget(QLabel("Périphérique Principal :"), 0, 0)
        form_layout.addWidget(self.cb_main_device, 0, 1)
        form_layout.addWidget(QLabel("Périphérique Secondaire (ex: Câble Virtuel) :"), 1, 0)
        form_layout.addWidget(self.cb_second_device, 1, 1)
        
        self.cb_ducking = QComboBox()
        self.cb_ducking.addItems(["Aucun", "Léger (50%)", "Fort (80%)", "Total (100%)"])
        self.cb_ducking.setCurrentText(self.config.get('audio_ducking_level', 'Léger (50%)'))
        
        form_layout.addWidget(QLabel("Atténuation (Ducking) :"), 2, 0)
        form_layout.addWidget(self.cb_ducking, 2, 1)
        
        self.btn_panic = QPushButton(f"Touche Arrêt: {self.config.get('panic_hotkey', 'None')}")
        self.btn_panic.clicked.connect(self.bind_panic_key)
        form_layout.addWidget(QLabel("Arrêt d'urgence global :"), 3, 0)
        form_layout.addWidget(self.btn_panic, 3, 1)
        
        btn_save = QPushButton("SAUVEGARDER")
        btn_save.setProperty("class", "accent")
        btn_save.clicked.connect(self.save_settings)
        form_layout.addWidget(btn_save, 4, 1)
        
        layout.addWidget(form)
        layout.addStretch()
        
        self.stacked_widget.addWidget(page)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resize_timer.start(150)

    def update_sound_list(self):
        self.sounds = self.config.get('sounds', [])
        self._filter_sounds()

    def _filter_sounds(self):
        term = self.search_input.text().lower()
        self.filtered_sounds = []
        for s in self.sounds:
            if term in s.get('name', '').lower() or term in s.get('hotkey', '').lower() or term in s.get('color', '').lower():
                self.filtered_sounds.append(s)
        self._rebuild_grid()

    def _rebuild_grid(self):
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        width = self.scroll_area.viewport().width()
        card_width = 320
        cols = max(1, width // (card_width + 15))
        
        for i, sound in enumerate(self.filtered_sounds):
            row = i // cols
            col = i % cols
            self.grid_layout.addWidget(self._create_card(sound), row, col)
            
        self.grid_layout.setRowStretch(self.grid_layout.rowCount(), 1)

    def _create_card(self, sound):
        card = QFrame()
        card.setObjectName("SoundCard")
        card.setFixedSize(300, 110)
        
        cat = sound.get('color', 'Gris')
        cat_hex = COLOR_MAP.get(cat, "#94a3b8")
        if cat != "Gris":
            card.setStyleSheet(f"#SoundCard {{ border-left: 4px solid {cat_hex}; }}")
            
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 10, 15, 10)
        
        top_row = QHBoxLayout()
        name_lbl = QLabel(sound.get('name', 'Unknown'))
        name_lbl.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {TEXT_MAIN};")
        top_row.addWidget(name_lbl)
        top_row.addStretch()
        
        hk_btn = QPushButton(sound.get('hotkey', 'None'))
        hk_btn.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; background: {BG_APP}; padding: 2px 6px; border-radius: 4px;")
        hk_btn.clicked.connect(lambda _, s=sound, b=hk_btn: self.bind_hotkey(s['id'], b))
        top_row.addWidget(hk_btn)
        
        btn_del = QPushButton()
        btn_del.setIcon(get_icon('delete.svg'))
        btn_del.setProperty("class", "danger")
        btn_del.setFixedSize(28, 28)
        btn_del.clicked.connect(lambda _, s=sound: self.remove_sound(s['id']))
        top_row.addWidget(btn_del)
        
        layout.addLayout(top_row)
        
        bot_row = QHBoxLayout()
        btn_play = QPushButton(" PLAY")
        btn_play.setIcon(get_icon('play.svg'))
        btn_play.setProperty("class", "accent")
        btn_play.setFixedSize(85, 26)
        btn_play.clicked.connect(lambda _, s=sound: self.play_sound(s))
        bot_row.addWidget(btn_play)
        
        vol_slider = QSlider(Qt.Horizontal)
        vol_slider.setRange(0, 400)
        vol_slider.setValue(sound.get('volume', 100))
        vol_slider.setFixedWidth(80)
        vol_slider.sliderReleased.connect(lambda s=sound, sl=vol_slider: self.apply_audio(s['id'], sl.value(), 100))
        bot_row.addWidget(vol_slider)
        
        cb_color = QComboBox()
        cb_color.addItems(list(COLOR_MAP.keys()))
        cb_color.setCurrentText(cat)
        cb_color.setFixedWidth(80)
        cb_color.currentTextChanged.connect(lambda c, s=sound: self.on_color_change(c, s['id']))
        bot_row.addWidget(cb_color)
        
        layout.addLayout(bot_row)
        return card

    def on_color_change(self, choice, sid):
        for s in self.sounds:
            if s['id'] == sid:
                s['color'] = choice
                break
        self.config['sounds'] = self.sounds
        config_manager.save_config(self.config)
        self.update_sound_list()

    def play_sound(self, sound):
        original_file = sound.get("filename") or sound.get("file")
        vol_p = sound.get("volume", 100)
        spd = sound.get("speed", 100)
        global_sec_vol = self.config.get("global_secondary_volume", 100)
        vol_s = int(vol_p * (global_sec_vol / 100.0))
        
        from audio_processor import generate_cached_file_sync
        try:
            filepath_sec = generate_cached_file_sync(original_file, vol_s, spd)
        except:
            filepath_sec = original_file

        self.lbl_playing.setText(f"En cours: {sound.get('name')}")
        
        self.audio_manager.toggle_play_pause(
            filepath_primary=sound.get("cached_file_primary") or sound.get("cached_file") or original_file,
            filepath_secondary=filepath_sec,
            name=sound.get("name", "Unknown"),
            volume=1.0,
            primary_device_name=self.config.get("primary_output"),
            secondary_device_name=self.config.get("secondary_output"),
            dual_enabled=self.config.get("dual_output_enabled", False),
            sound_id=sound.get("id")
        )

    def apply_audio(self, sid, vol, spd):
        for s in self.sounds:
            if s['id'] == sid:
                s['volume'] = vol
                break
        self.config['sounds'] = self.sounds
        config_manager.save_config(self.config)

    def remove_sound(self, sid):
        reply = QMessageBox.question(self, 'Confirmation', "Êtes-vous sûr de vouloir supprimer ce son ?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No: return
        
        self.sounds = [s for s in self.sounds if s['id'] != sid]
        self.config['sounds'] = self.sounds
        config_manager.save_config(self.config)
        self.update_sound_list()

    def bind_hotkey(self, sid, btn):
        btn.setText("Press key...")
        btn.setStyleSheet(f"color: {ACCENT_COLOR}; font-size: 11px; background: {BG_APP}; padding: 2px 6px;")
        
        def capture():
            hk = keyboard.read_hotkey(suppress=False)
            self.hotkey_manager.load_hotkeys(self.config)
            QTimer.singleShot(0, lambda: apply(hk))
            
        def apply(hk):
            for s in self.sounds:
                if s['id'] == sid:
                    s['hotkey'] = 'None' if hk == 'esc' else hk
            self.config['sounds'] = self.sounds
            config_manager.save_config(self.config)
            self.hotkey_manager.load_hotkeys(self.config)
            self.update_sound_list()
            
        self.hotkey_manager.shutdown()
        threading.Thread(target=capture, daemon=True).start()

    def bind_panic_key(self):
        self.btn_panic.setText("Appuyez sur une touche...")
        
        def capture():
            hk = keyboard.read_hotkey(suppress=False)
            self.hotkey_manager.load_hotkeys(self.config)
            QTimer.singleShot(0, lambda: apply(hk))
            
        def apply(hk):
            self.config['panic_hotkey'] = 'None' if hk == 'esc' else hk
            config_manager.save_config(self.config)
            self.hotkey_manager.load_hotkeys(self.config)
            self.btn_panic.setText(f"Touche Arrêt: {self.config['panic_hotkey']}")
            
        self.hotkey_manager.shutdown()
        threading.Thread(target=capture, daemon=True).start()

    def update_timeline(self):
        prog = self.audio_manager.get_focused_progress()
        if not prog:
            self.lbl_time_cur.setText("0:00")
            self.lbl_time_tot.setText("0:00")
            self.timeline.blockSignals(True)
            self.timeline.setValue(0)
            self.timeline.blockSignals(False)
            return
            
        current = prog["current"]
        duration = prog["duration"]
        
        self.lbl_time_cur.setText(self.format_time(current))
        self.lbl_time_tot.setText(self.format_time(duration))
        
        self.timeline.blockSignals(True)
        if duration > 0:
            self.timeline.setValue(int((current / duration) * 1000))
        self.timeline.blockSignals(False)
            
    def on_timeline_seek(self):
        val = self.timeline.value() / 1000.0
        fi = self.audio_manager.focused_info
        if fi and fi.get('duration'):
            target = val * fi['duration']
            self.audio_manager.seek_focused(target)

    def format_time(self, seconds):
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}:{secs:02d}"

    def add_sound(self):
        with open("debug.log", "a", encoding="utf-8") as dlog:
            dlog.write("add_sound clicked!\\n")
            
        f, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner un fichier audio", "", "Audio Files (*.mp3 *.wav *.ogg *.flac *.m4a)",
            options=QFileDialog.DontUseNativeDialog
        )
        if not f: return
        
        with open("debug.log", "a", encoding="utf-8") as dlog:
            dlog.write(f"File selected: {f}\\n")
        
        sid = str(uuid.uuid4())[:8]
        new_s = {
            "id": sid, "name": os.path.basename(f), "filename": f,
            "hotkey": "None", "volume": 100, "color": "Gris",
            "device": self.config.get('default_device', 'Par défaut'),
            "second_device": self.config.get('second_device', 'Aucun'),
            "audio_ducking": self.config.get('audio_ducking_level', 'Léger (50%)') != "Aucun"
        }
        
        self.progress_dialog = QProgressDialog("Importation et normalisation en cours...", None, 0, 0, self)
        self.progress_dialog.setWindowTitle("Veuillez patienter")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.show()

        def process():
            try:
                proc_path = normalize_and_import_audio(f, "downloads", sid)
            except Exception as e:
                import traceback
                with open("crash.log", "a", encoding="utf-8") as clog:
                    clog.write(f"IMPORT ERROR:\\n{traceback.format_exc()}\\n")
                proc_path = None
            self.add_sound_done.emit(proc_path or "", new_s)
            
        threading.Thread(target=process, daemon=True).start()

    @Slot(str, dict)
    def _on_add_sound_done(self, proc_path, new_s):
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()

        with open("debug.log", "a", encoding="utf-8") as dlog:
            dlog.write(f"_on_add_sound_done called with proc_path={proc_path}\\n")
        
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
            done = Signal(bool, list, str)
            
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
                    except Exception as e:
                        import traceback
                        with open("crash.log", "a", encoding="utf-8") as clog:
                            clog.write(f"YT IMPORT ERROR:\\n{traceback.format_exc()}\\n")
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

    def save_settings(self):
        self.config['default_device'] = self.cb_main_device.currentText()
        self.config['second_device'] = self.cb_second_device.currentText()
        self.config['audio_ducking_level'] = self.cb_ducking.currentText()
        config_manager.save_config(self.config)
        
        for s in self.sounds:
            s['device'] = self.config['default_device']
            s['second_device'] = self.config['second_device']
            s['audio_ducking'] = self.config['audio_ducking_level'] != "Aucun"
            
        self.config['sounds'] = self.sounds
        config_manager.save_config(self.config)
        QMessageBox.information(self, "Succès", "Réglages appliqués à tous les sons !")

if __name__ == "__main__":
    from audio_manager import AudioManager
    from hotkey_manager import HotkeyManager
    
    app = QApplication(sys.argv)
    audio = AudioManager()
    hotkey = HotkeyManager(audio, config_manager.load_config())
    hotkey.load_hotkeys(config_manager.load_config())
    
    window = AppGUI(audio, hotkey)
    window.show()
    sys.exit(app.exec())
