import customtkinter as ctk
from tkinter import filedialog, messagebox
import uuid
import os
import sys
import keyboard
import threading
from yt_downloader import download_youtube_audio_async
import config_manager

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

ctk.set_appearance_mode("Dark")

# PRO COLOR PALETTE (Studio)
BG_COLOR = "#0F172A"
PANEL_COLOR = "#1E293B"
CARD_COLOR = "#334155"
BORDER_COLOR = "#0F172A"
ACCENT_COLOR = "#38BDF8"
ACCENT_HOVER = "#0284C7"
TEXT_MAIN = "#F8FAFC"
TEXT_MUTED = "#94A3B8"
DANGER_COLOR = "#EF4444"
DANGER_HOVER = "#B91C1C"

CR = 8 # Global Corner Radius

class AppGUI(ctk.CTk):
    def __init__(self, audio_manager, hotkey_manager):
        super().__init__()
        
        self.audio_manager = audio_manager
        self.hotkey_manager = hotkey_manager
        self.config = config_manager.load_config()
        
        self.title("SidSoundboard - Studio Edition")
        self.geometry("900x650")
        self.minsize(850, 600)
        
        try:
            self.iconbitmap(resource_path("logo.ico"))
        except Exception:
            pass
            
        self.protocol('WM_DELETE_WINDOW', self.hide_window)
        self._build_ui()
        self.update_sound_list()
        self.after(50, self._set_dark_titlebar)

    def _set_dark_titlebar(self):
        try:
            import ctypes
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
            get_parent = ctypes.windll.user32.GetParent
            hwnd = get_parent(self.winfo_id())
            rendering_policy = ctypes.c_int(2)
            set_window_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(rendering_policy), ctypes.sizeof(rendering_policy))
        except Exception:
            pass

    def hide_window(self):
        self.withdraw()
        if not hasattr(self, "tray_icon") or self.tray_icon is None:
            self.create_tray_icon()
            
    def show_window(self, icon=None, item=None):
        self.after(0, self.deiconify)
        
    def quit_app(self, icon=None, item=None):
        if hasattr(self, "tray_icon") and self.tray_icon:
            self.tray_icon.stop()
        self.after(0, self.destroy)
        import os
        os._exit(0) # Ensure hotkey threads are killed
        
    def create_tray_icon(self):
        import pystray
        from PIL import Image
        
        try:
            image = Image.open(resource_path("logo_sq.png"))
        except:
            image = Image.new('RGB', (64, 64), color=(24, 24, 27))
            
        menu = pystray.Menu(
            pystray.MenuItem('Ouvrir', self.show_window, default=True),
            pystray.MenuItem('Stop Audio', lambda i, it: self.after(0, self.audio_manager.stop_all)),
            pystray.MenuItem('Quitter', self.quit_app)
        )
        self.tray_icon = pystray.Icon("SidSoundboard", image, "SidSoundboard", menu)
        import threading
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _build_ui(self):
        self.configure(fg_color=BG_COLOR)
        
        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=PANEL_COLOR, border_width=1, border_color=BORDER_COLOR)
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)
        
        self.title_label = ctk.CTkLabel(self.sidebar_frame, text="SIDSOUNDBOARD", font=("Segoe UI", 16, "bold"), text_color=TEXT_MAIN)
        self.title_label.pack(pady=(25, 30))
        
        self.nav_btns = {}
        
        def nav(view_name):
            for name, btn in self.nav_btns.items():
                if name == view_name:
                    btn.configure(fg_color=CARD_COLOR, text_color=ACCENT_COLOR, font=("Segoe UI", 13, "bold"))
                else:
                    btn.configure(fg_color="transparent", text_color=TEXT_MAIN, font=("Segoe UI", 13))
            self.show_view(view_name)
            
        btn_lib = ctk.CTkButton(self.sidebar_frame, text="  Bibliothèque", anchor="w", corner_radius=CR, fg_color="transparent", hover_color=CARD_COLOR, text_color=TEXT_MAIN, command=lambda: nav("lib"))
        btn_lib.pack(fill="x", padx=15, pady=5)
        self.nav_btns["lib"] = btn_lib
        
        btn_set = ctk.CTkButton(self.sidebar_frame, text="  Paramètres", anchor="w", corner_radius=CR, fg_color="transparent", hover_color=CARD_COLOR, text_color=TEXT_MAIN, command=lambda: nav("set"))
        btn_set.pack(fill="x", padx=15, pady=5)
        self.nav_btns["set"] = btn_set
        
        btn_rtg = ctk.CTkButton(self.sidebar_frame, text="  Routage Virtuel", anchor="w", corner_radius=CR, fg_color="transparent", hover_color=CARD_COLOR, text_color=TEXT_MAIN, command=lambda: nav("rtg"))
        btn_rtg.pack(fill="x", padx=15, pady=5)
        self.nav_btns["rtg"] = btn_rtg
        
        self.stop_btn = ctk.CTkButton(self.sidebar_frame, text="STOP AUDIO", height=36, corner_radius=CR, font=("Segoe UI", 12, "bold"), fg_color="transparent", border_width=1, border_color=DANGER_COLOR, hover_color=DANGER_HOVER, text_color=TEXT_MAIN, command=self.audio_manager.stop_all)
        self.stop_btn.pack(side="bottom", fill="x", padx=15, pady=20)
        
        # Main Content
        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=BG_COLOR)
        self.content_frame.pack(side="right", fill="both", expand=True)
        
        nav("lib")

    def show_view(self, view_name):
        # Cancel any pending seek tasks
        if hasattr(self, '_seek_after_id') and self._seek_after_id:
            self.after_cancel(self._seek_after_id)
            self._seek_after_id = None
            
        # Cancel timeline loop if leaving lib
        if view_name != "lib" and hasattr(self, '_timeline_loop_id') and self._timeline_loop_id:
            self.after_cancel(self._timeline_loop_id)
            self._timeline_loop_id = None

        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        if view_name == "lib":
            self._build_sounds_view()
        elif view_name == "set":
            self._build_settings_view()
        elif view_name == "rtg":
            self._build_discord_view()

    def _build_sounds_view(self):
        # Toolbar
        toolbar = ctk.CTkFrame(self.content_frame, height=55, corner_radius=0, fg_color=BG_COLOR)
        toolbar.pack(fill="x", pady=(10, 5), padx=20)
        toolbar.pack_propagate(False)
        
        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(toolbar, placeholder_text="Rechercher un son...", width=280, height=36, corner_radius=CR, fg_color=PANEL_COLOR, border_width=0, text_color=TEXT_MAIN, font=("Segoe UI", 13))
        search_entry.pack(side="left")
        
        self._search_timer = None
        def on_search_change(e):
            if self._search_timer:
                self.after_cancel(self._search_timer)
            self._search_timer = self.after(250, _do_search)
            
        def _do_search():
            self.search_var.set(search_entry.get())
            self.update_sound_list()
            
        search_entry.bind("<KeyRelease>", on_search_change)
        
        # Modern outline buttons
        ctk.CTkButton(toolbar, text="IMPORT LOCAL", width=120, height=36, corner_radius=CR, font=("Segoe UI", 11, "bold"), fg_color="transparent", border_width=1, border_color=BORDER_COLOR, hover_color=PANEL_COLOR, text_color=TEXT_MAIN, command=self.add_sound).pack(side="right", padx=(10, 0))
        ctk.CTkButton(toolbar, text="TÉLÉCHARGER URL", width=140, height=36, corner_radius=CR, font=("Segoe UI", 11, "bold"), fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER, text_color="#FFFFFF", command=self.download_youtube).pack(side="right")
        
        # Player (Top right below toolbar)
        self.player_frame = ctk.CTkFrame(self.content_frame, height=45, corner_radius=CR, fg_color=PANEL_COLOR, border_width=0)
        self.player_frame.pack(fill="x", padx=20, pady=(0, 15))
        self.player_frame.pack_propagate(False)
        
        self.player_status_lbl = ctk.CTkLabel(self.player_frame, text="EN ATTENTE", font=("Segoe UI", 12, "bold"), text_color=TEXT_MUTED)
        self.player_status_lbl.pack(side="left", padx=15)
        
        self.timeline_var = ctk.DoubleVar(value=0.0)
        self.timeline_slider = ctk.CTkSlider(self.player_frame, from_=0, to=100, variable=self.timeline_var, command=self.on_timeline_seek, progress_color=ACCENT_COLOR, fg_color=CARD_COLOR, button_color=TEXT_MAIN, button_hover_color="#FFFFFF", height=8)
        self.timeline_slider.pack(side="left", expand=True, fill="x", padx=15)
        
        self.time_lbl = ctk.CTkLabel(self.player_frame, text="0:00 / 0:00", width=70, font=("Segoe UI", 11), text_color=TEXT_MUTED)
        self.time_lbl.pack(side="right", padx=15)
        
        self.is_scrubbing = False
        self._seek_after_id = None
        
        # List
        self.sounds_scroll = ctk.CTkScrollableFrame(self.content_frame, corner_radius=4, fg_color=BG_COLOR)
        self.sounds_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        self.update_sound_list()
        self.update_timeline()

    def update_timeline(self):
        # Prevent running if not in lib view
        if not hasattr(self, 'sounds_scroll') or not self.sounds_scroll.winfo_exists():
            return
            
        progress = self.audio_manager.get_focused_progress()
        if progress:
            self.player_status_lbl.configure(text=f"LECTURE: {progress['name'][:25]}", text_color=ACCENT_COLOR)
            
            cur = int(progress['current'])
            tot = int(progress['duration'])
            if cur > tot: cur = tot
            
            cur_m, cur_s = divmod(cur, 60)
            tot_m, tot_s = divmod(tot, 60)
            self.time_lbl.configure(text=f"{cur_m}:{cur_s:02d} / {tot_m}:{tot_s:02d}")
            
            if tot > 0 and not getattr(self, 'is_scrubbing', False):
                self.timeline_var.set((progress['current'] / tot) * 100)
                
            playing_id = progress.get("sound_id")
            is_paused = progress.get("is_paused", False)
        else:
            self.player_status_lbl.configure(text="EN ATTENTE", text_color=TEXT_MUTED)
            self.time_lbl.configure(text="0:00 / 0:00")
            if not getattr(self, 'is_scrubbing', False):
                self.timeline_var.set(0.0)
            playing_id = None
            is_paused = False
            
        if hasattr(self, 'play_buttons'):
            for s_id, btn in self.play_buttons.items():
                try:
                    if s_id == playing_id:
                        if not is_paused:
                            if btn.cget("text") != "PAUSE":
                                btn.configure(text="PAUSE", text_color=DANGER_COLOR, fg_color="transparent", border_color=DANGER_COLOR)
                        else:
                            if btn.cget("text") != "PLAY":
                                btn.configure(text="PLAY", text_color=TEXT_MAIN, fg_color="transparent", border_color=BORDER_COLOR)
                    else:
                        if btn.cget("text") != "PLAY":
                            btn.configure(text="PLAY", text_color=TEXT_MAIN, fg_color="transparent", border_color=BORDER_COLOR)
                except:
                    pass
            
        self._timeline_loop_id = self.after(100, self.update_timeline)

    def on_timeline_seek(self, value):
        self.is_scrubbing = True
        if self._seek_after_id:
            self.after_cancel(self._seek_after_id)
            
        def do_seek():
            self.is_scrubbing = False
            fi = self.audio_manager.focused_info
            if not fi: return
            tot = fi['duration']
            target_time = (value / 100.0) * tot
            self.audio_manager.seek_focused(target_time)
            
        self._seek_after_id = self.after(250, do_seek)

    def _build_settings_view(self):
        devices = self.audio_manager.get_output_devices()
        device_names = ["Aucun"] + [d["name"] for d in devices]
        
        inner = ctk.CTkFrame(self.content_frame, fg_color=PANEL_COLOR, corner_radius=4, border_width=1, border_color=BORDER_COLOR)
        inner.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(inner, text="ROUTAGE AUDIO", font=("Segoe UI", 16, "bold"), text_color=TEXT_MAIN).pack(anchor="w", padx=30, pady=(30, 10))
        
        ctk.CTkLabel(inner, text="Sortie Principale (Casque / Haut-parleurs) :", font=("Segoe UI", 12), text_color=TEXT_MUTED).pack(anchor="w", padx=30, pady=(10, 0))
        self.primary_cb = ctk.CTkComboBox(inner, values=device_names, width=400, height=32, corner_radius=4, fg_color=CARD_COLOR, border_color=BORDER_COLOR, text_color=TEXT_MAIN, button_color=CARD_COLOR, button_hover_color=BORDER_COLOR, font=("Segoe UI", 12))
        self.primary_cb.set(self.config.get("primary_output") if self.config.get("primary_output") in device_names else "Aucun")
        self.primary_cb.pack(anchor="w", padx=30, pady=5)
        
        ctk.CTkLabel(inner, text="Sortie Secondaire (VB-Cable / Discord) :", font=("Segoe UI", 12), text_color=TEXT_MUTED).pack(anchor="w", padx=30, pady=(20, 0))
        self.secondary_cb = ctk.CTkComboBox(inner, values=device_names, width=400, height=32, corner_radius=4, fg_color=CARD_COLOR, border_color=BORDER_COLOR, text_color=TEXT_MAIN, button_color=CARD_COLOR, button_hover_color=BORDER_COLOR, font=("Segoe UI", 12))
        self.secondary_cb.set(self.config.get("secondary_output") if self.config.get("secondary_output") in device_names else "Aucun")
        self.secondary_cb.pack(anchor="w", padx=30, pady=5)
        
        self.dual_var = ctk.BooleanVar(value=self.config.get("dual_output_enabled", False))
        ctk.CTkSwitch(inner, text="Activer la double sortie audio", variable=self.dual_var, font=("Segoe UI", 12), text_color=TEXT_MAIN, progress_color=ACCENT_COLOR).pack(anchor="w", padx=30, pady=(20, 10))
        
        ctk.CTkLabel(inner, text="Volume Sortie Secondaire (Discord) :", font=("Segoe UI", 12), text_color=TEXT_MUTED).pack(anchor="w", padx=30, pady=(5, 5))
        self.sec_vol_var = ctk.DoubleVar(value=self.config.get("global_secondary_volume", 100))
        vol_s_slider = ctk.CTkSlider(inner, from_=0, to=200, number_of_steps=20, variable=self.sec_vol_var, width=400, height=12, progress_color="#8B5CF6", fg_color=CARD_COLOR, button_color=TEXT_MAIN, button_hover_color="#FFFFFF")
        vol_s_slider.pack(anchor="w", padx=30, pady=0)
        self.sec_vol_lbl = ctk.CTkLabel(inner, text=f"{int(self.sec_vol_var.get())}%", font=("Segoe UI", 11), text_color=TEXT_MAIN)
        self.sec_vol_lbl.place(x=440, y=283)
        vol_s_slider.configure(command=lambda v: self.sec_vol_lbl.configure(text=f"{int(v)}%"))
        
        ctk.CTkLabel(inner, text="SYSTÈME", font=("Segoe UI", 16, "bold"), text_color=TEXT_MAIN).pack(anchor="w", padx=30, pady=(30, 10))
        
        ctk.CTkLabel(inner, text="Touche d'arrêt d'urgence (Panic Key) :", font=("Segoe UI", 12), text_color=TEXT_MUTED).pack(anchor="w", padx=30, pady=(10, 0))
        panic_val = self.config.get("panic_key", "pause").upper()
        self.panic_btn = ctk.CTkButton(inner, text=f"KEY: {panic_val}", width=200, height=32, corner_radius=4, font=("Segoe UI", 12, "bold"), fg_color="transparent", border_width=1, border_color=BORDER_COLOR, hover_color=CARD_COLOR, text_color=TEXT_MAIN, command=self.bind_panic_key)
        self.panic_btn.pack(anchor="w", padx=30, pady=5)
        
        self.solo_var = ctk.BooleanVar(value=self.config.get("mode_solo", False))
        ctk.CTkSwitch(inner, text="Mode Solo (Anti-superposition de sons)", variable=self.solo_var, font=("Segoe UI", 12), text_color=TEXT_MAIN, progress_color=ACCENT_COLOR).pack(anchor="w", padx=30, pady=20)
        
        ctk.CTkButton(inner, text="SAUVEGARDER", height=36, corner_radius=4, font=("Segoe UI", 12, "bold"), command=self.save_settings, fg_color="transparent", border_width=1, border_color=ACCENT_COLOR, hover_color=PANEL_COLOR, text_color=ACCENT_COLOR).pack(anchor="w", padx=30, pady=20)

    def bind_panic_key(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Assigner Raccourci")
        dialog.geometry("300x140")
        dialog.configure(fg_color=BG_COLOR)
        dialog.transient(self)
        dialog.grab_set()
        
        lbl = ctk.CTkLabel(dialog, text="Appuyez sur une touche ou combinaison...", font=("Segoe UI", 12), text_color=TEXT_MAIN)
        lbl.pack(expand=True, pady=15)
        
        btn_cancel = ctk.CTkButton(dialog, text="ANNULER", width=100, height=28, corner_radius=4, font=("Segoe UI", 11, "bold"), fg_color="transparent", border_width=1, border_color=BORDER_COLOR, hover_color=CARD_COLOR, text_color=TEXT_MUTED, command=dialog.destroy)
        btn_cancel.pack(pady=15)
        
        def capture_hotkey():
            import keyboard
            hk = keyboard.read_hotkey(suppress=False)
            self.after(0, lambda: apply_hotkey(hk))
            
        def apply_hotkey(hk):
            if not dialog.winfo_exists():
                return
            self.config["panic_key"] = hk
            if hasattr(self, 'panic_btn'):
                self.panic_btn.configure(text=f"KEY: {hk.upper()}")
            dialog.destroy()
            
        threading.Thread(target=capture_hotkey, daemon=True).start()

    def _build_discord_view(self):
        inner = ctk.CTkFrame(self.content_frame, fg_color=PANEL_COLOR, corner_radius=4, border_width=1, border_color=BORDER_COLOR)
        inner.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(inner, text="INSTALLATION DU CÂBLE VIRTUEL", font=("Segoe UI", 18, "bold"), text_color=TEXT_MAIN).pack(pady=(60, 10))
        ctk.CTkLabel(inner, text="Pour envoyer vos sons directement dans le micro de Discord,\nvous devez installer un Virtual Audio Cable.", font=("Segoe UI", 13), justify="center", text_color=TEXT_MUTED).pack(pady=10)
        
        ctk.CTkButton(inner, text="INSTALLER VB-CABLE", command=self.install_vbcable, width=200, height=36, corner_radius=4, font=("Segoe UI", 12, "bold"), fg_color="transparent", border_width=1, border_color=BORDER_COLOR, hover_color=CARD_COLOR, text_color=TEXT_MAIN).pack(pady=30)

    def update_sound_list(self):
        if not hasattr(self, 'sounds_scroll') or not self.sounds_scroll.winfo_exists():
            return
            
        self.play_buttons = {}
        for widget in self.sounds_scroll.winfo_children():
            widget.destroy()
            
        sounds = self.config.get("sounds", [])
        search_q = getattr(self, "search_var", ctk.StringVar()).get().lower()
        
        if search_q:
            sounds = [s for s in sounds if search_q in s["name"].lower()]
            
        if not sounds:
            empty_frame = ctk.CTkFrame(self.sounds_scroll, fg_color="transparent")
            empty_frame.pack(expand=True, fill="both", pady=100)
            
            if search_q:
                ctk.CTkLabel(empty_frame, text="Aucun résultat trouvé.", font=("Segoe UI", 16, "bold"), text_color=TEXT_MAIN).pack(pady=5)
                ctk.CTkLabel(empty_frame, text="Essayez un autre mot-clé.", font=("Segoe UI", 13), text_color=TEXT_MUTED).pack()
            else:
                ctk.CTkLabel(empty_frame, text="Votre bibliothèque est vide.", font=("Segoe UI", 18, "bold"), text_color=TEXT_MAIN).pack(pady=(0, 5))
                ctk.CTkLabel(empty_frame, text="Commencez par importer un fichier local\nou téléchargez un son depuis YouTube.", font=("Segoe UI", 14), text_color=TEXT_MUTED).pack(pady=5)
            return
            
        for sound in sounds:
            color_map = {
                "Gris": BORDER_COLOR,
                "Rouge (Troll)": DANGER_COLOR,
                "Bleu (Musique)": ACCENT_COLOR,
                "Vert (SFX)": "#10B981",
                "Violet (Voix)": "#8B5CF6",
                "Orange (Alerte)": "#F59E0B"
            }
            c_val = sound.get("color", "Gris")
            c_hex = color_map.get(c_val, BORDER_COLOR)
            
            card = ctk.CTkFrame(self.sounds_scroll, height=85, corner_radius=CR, fg_color=PANEL_COLOR, border_width=1, border_color=c_hex if c_val != "Gris" else BG_COLOR)
            card.pack(fill="x", pady=6, padx=5)
            card.pack_propagate(False)
            
            # Left Color Bar
            color_bar = ctk.CTkFrame(card, width=6, corner_radius=0, fg_color=c_hex)
            color_bar.pack(side="left", fill="y")
            
            # Left: Play button
            btn_play = ctk.CTkButton(card, text="PLAY", width=65, height=55, corner_radius=CR, font=("Segoe UI", 11, "bold"), fg_color=BG_COLOR, hover_color=CARD_COLOR, text_color=TEXT_MAIN, command=lambda s=sound: self.play_sound(s))
            btn_play.pack(side="left", padx=(15, 15), pady=15)
            self.play_buttons[sound["id"]] = btn_play
            
            # Center: Info & Sliders
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", expand=True, fill="both", padx=10, pady=10)
            
            # Name
            name_lbl = ctk.CTkLabel(info_frame, text=sound["name"][:45] + ("..." if len(sound["name"])>45 else ""), font=("Segoe UI", 14, "bold"), anchor="w", text_color=TEXT_MAIN)
            name_lbl.place(relx=0.0, rely=0.15, anchor="w")
            
            # Single Volume Slider & Speed
            vol_p = sound.get("volume", 100)
            spd = sound.get("speed", 100)
            
            sl_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            sl_frame.place(relx=0.0, rely=0.75, anchor="w", relwidth=1.0)
            
            # Vol
            ctk.CTkLabel(sl_frame, text=f"VOL:", width=35, anchor="w", font=("Segoe UI", 10, "bold"), text_color=TEXT_MUTED).pack(side="left")
            vol_p_slider = ctk.CTkSlider(sl_frame, from_=0, to=400, number_of_steps=40, height=8, width=100, progress_color=ACCENT_COLOR, fg_color=BG_COLOR, button_color=TEXT_MAIN, button_hover_color="#FFFFFF")
            vol_p_slider.set(vol_p)
            vol_p_slider.pack(side="left", padx=(0, 25))
            
            # Speed
            ctk.CTkLabel(sl_frame, text=f"VIT:", width=25, anchor="w", font=("Segoe UI", 10, "bold"), text_color=TEXT_MUTED).pack(side="left")
            spd_slider = ctk.CTkSlider(sl_frame, from_=50, to=200, number_of_steps=30, height=8, width=100, progress_color="#10B981", fg_color=BG_COLOR, button_color=TEXT_MAIN, button_hover_color="#FFFFFF")
            spd_slider.set(spd)
            spd_slider.pack(side="left", padx=(0, 25))
            
            # Color Dropdown
            color_combo = ctk.CTkComboBox(sl_frame, values=list(color_map.keys()), width=140, height=28, corner_radius=4, font=("Segoe UI", 11), dropdown_font=("Segoe UI", 11), fg_color=BG_COLOR, border_width=1, border_color=BORDER_COLOR, button_color=CARD_COLOR, button_hover_color=PANEL_COLOR)
            color_combo.set(c_val)
            color_combo.pack(side="left")
            
            # Right: Actions (Status, Bind, Delete)
            right_actions = ctk.CTkFrame(card, fg_color="transparent")
            right_actions.pack(side="right", padx=15, pady=15)
            
            status_lbl = ctk.CTkLabel(right_actions, text="", width=30, font=("Segoe UI", 12), text_color="#F59E0B")
            status_lbl.pack(side="left", padx=(0, 10))
            
            # Bind events to sliders for processing
            def on_slider_release(e, s=sound, vp=vol_p_slider, sp=spd_slider, ind=status_lbl):
                self.apply_audio(s["id"], vp.get(), sp.get(), ind)
                
            def on_color_change(choice, s=sound, c_bar=color_bar, crd=card):
                s["color"] = choice
                config_manager.save_config(self.config)
                # In-place update to prevent UI stutter
                new_hex = color_map.get(choice, BORDER_COLOR)
                c_bar.configure(fg_color=new_hex)
                crd.configure(border_color=new_hex if choice != "Gris" else BG_COLOR)
                
            vol_p_slider.bind("<ButtonRelease-1>", on_slider_release)
            spd_slider.bind("<ButtonRelease-1>", on_slider_release)
            color_combo.configure(command=on_color_change)
            
            hk_val = sound.get("hotkey", "Aucun").upper()
            hk_btn = ctk.CTkButton(right_actions, text=f"KEY: {hk_val}", width=80, height=28, corner_radius=4, font=("Segoe UI", 11, "bold"), fg_color=BG_COLOR, hover_color=CARD_COLOR, text_color=TEXT_MUTED)
            hk_btn.configure(command=lambda s=sound, b=hk_btn: self.bind_hotkey(s["id"], b))
            hk_btn.pack(side="left", padx=5)
            
            btn_del = ctk.CTkButton(right_actions, text="SUPP", width=45, height=28, corner_radius=4, font=("Segoe UI", 11, "bold"), fg_color="transparent", hover_color=DANGER_HOVER, text_color=DANGER_COLOR, command=lambda s=sound: self.remove_sound(s["id"]))
            btn_del.pack(side="left")

    def bind_hotkey(self, sound_id, hk_btn=None):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Assigner Raccourci")
        dialog.geometry("300x140")
        dialog.configure(fg_color=BG_COLOR)
        dialog.transient(self)
        dialog.grab_set()
        
        lbl = ctk.CTkLabel(dialog, text="Appuyez sur une touche ou combinaison...", font=("Segoe UI", 12), text_color=TEXT_MAIN)
        lbl.pack(expand=True, pady=15)
        
        btn_cancel = ctk.CTkButton(dialog, text="ANNULER", width=100, height=28, corner_radius=4, font=("Segoe UI", 11, "bold"), fg_color="transparent", border_width=1, border_color=BORDER_COLOR, hover_color=CARD_COLOR, text_color=TEXT_MUTED, command=dialog.destroy)
        btn_cancel.pack(pady=15)
        
        def capture_hotkey():
            import keyboard
            hk = keyboard.read_hotkey(suppress=False)
            self.after(0, lambda: apply_hotkey(hk))
            
        def apply_hotkey(hk):
            if hk == 'escape':
                dialog.destroy()
                return
            
            for s in self.config["sounds"]:
                if s["id"] == sound_id:
                    s["hotkey"] = hk
                    break
            config_manager.save_config(self.config)
            self.hotkey_manager.load_hotkeys(self.config)
            
            if hk_btn:
                hk_btn.configure(text=f"KEY: {hk.upper()}")
            dialog.destroy()
            
        threading.Thread(target=capture_hotkey, daemon=True).start()

    def apply_audio(self, sound_id, vol_p, spd, status_indicator):
        vol_p = int(vol_p)
        spd = int(spd)
        sound = next((s for s in self.config["sounds"] if s["id"] == sound_id), None)
        if not sound: return
        
        sound["volume"] = vol_p
        sound["speed"] = spd
        status_indicator.configure(text="~") # Processing indicator
        
        from audio_processor import process_audio_async
        import cache_manager
        
        def on_done(success, target_file, err):
            def ui_update():
                if success:
                    sound["cached_file_primary"] = target_file
                    config_manager.save_config(self.config)
                    self.hotkey_manager.load_hotkeys(self.config)
                    cache_manager.cleanup_caches(self.config)
                    status_indicator.configure(text="OK", text_color="#10B981")
                    self.after(2000, lambda: status_indicator.configure(text=""))
                else:
                    status_indicator.configure(text="ERR", text_color=DANGER_COLOR)
                    messagebox.showerror("Erreur Audio", str(err))
            self.after(0, ui_update)
            
        process_audio_async(sound.get("file"), vol_p, spd, on_done)

    def add_sound(self):
        filepath = filedialog.askopenfilename(filetypes=[("Fichiers Audio", "*.mp3 *.wav *.ogg *.flac")])
        if not filepath: return
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Importation")
        dialog.geometry("300x100")
        dialog.configure(fg_color=BG_COLOR)
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Importation et Normalisation en cours...", font=("Segoe UI", 12), text_color=TEXT_MAIN).pack(expand=True)
        
        def worker():
            try:
                from audio_processor import normalize_and_import_audio
                dl_dir = os.path.join(os.path.abspath("."), "library")
                base = os.path.basename(filepath).split('.')[0]
                final_path = normalize_and_import_audio(filepath, dl_dir, base)
                
                new_sound = {
                    "id": str(uuid.uuid4()),
                    "name": base,
                    "file": final_path,
                    "hotkey": "Aucun",
                    "volume": 100,
                    "speed": 100,
                    "color": "Gris"
                }
                self.config["sounds"].append(new_sound)
                config_manager.save_config(self.config)
                self.after(0, lambda: self.hotkey_manager.load_hotkeys(self.config))
                self.after(0, self.update_sound_list)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erreur Import", str(e)))
            finally:
                self.after(0, dialog.destroy)
                
        threading.Thread(target=worker, daemon=True).start()

    def remove_sound(self, sound_id):
        if not messagebox.askyesno("Supprimer", "Voulez-vous supprimer ce son ?"): return
        self.config["sounds"] = [s for s in self.config["sounds"] if s["id"] != sound_id]
        config_manager.save_config(self.config)
        self.hotkey_manager.load_hotkeys(self.config)
        self.update_sound_list()

    def play_sound(self, sound):
        vol_p = sound.get("volume", 100)
        spd = sound.get("speed", 100)
        global_sec_vol = self.config.get("global_secondary_volume", 100)
        vol_s = int(vol_p * (global_sec_vol / 100.0))
        
        original_file = sound.get("file")
        from audio_processor import generate_cached_file_sync
        try:
            filepath_sec = generate_cached_file_sync(original_file, vol_s, spd)
        except:
            filepath_sec = original_file
            
        if self.config.get("mode_solo", False):
            self.audio_manager.stop_all()
            
        self.audio_manager.toggle_play_pause(
            filepath_primary=sound.get("cached_file_primary") or sound.get("cached_file") or original_file,
            filepath_secondary=filepath_sec,
            name=sound["name"],
            volume=1.0,
            primary_device_name=self.config.get("primary_output"),
            secondary_device_name=self.config.get("secondary_output"),
            dual_enabled=self.config.get("dual_output_enabled", False),
            sound_id=sound["id"]
        )

    def download_youtube(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Télécharger URL")
        dialog.geometry("500x180")
        dialog.configure(fg_color=BG_COLOR)
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Lien YouTube ou YT Music :", font=("Segoe UI", 12), text_color=TEXT_MUTED).pack(pady=(15, 5))
        url_entry = ctk.CTkEntry(dialog, width=400, height=30, corner_radius=4, fg_color=CARD_COLOR, border_color=BORDER_COLOR, text_color=TEXT_MAIN, font=("Segoe UI", 12))
        url_entry.pack(pady=5)
        
        progress_bar = ctk.CTkProgressBar(dialog, width=400, height=4, progress_color=ACCENT_COLOR, fg_color=PANEL_COLOR)
        progress_bar.set(0)
        progress_bar.pack(pady=10)
        
        status_lbl = ctk.CTkLabel(dialog, text="", font=("Segoe UI", 11), text_color=TEXT_MUTED)
        status_lbl.pack()
        
        def start_dl():
            url = url_entry.get().strip()
            if not url: return
            btn.configure(state="disabled")
            status_lbl.configure(text="Récupération...")
            
            def progress_cb(percent_str, p_index, p_count, title):
                def update():
                    try:
                        clean = percent_str.replace('%', '').strip()
                        progress_bar.set(float(clean) / 100.0)
                    except: pass
                    status_lbl.configure(text=f"{percent_str} - {title[:35]}")
                dialog.after(0, update)
                
            def on_done(success, results, error):
                def finish():
                    if success:
                        for filepath, title in results:
                            new_sound = {
                                "id": str(uuid.uuid4()),
                                "name": title,
                                "file": filepath,
                                "hotkey": "Aucun",
                                "volume": 100,
                                "speed": 100,
                                "color": "Gris"
                            }
                            self.config["sounds"].append(new_sound)
                        config_manager.save_config(self.config)
                        self.hotkey_manager.load_hotkeys(self.config)
                        self.update_sound_list()
                        dialog.destroy()
                    else:
                        status_lbl.configure(text="Erreur !", text_color=DANGER_COLOR)
                        messagebox.showerror("Erreur", error)
                        btn.configure(state="normal")
                dialog.after(0, finish)
                
            dl_dir = os.path.join(os.path.abspath("."), "downloads")
            download_youtube_audio_async(url, dl_dir, on_done, progress_cb)
            
        btn = ctk.CTkButton(dialog, text="TELECHARGER", width=120, height=28, corner_radius=4, font=("Segoe UI", 11, "bold"), fg_color="transparent", border_width=1, border_color=ACCENT_COLOR, hover_color=PANEL_COLOR, text_color=ACCENT_COLOR, command=start_dl)
        btn.place(relx=0.5, rely=0.85, anchor="center")

    def save_settings(self):
        prim = self.primary_cb.get()
        sec = self.secondary_cb.get()
        self.config["primary_output"] = prim if prim != "Aucun" else None
        self.config["secondary_output"] = sec if sec != "Aucun" else None
        self.config["dual_output_enabled"] = self.dual_var.get()
        self.config["global_secondary_volume"] = int(self.sec_vol_var.get())
        self.config["mode_solo"] = self.solo_var.get()
        
        config_manager.save_config(self.config)
        import cache_manager
        cache_manager.cleanup_caches(self.config)
        self.hotkey_manager.load_hotkeys(self.config)
        messagebox.showinfo("Succès", "Paramètres sauvegardés !")

    def install_vbcable(self):
        if not messagebox.askyesno("VB-Cable", "Installer VB-Cable ? (Nécessite les droits administrateur)"):
            return
        from vbcable_installer import install_vbcable_async
        def on_done(success, error):
            if success:
                messagebox.showinfo("Succès", "Câble installé ! Redémarrez le logiciel pour l'utiliser.")
            else:
                messagebox.showerror("Erreur", str(error))
        install_vbcable_async(lambda x: None, on_done)
