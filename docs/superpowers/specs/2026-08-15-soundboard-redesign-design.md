# SidSoundboard — Refonte UI & Fonctionnalités (Design)

## Contexte

Le projet est mi-migré de CustomTkinter vers PySide6. Le moteur audio
(`audio_manager.py` + `miniaudio`, `audio_processor.py` + FFmpeg précalculé,
`hotkey_manager.py`) fonctionne et respecte l'objectif de performance
(streaming disque direct, 0% CPU idle, <30 Mo RAM). Ce document couvre la
refonte de la couche UI (`gui_pyside.py`, 700 lignes, instable) et l'ajout de
deux fonctionnalités : waveform et fade in/out/crossfade.

**Contrainte non négociable** : aucune régression sur le principe zéro-coût
à l'idle et en lecture stable. Tout calcul (waveform, fades) doit être
précalculé ou limité à une fenêtre de quelques centaines de ms.

## Décisions validées avec l'utilisateur

- Réécriture complète de la couche UI plutôt que patch de l'existant.
- Nouvelles fonctionnalités prioritaires : waveform (pré-calculée à
  l'import) et mixage fade in/out + crossfade.
- Le double-output (VB-Cable) doit être un vrai switch on/off dans les
  Réglages, appliqué de façon synchronisée aux deux flux (y compris pour
  les fades).
- Design visuel à soigner ("beau design"), liberté créative laissée au
  développeur.
- Le remplacement du FFmpeg statique (198 Mo → build audio-only) est
  identifié comme le plus gros gain de légèreté possible mais traité comme
  chantier séparé, hors scope de cette refonte.

## Architecture du code

Découpage modulaire du dossier `ui/` (remplace le fichier unique
`gui_pyside.py`) :

```
ui/
  __init__.py
  theme.py            # couleurs, typographie, QSS
  main_window.py       # AppGUI (QMainWindow), sidebar, navigation, player bar
  views/
    library_view.py    # grille de sons, recherche, import, YouTube
    settings_view.py    # périphériques, double-output, ducking, panic key
  widgets/
    sound_card.py       # carte son (waveform mini, hotkey, play, volume)
    waveform.py          # QPainter widget réutilisable (mini + grande vue)
    player_bar.py        # barre de lecture bas de fenêtre (timeline, fades)
```

`main.py` importe `ui.main_window.AppGUI` au lieu de `gui_pyside`.
Le reste (`audio_manager.py`, `audio_processor.py`, `hotkey_manager.py`,
`config_manager.py`, `cache_manager.py`, `yt_downloader.py`) reste en place,
avec les extensions décrites ci-dessous.

Nettoyage inclus dans ce travail :
- Suppression des fichiers de scratch : `patch_gui.py`, `test_import.py`,
  `test_qt.py`, `test_miniaudio2.py`, `debug.log`/écritures de debug dans le
  code.
- Suppression de `gui.py` (déjà fait localement, à committer).
- Mise à jour de `SidSoundboard.spec` (retrait de la référence
  `customtkinter`, mise à jour des `datas`/`hiddenimports` pour la nouvelle
  structure `ui/`).

## Système visuel

Direction : **console de mixage haut de gamme**, pas un dashboard SaaS
générique. On s'éloigne de la palette slate/bleu Tailwind par défaut du
premier jet PySide6.

- **Fond** : graphite quasi-noir `#121316` (fenêtre), panneaux `#1B1D21`,
  survol `#26292F`.
- **Accent principal** : ambre signal `#FF8A3D` (rappel des LED de peak sur
  une vraie console audio), utilisé avec parcimonie (CTA, état actif,
  waveform de lecture).
- **Texte** : blanc cassé `#F2F1ED` / gris `#8B8D93` pour le secondaire.
- **Tags de catégorie** existants (rouge, cyan, vert, jaune, violet) conservés
  tels quels sur le bord gauche des cartes — bon repère visuel déjà en place.
- **Typographie** : `Inter` pour le corps (déjà dispo système Win10/11 via
  Segoe UI en repli), poids 600 sur les titres, espacement de lettres léger
  en majuscules pour les labels de section (rappel sérigraphie de matériel
  audio).
- **Coins arrondis modérés** (8px cartes, 6px boutons/inputs) — pas de
  neumorphisme, pas d'ombres portées lourdes (coûteux à rendre en Qt et peu
  lisible en dark mode).
- **Sidebar** : icônes + libellés, indicateur actif = liseré ambre à gauche
  (déjà présent dans la V1, conservé et affiné).

## Composants clés

**Carte son (`SoundCard`)**
- Bande waveform miniature en fond de carte (lecture des points précalculés,
  dessinée avec `QPainter`, teintée dans la couleur de catégorie).
- Pendant la lecture : la portion jouée de la waveform se remplit en ambre,
  progression en temps réel (même timer 100ms que la barre de lecture
  actuelle).
- Hotkey affichée en chip, bouton play, slider volume, tag catégorie —
  layout conservé de la V1 qui fonctionnait bien, retravaillé visuellement.

**Waveform (`widgets/waveform.py`)**
- Widget réutilisable : mini (dans la carte, non interactif) et grande
  (dans la player bar, cliquable pour seek — remplace le simple `QSlider`
  actuel par une waveform cliquable, plus lisible).
- Lit un fichier `<cache>.peaks.json` (~200 valeurs min/max) généré une
  seule fois à l'import (cf. section moteur audio).

**Player bar**
- Reprend nom du son, temps courant/total, waveform cliquable pour seek.
- Ajout : boutons/indicateurs pour fade in/out actifs sur le son en cours
  (visuel simple, pas de contrôle temps réel complexe).

**Réglages**
- Ajout d'un vrai toggle "Double Sortie (Casque + Câble Virtuel)" qui
  active/désactive `dual_output_enabled` et affiche/masque le sélecteur de
  device secondaire en conséquence.
- Ajout de champs fade : durée fade-in / fade-out par défaut (ms),
  applicables à tous les sons (pas de réglage par son pour rester simple —
  YAGNI, à revoir si le besoin apparaît).

## Extensions moteur audio

**Peaks (waveform)** — nouvelle fonction dans `audio_processor.py` :
`generate_peaks(filepath) -> list[float]`. Décode le fichier une fois via
`miniaudio.decode_file`, réduit en ~200 buckets (max amplitude absolue par
bucket, normalisé 0-1), écrit `<filepath>.peaks.json` à côté du fichier
audio en cache. Appelé une seule fois, juste après
`normalize_and_import_audio`, en tâche de fond (déjà threadé côté import).

**Fade in/out & crossfade** — nouvelle fonction dans `audio_manager.py` :
un générateur `_apply_fade(stream, fade_in_ms, fade_out_ms, duration,
sample_rate)` qui enveloppe le générateur `miniaudio.stream_file` existant.
Pendant les échantillons dans la fenêtre de fade, multiplie le buffer par un
facteur de gain linéaire (0→1 ou 1→0) ; en dehors de la fenêtre, il yield
directement le buffer reçu sans modification (donc coût nul en régime
établi). Appliqué **identiquement aux flux primaire et secondaire** pour
rester synchronisé sur le double-output. Le crossfade au changement de son
réutilise ce mécanisme : le son sortant reçoit un fade-out programmé au
moment du `toggle_play_pause` vers un nouveau son, qui démarre en parallèle
avec son propre fade-in, avant que `stop_all()` ne coupe l'ancien son une
fois son fade-out terminé (petit changement dans `toggle_play_pause` pour ne
pas couper instantanément quand un fade-out est en cours).

## Tests / vérification

Pas de framework de test existant dans le projet. Vérification manuelle
prévue après implémentation :
- Lancement `python main.py` en dev, test des flux : import local, import
  YouTube, lecture, pause/reprise, seek via waveform, fade in/out perceptible
  à l'oreille, double-output vers VB-Cable si installé sur la machine de
  dev, hotkeys, panic key, system tray.
- Contrôle RAM/CPU idle via le Gestionnaire des tâches Windows (objectif :
  pas de régression vs baseline actuelle).
- Build PyInstaller (`SidSoundboard.spec` mis à jour) et test du `.exe`
  final en conditions réelles.

## Hors scope (à traiter séparément)

- Remplacement du FFmpeg statique par un build audio-only minimal.
- Playlists/files d'attente, profils multiples (non retenus dans cette
  itération).
