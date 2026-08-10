# SidSoundboard 🎵

SidSoundboard est une application Windows légère, moderne et performante de Soundboard. 
Conçue avec Python et CustomTkinter, elle permet de lire instantanément vos sons préférés avec une interface élégante et minimaliste, tout en gardant une empreinte mémoire extrêmement faible (< 30 Mo de RAM).

## ✨ Fonctionnalités

*   **Design Premium** : Interface sombre moderne, fluide et réactive.
*   **Téléchargement YouTube** : Téléchargez directement l'audio depuis une vidéo YouTube via l'URL, avec extraction ultra-rapide.
*   **Raccourcis Clavier (Hotkeys)** : Assignez des touches globales pour jouer des sons même en plein jeu ou dans une autre application.
*   **Contrôle en Temps Réel** : Modifiez le volume global ou la vitesse de lecture (Pitch/Speed) à la volée.
*   **Application d'Arrière-Plan** : L'application peut être réduite dans la zone de notification Windows (System Tray) pour rester discrète mais toujours active.
*   **Haute Performance** : Traitement asynchrone et utilisation de `miniaudio` et `FFmpeg` pour une latence minimale.

## 🚀 Installation & Utilisation

L'application est disponible sous la forme d'un exécutable unique, sans installation requise :

1. Téléchargez la dernière version compilée (ou compilez-la vous-même).
2. Lancez `SidSoundboard.exe`.
3. Ajoutez vos sons (MP3, WAV, OGG) manuellement dans le dossier `cache/` ou utilisez le téléchargeur YouTube intégré.
4. Assignez vos touches via l'interface et profitez !

## 🛠️ Compilation à partir des sources

Si vous souhaitez modifier le code ou recompiler l'exécutable vous-même :

1.  **Prérequis** :
    *   Python 3.10+
    *   `ffmpeg` installé (ou géré via le module `static_ffmpeg`)
2.  **Installation des dépendances** :
    ```bash
    pip install -r requirements.txt
    ```
3.  **Compilation** :
    Utilisez PyInstaller pour générer l'exécutable :
    ```bash
    python -m PyInstaller --noconfirm --onefile --windowed --icon=logo.ico --add-data "logo_sq.png;." --add-data "logo.ico;." --hidden-import _cffi_backend --hidden-import cffi --hidden-import static_ffmpeg --hidden-import audio_processor --name "SidSoundboard" main.py
    ```

## ⚙️ Technologies Utilisées

*   [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Interface graphique moderne
*   [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Téléchargement YouTube
*   [Miniaudio](https://github.com/dr-ni/miniaudio) - Lecture audio ultra-rapide et légère en C
*   [FFmpeg](https://ffmpeg.org/) - Traitement audio (Volume, Vitesse)
*   [Pystray](https://github.com/moses-palmer/pystray) - Gestion de la zone de notification (System Tray)
*   [Keyboard](https://github.com/boppreh/keyboard) - Écoute des raccourcis globaux
