# Composants tiers

SidSoundboard est distribué sous forme d'un exécutable unique qui embarque
les composants ci-dessous. Ce document accompagne toute redistribution du
`.exe`.

## FFmpeg — GPLv3

Le binaire embarqué (`bin/win32/ffmpeg.exe`) est une compilation
*essentials* de gyan.dev, configurée avec `--enable-gpl
--enable-version3`. Il est donc couvert par la **GNU General Public
License version 3**.

- Licence : https://www.gnu.org/licenses/gpl-3.0.html
- Sources : https://github.com/FFmpeg/FFmpeg
- Build redistribué : https://www.gyan.dev/ffmpeg/builds/

Conformément à la GPLv3, le code source complet de la version de FFmpeg
distribuée ici est disponible aux adresses ci-dessus. Toute personne
recevant ce logiciel peut en obtenir les sources sans frais.

SidSoundboard n'est pas lié à FFmpeg : il l'invoque comme un programme
externe, via un sous-processus.

## PySide6 / Qt — LGPLv3

Interface graphique. Utilisé sans modification, en liaison dynamique.

- Licence : https://www.gnu.org/licenses/lgpl-3.0.html
- Sources : https://code.qt.io/cgit/pyside/pyside-setup.git/

## miniaudio — MIT / Unlicense

Lecture audio bas niveau et décodage.
https://github.com/irmen/pyminiaudio

## yt-dlp — Unlicense

Téléchargement audio depuis YouTube.
https://github.com/yt-dlp/yt-dlp

## keyboard — MIT

Raccourcis clavier globaux.
https://github.com/boppreh/keyboard

## pystray — LGPLv3

Icône de zone de notification.
https://github.com/moses-palmer/pystray

## Pillow — MIT-CMU

Traitement des images d'icônes.
https://github.com/python-pillow/Pillow

## Logo

Le logo représente un personnage issu de la franchise *L'Âge de glace*
(20th Century Studios). Il n'est pas couvert par la licence de ce
logiciel et n'est pas fourni pour un usage commercial.
