import customtkinter as ctk
from tkinter import filedialog, messagebox
import uuid
import os
import sys
import keyboard
import threading
from PIL import Image
from yt_downloader import download_youtube_audio_async
import config_manager

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Configuration de CustomTkinter
ctk.set_appearance_mode("Dark")  # Thème sombre profond
ctk.set_default_color_theme("blue")  # Accents bleu / cyan

class AppGUI(ctk.CTk):
    def __init__(self, audio_manager, hotkey_manager):
        super().__init__()
        
        self.audio_manager = audio_manager
        self.hotkey_manager = hotkey_manager
        self.config = config_manager.load_config()
        
        self.title("SidSoundboard - Premium Edition")
        self.geometry("800x600")
        
        try:
            self.iconbitmap(resource_path("logo.ico"))
        except Exception:
            pass
            
        self._build_ui()
        self.update_sound_list()

    def _build_ui(self):
        # Configure le fond principal de l'application
        self.configure(fg_color="#061121")
        
        # Header principal
        self.header_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="SidSoundboard - Ice Age", font=ctk.CTkFont(size=24, weight="bold"), text_color="#CAF0F8")
        self.title_label.pack(side="left")
        
        self.stop_btn = ctk.CTkButton(self.header_frame, text="⏹ Stop Tout", fg_color="#D90429", hover_color="#8D0801", text_color="#FFFFFF", command=self.audio_manager.stop_all)
        self.stop_btn.pack(side="right")
        
        # Onglets (Tabs)
        self.tabview = ctk.CTkTabview(self, fg_color="#0B1320", segmented_button_fg_color="#112236", segmented_button_selected_color="#0077B6", segmented_button_selected_hover_color="#03045E")
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.tabview.add("Mes Sons")
        self.tabview.add("Paramètres")
        self.tabview.add("Discord")
        
        self._build_sounds_tab()
        self._build_settings_tab()
        self._build_discord_tab()

    def _build_sounds_tab(self):
        tab = self.tabview.tab("Mes Sons")
        tab.configure(fg_color="#0B1121") # Modern Dark Blue
        
        # Barre d'actions en haut
        action_frame = ctk.CTkFrame(tab, fg_color="transparent")
        action_frame.pack(fill="x", pady=5)
        
        # Search Bar
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self.update_sound_list())
        search_entry = ctk.CTkEntry(action_frame, textvariable=self.search_var, placeholder_text="🔍 Rechercher un son...", width=300, height=36, corner_radius=18, fg_color="#151E32", border_color="#1E2B43", text_color="#F1F5F9", font=("Segoe UI", 13))
        search_entry.pack(side="left", padx=5)
        
        # Boutons d'ajout alignés à droite
        ctk.CTkButton(action_frame, text="+ Fichier Local", width=120, height=36, corner_radius=18, font=("Segoe UI", 13, "bold"), fg_color="#0EA5E9", hover_color="#0284C7", text_color="#F1F5F9", command=self.add_sound).pack(side="right", padx=5)
        ctk.CTkButton(action_frame, text="▶ YouTube", width=120, height=36, corner_radius=18, font=("Segoe UI", 13, "bold"), fg_color="#EF4444", hover_color="#B91C1C", text_color="#F1F5F9", command=self.download_youtube).pack(side="right", padx=5)
        
        # Zone des sons (Scrollable)
        self.sounds_scroll = ctk.CTkScrollableFrame(tab, corner_radius=10, fg_color="transparent")
        self.sounds_scroll.pack(fill="both", expand=True, pady=(15, 0))
        
        # LECTEUR GLOBAL (En bas)
        self.player_frame = ctk.CTkFrame(tab, height=65, corner_radius=15, fg_color="#151E32", border_width=1, border_color="#1E2B43")
        self.player_frame.pack(fill="x", pady=(10, 5))
        self.player_frame.pack_propagate(False)
        
        self.player_status_lbl = ctk.CTkLabel(self.player_frame, text="🔇 Aucun son en cours...", font=("Segoe UI", 14, "bold"), text_color="#38BDF8")
        self.player_status_lbl.pack(side="left", padx=20)
        
        self.timeline_var = ctk.DoubleVar(value=0.0)
        self.timeline_slider = ctk.CTkSlider(self.player_frame, from_=0, to=100, variable=self.timeline_var, command=self.on_timeline_seek, progress_color="#0EA5E9", button_color="#38BDF8", button_hover_color="#BAE6FD", height=14)
        self.timeline_slider.pack(side="left", expand=True, fill="x", padx=15)
        
        self.time_lbl = ctk.CTkLabel(self.player_frame, text="0:00 / 0:00", width=80, font=("Segoe UI", 13), text_color="#94A3B8")
        self.time_lbl.pack(side="right", padx=20)
        
        # Lancer la boucle de mise à jour
        self.is_scrubbing = False
        self._seek_after_id = None
        self.after(100, self.update_timeline)

    def update_timeline(self):
        progress = self.audio_manager.get_focused_progress()
        if progress:
            self.player_status_lbl.configure(text=f"🔊 {progress['name']}")
            
            # Format time
            cur = int(progress['current'])
            tot = int(progress['duration'])
            if cur > tot: cur = tot
            
            cur_m, cur_s = divmod(cur, 60)
            tot_m, tot_s = divmod(tot, 60)
            self.time_lbl.configure(text=f"{cur_m}:{cur_s:02d} / {tot_m}:{tot_s:02d}")
            
            if tot > 0 and not getattr(self, 'is_scrubbing', False):
                self.timeline_var.set((progress['current'] / tot) * 100)
                
        else:
            self.player_status_lbl.configure(text="🔇 Aucun son en cours...")
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
        tab = self.tabview.tab("Paramètres")
        tab.configure(fg_color="#0B1121")
        
        devices = self.audio_manager.get_output_devices()
        device_names = ["Aucun"] + [d["name"] for d in devices]
        
        ctk.CTkLabel(tab, text="Sortie Principale :", font=("Segoe UI", 13), text_color="#94A3B8").pack(anchor="w", pady=(10, 0))
        self.primary_cb = ctk.CTkComboBox(tab, values=device_names, width=400, height=36, corner_radius=8, fg_color="#151E32", border_color="#1E2B43", text_color="#F1F5F9", button_color="#0EA5E9", button_hover_color="#0284C7", font=("Segoe UI", 13))
        if self.config.get("primary_output") in device_names:
            self.primary_cb.set(self.config.get("primary_output"))
        else:
            self.primary_cb.set("Aucun")
        self.primary_cb.pack(anchor="w", pady=5)
        
        ctk.CTkLabel(tab, text="Sortie Secondaire :", font=("Segoe UI", 13), text_color="#94A3B8").pack(anchor="w", pady=(10, 0))
        self.secondary_cb = ctk.CTkComboBox(tab, values=device_names, width=400, height=36, corner_radius=8, fg_color="#151E32", border_color="#1E2B43", text_color="#F1F5F9", button_color="#0EA5E9", button_hover_color="#0284C7", font=("Segoe UI", 13))
        if self.config.get("secondary_output") in device_names:
            self.secondary_cb.set(self.config.get("secondary_output"))
        else:
            self.secondary_cb.set("Aucun")
        self.secondary_cb.pack(anchor="w", pady=5)
        
        self.dual_var = ctk.BooleanVar(value=self.config.get("dual_output_enabled", False))
        ctk.CTkSwitch(tab, text="Activer le Double Output", variable=self.dual_var, font=("Segoe UI", 13), text_color="#F1F5F9", progress_color="#0EA5E9").pack(anchor="w", pady=15)
        
        self.single_mode_var = ctk.BooleanVar(value=self.config.get("single_mode", False))
        ctk.CTkSwitch(tab, text="Un seul son à la fois (Mode Exclusif)", variable=self.single_mode_var, font=("Segoe UI", 13), text_color="#F1F5F9", progress_color="#0EA5E9").pack(anchor="w", pady=5)
        
        ctk.CTkLabel(tab, text="Touche Panique Globale :", font=("Segoe UI", 13), text_color="#94A3B8").pack(anchor="w", pady=(15, 0))
        self.panic_entry = ctk.CTkEntry(tab, width=200, height=36, corner_radius=8, fg_color="#151E32", border_color="#1E2B43", text_color="#F1F5F9", font=("Segoe UI", 13))
        self.panic_entry.insert(0, self.config.get("panic_key", "pause"))
        self.panic_entry.pack(anchor="w", pady=5)
        
        ctk.CTkButton(tab, text="💾 Sauvegarder", height=40, corner_radius=20, font=("Segoe UI", 14, "bold"), command=self.save_settings, fg_color="#0EA5E9", hover_color="#0284C7", text_color="#F1F5F9").pack(pady=30)

    def _build_discord_tab(self):
        tab = self.tabview.tab("Discord")
        tab.configure(fg_color="#0B1121")
        
        ctk.CTkLabel(tab, text="Installation du Câble Virtuel pour Discord", font=("Segoe UI", 20, "bold"), text_color="#38BDF8").pack(pady=30)
        ctk.CTkLabel(tab, text="Pour envoyer vos sons directement dans le micro de Discord,\nvous devez installer le câble VB-Audio.", font=("Segoe UI", 14), justify="center", text_color="#94A3B8").pack(pady=10)
        
        ctk.CTkButton(tab, text="⚙ Installer VB-Cable", command=self.install_vbcable, width=250, height=45, corner_radius=22, font=("Segoe UI", 15, "bold"), fg_color="#0EA5E9", hover_color="#0284C7", text_color="#F1F5F9").pack(pady=30)

    def update_sound_list(self):
        # Vider la liste
        for widget in self.sounds_scroll.winfo_children():
            widget.destroy()
            
        sounds = self.config.get("sounds", [])
        search_q = getattr(self, "search_var", ctk.StringVar()).get().lower()
        
        if search_q:
            sounds = [s for s in sounds if search_q in s["name"].lower()]
            
        if not sounds:
            txt = "Aucun son trouvé." if search_q else "Aucun son. Ajoutez-en un !"
            ctk.CTkLabel(self.sounds_scroll, text=txt, font=("Segoe UI", 15), text_color="#94A3B8").pack(pady=50)
            return
            
        for sound in sounds:
            card = ctk.CTkFrame(self.sounds_scroll, corner_radius=15, fg_color="#151E32", border_width=1, border_color="#1E2B43")
            card.pack(fill="x", pady=6, padx=5)
            
            # Row unifiée
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=15)
            
            # Bouton Play - Big pill
            btn_play = ctk.CTkButton(row, text="▶", width=50, height=50, corner_radius=25, font=("Segoe UI", 22), fg_color="#0EA5E9", hover_color="#0284C7", text_color="#FFFFFF", command=lambda s=sound: self.play_sound(s))
            btn_play.pack(side="left")
            
            # Info Center
            info_frame = ctk.CTkFrame(row, fg_color="transparent")
            info_frame.pack(side="left", expand=True, fill="both", padx=20)
            
            # Titre + Hotkey
            top_info = ctk.CTkFrame(info_frame, fg_color="transparent")
            top_info.pack(fill="x")
            
            name_lbl = ctk.CTkLabel(top_info, text=sound["name"], font=("Segoe UI", 16, "bold"), anchor="w", text_color="#F1F5F9")
            name_lbl.pack(side="left")
            
            hk_btn = ctk.CTkButton(top_info, text=f"⌨ {sound.get('hotkey', 'Aucun')}", width=70, height=26, corner_radius=13, font=("Segoe UI", 12), fg_color="#1E2B43", hover_color="#334155", text_color="#94A3B8", command=lambda s=sound: self.bind_hotkey(s["id"]))
            hk_btn.pack(side="left", padx=15)
            
            # Sliders
            vol = sound.get("volume", 100)
            spd = sound.get("speed", 100)
            
            bot_info = ctk.CTkFrame(info_frame, fg_color="transparent")
            bot_info.pack(fill="x", pady=(8, 0))
            
            vol_lbl = ctk.CTkLabel(bot_info, text=f"Vol: {vol}%", width=65, anchor="w", font=("Segoe UI", 12), text_color="#94A3B8")
            vol_lbl.pack(side="left")
            vol_slider = ctk.CTkSlider(bot_info, from_=10, to=400, number_of_steps=39, height=10, width=120, progress_color="#0EA5E9", button_color="#38BDF8", button_hover_color="#BAE6FD")
            vol_slider.set(vol)
            vol_slider.configure(command=lambda v, l=vol_lbl: l.configure(text=f"Vol: {int(v)}%"))
            vol_slider.pack(side="left", padx=(0, 20))
            
            spd_lbl = ctk.CTkLabel(bot_info, text=f"Vit: {spd}%", width=65, anchor="w", font=("Segoe UI", 12), text_color="#94A3B8")
            spd_lbl.pack(side="left")
            spd_slider = ctk.CTkSlider(bot_info, from_=50, to=200, number_of_steps=30, height=10, width=120, progress_color="#10B981", button_color="#34D399", button_hover_color="#6EE7B7")
            spd_slider.set(spd)
            spd_slider.configure(command=lambda v, l=spd_lbl: l.configure(text=f"Vit: {int(v)}%"))
            spd_slider.pack(side="left")
            
            # Actions de droite (Apply & Delete)
            right_actions = ctk.CTkFrame(row, fg_color="transparent")
            right_actions.pack(side="right")
            
            # Status Indicator for processing
            status_lbl = ctk.CTkLabel(right_actions, text="", width=30, text_color="#F59E0B")
            status_lbl.pack(side="left", padx=4)
            
            # Auto-apply binding on release
            vol_slider.bind("<ButtonRelease-1>", lambda e, s=sound, v_s=vol_slider, s_s=spd_slider, ind=status_lbl: self.apply_audio(s["id"], v_s.get(), s_s.get(), ind))
            spd_slider.bind("<ButtonRelease-1>", lambda e, s=sound, v_s=vol_slider, s_s=spd_slider, ind=status_lbl: self.apply_audio(s["id"], v_s.get(), s_s.get(), ind))
            
            btn_del = ctk.CTkButton(right_actions, text="🗑", width=42, height=42, corner_radius=10, font=("Segoe UI", 16), fg_color="#1E2B43", hover_color="#EF4444", text_color="#F1F5F9", command=lambda s=sound: self.remove_sound(s["id"]))
            btn_del.pack(side="left", padx=4)

    def bind_hotkey(self, sound_id):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Raccourci")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()
        
        lbl = ctk.CTkLabel(dialog, text="Appuyez sur une touche...", font=ctk.CTkFont(size=16))
        lbl.pack(expand=True)
        
        detected = ["Aucun"]
        def on_key(e):
            detected[0] = e.name
            lbl.configure(text=f"Touche : {e.name}")
            
        hook = keyboard.on_press(on_key)
        
        def valider():
            keyboard.unhook(hook)
            sound = next((s for s in self.config["sounds"] if s["id"] == sound_id), None)
            if sound:
                sound["hotkey"] = detected[0]
                config_manager.save_config(self.config)
                self.hotkey_manager.load_hotkeys(self.config)
                self.update_sound_list()
            dialog.destroy()
            
        ctk.CTkButton(dialog, text="✔ Valider", command=valider).pack(pady=10)

    def apply_audio(self, sound_id, vol, spd, status_indicator):
        vol = int(vol)
        spd = int(spd)
        
        sound = next((s for s in self.config["sounds"] if s["id"] == sound_id), None)
        if not sound: return
        
        sound["volume"] = vol
        sound["speed"] = spd
        
        status_indicator.configure(text="⏳")
        
        from audio_processor import process_audio_async
        
        def on_done(success, target_file, err):
            def ui_update():
                if success:
                    sound["cached_file"] = target_file
                    config_manager.save_config(self.config)
                    self.hotkey_manager.load_hotkeys(self.config)
                    status_indicator.configure(text="✔", text_color="#10B981")
                    # Effacer le check après 2s
                    self.after(2000, lambda: status_indicator.configure(text=""))
                else:
                    status_indicator.configure(text="❌", text_color="#EF4444")
                    messagebox.showerror("Erreur Audio", str(err))
            # Toujours mettre à jour l'UI dans le thread principal
            self.after(0, ui_update)
            
        process_audio_async(sound.get("file"), vol, spd, on_done)

    def add_sound(self):
        filepath = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav *.ogg *.flac")])
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
        if not messagebox.askyesno("Supprimer", "Supprimer ce son ?"): return
        self.config["sounds"] = [s for s in self.config["sounds"] if s["id"] != sound_id]
        config_manager.save_config(self.config)
        self.hotkey_manager.load_hotkeys(self.config)
        self.update_sound_list()

    def play_sound(self, sound):
        if self.config.get("single_mode"):
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
        dialog.title("Télécharger YouTube")
        dialog.geometry("500x200")
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Lien YouTube ou YT Music :").pack(pady=10)
        url_entry = ctk.CTkEntry(dialog, width=400)
        url_entry.pack(pady=5)
        
        progress_bar = ctk.CTkProgressBar(dialog, width=400)
        progress_bar.set(0)
        progress_bar.pack(pady=10)
        
        status_lbl = ctk.CTkLabel(dialog, text="")
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
                    status_lbl.configure(text=f"{percent_str} - {title[:30]}")
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
                        status_lbl.configure(text="Erreur !", text_color="red")
                        messagebox.showerror("Erreur", error)
                        btn.configure(state="normal")
                dialog.after(0, finish)
                
            dl_dir = os.path.join(os.path.abspath("."), "downloads")
            download_youtube_audio_async(url, dl_dir, on_done, progress_cb)
            
        btn = ctk.CTkButton(dialog, text="Télécharger", fg_color="#cc0000", hover_color="#990000", command=start_dl)
        btn.pack(pady=10)

    def save_settings(self):
        prim = self.primary_cb.get()
        sec = self.secondary_cb.get()
        self.config["primary_output"] = prim if prim != "Aucun" else None
        self.config["secondary_output"] = sec if sec != "Aucun" else None
        self.config["dual_output_enabled"] = self.dual_var.get()
        self.config["single_mode"] = self.single_mode_var.get()
        self.config["panic_key"] = self.panic_entry.get()
        
        config_manager.save_config(self.config)
        self.hotkey_manager.load_hotkeys(self.config)
        messagebox.showinfo("Succès", "Paramètres sauvegardés !")

    def install_vbcable(self):
        if not messagebox.askyesno("VB-Cable", "Installer VB-Cable ? (Ça prend quelques secondes)"):
            return
            
        from vbcable_installer import install_vbcable_async
        def on_done(success, error):
            if success:
                messagebox.showinfo("Succès", "Câble installé ! Redémarrez le logiciel pour voir le périphérique.")
            else:
                messagebox.showerror("Erreur", str(error))
                
        install_vbcable_async(lambda x: None, on_done)
