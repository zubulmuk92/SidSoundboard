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

# PRO COLOR PALETTE
BG_COLOR = "#09090B"
PANEL_COLOR = "#18181B"
CARD_COLOR = "#27272A"
BORDER_COLOR = "#3F3F46"
ACCENT_COLOR = "#3B82F6"
ACCENT_HOVER = "#2563EB"
TEXT_MAIN = "#F4F4F5"
TEXT_MUTED = "#A1A1AA"
DANGER_COLOR = "#E11D48"
DANGER_HOVER = "#BE123C"

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
            
        self._build_ui()
        self.update_sound_list()

    def _build_ui(self):
        self.configure(fg_color=BG_COLOR)
        
        # Header (Top Bar)
        self.header_frame = ctk.CTkFrame(self, height=55, corner_radius=0, fg_color=PANEL_COLOR, border_width=1, border_color=BORDER_COLOR)
        self.header_frame.pack(fill="x", side="top")
        self.header_frame.pack_propagate(False)
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="SIDSOUNDBOARD", font=("Segoe UI", 15, "bold"), text_color=TEXT_MAIN, letter_spacing=1)
        self.title_label.pack(side="left", padx=20)
        
        self.stop_btn = ctk.CTkButton(self.header_frame, text="STOP AUDIO", width=110, height=28, corner_radius=4, font=("Segoe UI", 11, "bold"), fg_color=DANGER_COLOR, hover_color=DANGER_HOVER, text_color="#FFFFFF", command=self.audio_manager.stop_all)
        self.stop_btn.pack(side="right", padx=20)
        
        # Tabs
        self.tabview = ctk.CTkTabview(self, corner_radius=4, fg_color=BG_COLOR, 
                                      segmented_button_fg_color=PANEL_COLOR, 
                                      segmented_button_selected_color=ACCENT_COLOR, 
                                      segmented_button_selected_hover_color=ACCENT_HOVER,
                                      segmented_button_unselected_color=PANEL_COLOR,
                                      segmented_button_unselected_hover_color=CARD_COLOR,
                                      text_color=TEXT_MAIN, font=("Segoe UI", 12))
        self.tabview.pack(fill="both", expand=True, padx=15, pady=10)
        
        self.tabview.add("BIBLIOTHÈQUE")
        self.tabview.add("PARAMÈTRES")
        self.tabview.add("ROUTAGE")
        
        self._build_sounds_tab()
        self._build_settings_tab()
        self._build_discord_tab()

    def _build_sounds_tab(self):
        tab = self.tabview.tab("BIBLIOTHÈQUE")
        tab.configure(fg_color=BG_COLOR)
        
        # Toolbar
        toolbar = ctk.CTkFrame(tab, height=45, corner_radius=4, fg_color=PANEL_COLOR, border_width=1, border_color=BORDER_COLOR)
        toolbar.pack(fill="x", pady=(0, 10))
        toolbar.pack_propagate(False)
        
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self.update_sound_list())
        search_entry = ctk.CTkEntry(toolbar, textvariable=self.search_var, placeholder_text="Rechercher...", width=250, height=28, corner_radius=4, fg_color=CARD_COLOR, border_color=BORDER_COLOR, text_color=TEXT_MAIN, font=("Segoe UI", 12))
        search_entry.pack(side="left", padx=10)
        
        ctk.CTkButton(toolbar, text="IMPORT LOCAL", width=110, height=28, corner_radius=4, font=("Segoe UI", 11, "bold"), fg_color=CARD_COLOR, border_width=1, border_color=BORDER_COLOR, hover_color=BORDER_COLOR, text_color=TEXT_MAIN, command=self.add_sound).pack(side="right", padx=10)
        ctk.CTkButton(toolbar, text="TELECHARGER URL", width=130, height=28, corner_radius=4, font=("Segoe UI", 11, "bold"), fg_color=CARD_COLOR, border_width=1, border_color=BORDER_COLOR, hover_color=BORDER_COLOR, text_color=TEXT_MAIN, command=self.download_youtube).pack(side="right", padx=0)
        
        # List
        self.sounds_scroll = ctk.CTkScrollableFrame(tab, corner_radius=4, fg_color=PANEL_COLOR, border_width=1, border_color=BORDER_COLOR)
        self.sounds_scroll.pack(fill="both", expand=True, pady=(0, 10))
        
        # Global Player
        self.player_frame = ctk.CTkFrame(tab, height=45, corner_radius=4, fg_color=PANEL_COLOR, border_width=1, border_color=BORDER_COLOR)
        self.player_frame.pack(fill="x")
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
        self.after(100, self.update_timeline)

    def update_timeline(self):
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
                
        else:
            self.player_status_lbl.configure(text="EN ATTENTE", text_color=TEXT_MUTED)
            self.time_lbl.configure(text="0:00 / 0:00")
            if not getattr(self, 'is_scrubbing', False):
                self.timeline_var.set(0.0)
            
        self.after(100, self.update_timeline)

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

    def _build_settings_tab(self):
        tab = self.tabview.tab("PARAMÈTRES")
        tab.configure(fg_color=BG_COLOR)
        
        devices = self.audio_manager.get_output_devices()
        device_names = ["Aucun"] + [d["name"] for d in devices]
        
        inner = ctk.CTkFrame(tab, fg_color=PANEL_COLOR, corner_radius=4, border_width=1, border_color=BORDER_COLOR)
        inner.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(inner, text="ROUTAGE AUDIO", font=("Segoe UI", 14, "bold"), text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(inner, text="Sortie Principale (Casque / Haut-parleurs) :", font=("Segoe UI", 12), text_color=TEXT_MUTED).pack(anchor="w", padx=20, pady=(10, 0))
        self.primary_cb = ctk.CTkComboBox(inner, values=device_names, width=400, height=32, corner_radius=4, fg_color=CARD_COLOR, border_color=BORDER_COLOR, text_color=TEXT_MAIN, button_color=CARD_COLOR, button_hover_color=BORDER_COLOR, font=("Segoe UI", 12))
        self.primary_cb.set(self.config.get("primary_output") if self.config.get("primary_output") in device_names else "Aucun")
        self.primary_cb.pack(anchor="w", padx=20, pady=5)
        
        ctk.CTkLabel(inner, text="Sortie Secondaire (VB-Cable / Discord) :", font=("Segoe UI", 12), text_color=TEXT_MUTED).pack(anchor="w", padx=20, pady=(15, 0))
        self.secondary_cb = ctk.CTkComboBox(inner, values=device_names, width=400, height=32, corner_radius=4, fg_color=CARD_COLOR, border_color=BORDER_COLOR, text_color=TEXT_MAIN, button_color=CARD_COLOR, button_hover_color=BORDER_COLOR, font=("Segoe UI", 12))
        self.secondary_cb.set(self.config.get("secondary_output") if self.config.get("secondary_output") in device_names else "Aucun")
        self.secondary_cb.pack(anchor="w", padx=20, pady=5)
        
        self.dual_var = ctk.BooleanVar(value=self.config.get("dual_output_enabled", False))
        ctk.CTkSwitch(inner, text="Activer la double sortie audio", variable=self.dual_var, font=("Segoe UI", 12), text_color=TEXT_MAIN, progress_color=ACCENT_COLOR).pack(anchor="w", padx=20, pady=15)
        
        ctk.CTkLabel(inner, text="SYSTÈME", font=("Segoe UI", 14, "bold"), text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(30, 10))
        
        ctk.CTkLabel(inner, text="Touche d'arrêt d'urgence (Panic Key) :", font=("Segoe UI", 12), text_color=TEXT_MUTED).pack(anchor="w", padx=20, pady=(10, 0))
        self.panic_entry = ctk.CTkEntry(inner, width=200, height=32, corner_radius=4, fg_color=CARD_COLOR, border_color=BORDER_COLOR, text_color=TEXT_MAIN, font=("Segoe UI", 12))
        self.panic_entry.insert(0, self.config.get("panic_key", "pause"))
        self.panic_entry.pack(anchor="w", padx=20, pady=5)
        
        ctk.CTkButton(inner, text="SAUVEGARDER", height=36, corner_radius=4, font=("Segoe UI", 12, "bold"), command=self.save_settings, fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER, text_color="#FFFFFF").pack(anchor="w", padx=20, pady=30)

    def _build_discord_tab(self):
        tab = self.tabview.tab("ROUTAGE")
        tab.configure(fg_color=BG_COLOR)
        
        inner = ctk.CTkFrame(tab, fg_color=PANEL_COLOR, corner_radius=4, border_width=1, border_color=BORDER_COLOR)
        inner.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(inner, text="INSTALLATION DU CÂBLE VIRTUEL", font=("Segoe UI", 16, "bold"), text_color=TEXT_MAIN).pack(pady=(40, 10))
        ctk.CTkLabel(inner, text="Pour envoyer vos sons directement dans le micro de Discord,\nvous devez installer un Virtual Audio Cable.", font=("Segoe UI", 12), justify="center", text_color=TEXT_MUTED).pack(pady=10)
        
        ctk.CTkButton(inner, text="INSTALLER VB-CABLE", command=self.install_vbcable, width=200, height=36, corner_radius=4, font=("Segoe UI", 12, "bold"), fg_color=CARD_COLOR, border_width=1, border_color=BORDER_COLOR, hover_color=BORDER_COLOR, text_color=TEXT_MAIN).pack(pady=30)

    def update_sound_list(self):
        for widget in self.sounds_scroll.winfo_children():
            widget.destroy()
            
        sounds = self.config.get("sounds", [])
        search_q = getattr(self, "search_var", ctk.StringVar()).get().lower()
        
        if search_q:
            sounds = [s for s in sounds if search_q in s["name"].lower()]
            
        if not sounds:
            txt = "Aucun résultat." if search_q else "La bibliothèque est vide."
            ctk.CTkLabel(self.sounds_scroll, text=txt, font=("Segoe UI", 13), text_color=TEXT_MUTED).pack(pady=50)
            return
            
        for sound in sounds:
            card = ctk.CTkFrame(self.sounds_scroll, height=65, corner_radius=4, fg_color=CARD_COLOR, border_width=1, border_color=BORDER_COLOR)
            card.pack(fill="x", pady=4, padx=5)
            card.pack_propagate(False)
            
            # Left: Play button
            btn_play = ctk.CTkButton(card, text="PLAY", width=60, height=45, corner_radius=4, font=("Segoe UI", 11, "bold"), fg_color=PANEL_COLOR, border_width=1, border_color=BORDER_COLOR, hover_color=BORDER_COLOR, text_color=TEXT_MAIN, command=lambda s=sound: self.play_sound(s))
            btn_play.pack(side="left", padx=10, pady=10)
            
            # Center: Info & Sliders
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", expand=True, fill="both", padx=10)
            
            # Name
            name_lbl = ctk.CTkLabel(info_frame, text=sound["name"][:45] + ("..." if len(sound["name"])>45 else ""), font=("Segoe UI", 13, "bold"), anchor="w", text_color=TEXT_MAIN)
            name_lbl.place(relx=0.0, rely=0.2, anchor="w")
            
            # Sliders (compact)
            vol = sound.get("volume", 100)
            spd = sound.get("speed", 100)
            
            sl_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            sl_frame.place(relx=0.0, rely=0.7, anchor="w", relwidth=1.0)
            
            # Vol
            vol_lbl = ctk.CTkLabel(sl_frame, text=f"VOL: {vol}%", width=55, anchor="w", font=("Segoe UI", 10), text_color=TEXT_MUTED)
            vol_lbl.pack(side="left")
            vol_slider = ctk.CTkSlider(sl_frame, from_=10, to=400, number_of_steps=39, height=6, width=100, progress_color=ACCENT_COLOR, fg_color=PANEL_COLOR, button_color=TEXT_MAIN, button_hover_color="#FFFFFF")
            vol_slider.set(vol)
            vol_slider.configure(command=lambda v, l=vol_lbl: l.configure(text=f"VOL: {int(v)}%"))
            vol_slider.pack(side="left", padx=(0, 20))
            
            # Speed
            spd_lbl = ctk.CTkLabel(sl_frame, text=f"VIT: {spd}%", width=55, anchor="w", font=("Segoe UI", 10), text_color=TEXT_MUTED)
            spd_lbl.pack(side="left")
            spd_slider = ctk.CTkSlider(sl_frame, from_=50, to=200, number_of_steps=30, height=6, width=100, progress_color="#10B981", fg_color=PANEL_COLOR, button_color=TEXT_MAIN, button_hover_color="#FFFFFF")
            spd_slider.set(spd)
            spd_slider.configure(command=lambda v, l=spd_lbl: l.configure(text=f"VIT: {int(v)}%"))
            spd_slider.pack(side="left")
            
            # Right: Actions (Status, Bind, Delete)
            right_actions = ctk.CTkFrame(card, fg_color="transparent")
            right_actions.pack(side="right", padx=10, pady=10)
            
            status_lbl = ctk.CTkLabel(right_actions, text="", width=20, font=("Segoe UI", 12), text_color="#F59E0B")
            status_lbl.pack(side="left", padx=(0, 10))
            
            # Bind events to sliders for processing
            vol_slider.bind("<ButtonRelease-1>", lambda e, s=sound, v_s=vol_slider, s_s=spd_slider, ind=status_lbl: self.apply_audio(s["id"], v_s.get(), s_s.get(), ind))
            spd_slider.bind("<ButtonRelease-1>", lambda e, s=sound, v_s=vol_slider, s_s=spd_slider, ind=status_lbl: self.apply_audio(s["id"], v_s.get(), s_s.get(), ind))
            
            hk_val = sound.get("hotkey", "Aucun").upper()
            hk_btn = ctk.CTkButton(right_actions, text=f"KEY: {hk_val}", width=90, height=28, corner_radius=4, font=("Segoe UI", 10, "bold"), fg_color=PANEL_COLOR, border_width=1, border_color=BORDER_COLOR, hover_color=BORDER_COLOR, text_color=TEXT_MUTED, command=lambda s=sound: self.bind_hotkey(s["id"]))
            hk_btn.pack(side="left", padx=5)
            
            btn_del = ctk.CTkButton(right_actions, text="SUPP", width=45, height=28, corner_radius=4, font=("Segoe UI", 10, "bold"), fg_color=PANEL_COLOR, border_width=1, border_color=BORDER_COLOR, hover_color=DANGER_HOVER, text_color=DANGER_COLOR, command=lambda s=sound: self.remove_sound(s["id"]))
            btn_del.pack(side="left")

    def bind_hotkey(self, sound_id):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Assigner Raccourci")
        dialog.geometry("300x140")
        dialog.configure(fg_color=BG_COLOR)
        dialog.transient(self)
        dialog.grab_set()
        
        lbl = ctk.CTkLabel(dialog, text="Appuyez sur une touche ou combinaison...", font=("Segoe UI", 12), text_color=TEXT_MAIN)
        lbl.pack(expand=True, pady=15)
        
        btn_cancel = ctk.CTkButton(dialog, text="ANNULER", width=100, height=28, corner_radius=4, font=("Segoe UI", 11, "bold"), fg_color=PANEL_COLOR, border_width=1, border_color=BORDER_COLOR, hover_color=BORDER_COLOR, text_color=TEXT_MUTED, command=dialog.destroy)
        btn_cancel.pack(pady=15)
        
        def capture_hotkey():
            import keyboard
            hk = keyboard.read_hotkey(suppress=False)
            self.after(0, lambda: apply_hotkey(hk))
            
        def apply_hotkey(hk):
            if not dialog.winfo_exists():
                return
            sound = next((s for s in self.config["sounds"] if s["id"] == sound_id), None)
            if sound:
                sound["hotkey"] = hk
                config_manager.save_config(self.config)
                self.hotkey_manager.load_hotkeys(self.config)
                self.update_sound_list()
            dialog.destroy()
            
        threading.Thread(target=capture_hotkey, daemon=True).start()

    def apply_audio(self, sound_id, vol, spd, status_indicator):
        vol = int(vol)
        spd = int(spd)
        sound = next((s for s in self.config["sounds"] if s["id"] == sound_id), None)
        if not sound: return
        
        sound["volume"] = vol
        sound["speed"] = spd
        status_indicator.configure(text="~") # Processing indicator
        
        from audio_processor import process_audio_async
        def on_done(success, target_file, err):
            def ui_update():
                if success:
                    sound["cached_file"] = target_file
                    config_manager.save_config(self.config)
                    self.hotkey_manager.load_hotkeys(self.config)
                    status_indicator.configure(text="OK", text_color="#10B981")
                    self.after(2000, lambda: status_indicator.configure(text=""))
                else:
                    status_indicator.configure(text="ERR", text_color=DANGER_COLOR)
                    messagebox.showerror("Erreur Audio", str(err))
            self.after(0, ui_update)
            
        process_audio_async(sound.get("file"), vol, spd, on_done)

    def add_sound(self):
        filepath = filedialog.askopenfilename(filetypes=[("Fichiers Audio", "*.mp3 *.wav *.ogg *.flac")])
        if not filepath: return
        new_sound = {
            "id": str(uuid.uuid4()),
            "name": os.path.basename(filepath).split('.')[0],
            "file": filepath,
            "hotkey": "Aucun",
            "volume": 100,
            "speed": 100
        }
        self.config["sounds"].append(new_sound)
        config_manager.save_config(self.config)
        self.hotkey_manager.load_hotkeys(self.config)
        self.update_sound_list()

    def remove_sound(self, sound_id):
        if not messagebox.askyesno("Supprimer", "Voulez-vous supprimer ce son ?"): return
        self.config["sounds"] = [s for s in self.config["sounds"] if s["id"] != sound_id]
        config_manager.save_config(self.config)
        self.hotkey_manager.load_hotkeys(self.config)
        self.update_sound_list()

    def play_sound(self, sound):
        self.audio_manager.stop_all()
        self.audio_manager.play_sound(
            filepath=sound.get("cached_file") or sound.get("file"),
            name=sound["name"],
            volume=1.0,
            primary_device_name=self.config.get("primary_output"),
            secondary_device_name=self.config.get("secondary_output"),
            dual_enabled=self.config.get("dual_output_enabled", False)
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
                                "speed": 100
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
            
        btn = ctk.CTkButton(dialog, text="TELECHARGER", width=120, height=28, corner_radius=4, font=("Segoe UI", 11, "bold"), fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER, text_color="#FFFFFF", command=start_dl)
        btn.place(relx=0.5, rely=0.85, anchor="center")

    def save_settings(self):
        prim = self.primary_cb.get()
        sec = self.secondary_cb.get()
        self.config["primary_output"] = prim if prim != "Aucun" else None
        self.config["secondary_output"] = sec if sec != "Aucun" else None
        self.config["dual_output_enabled"] = self.dual_var.get()
        self.config["panic_key"] = self.panic_entry.get()
        
        config_manager.save_config(self.config)
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
