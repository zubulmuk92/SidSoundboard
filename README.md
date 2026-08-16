<div align="center">

# SidSoundboard

**La soundboard Windows qui ne touche pas à vos FPS.**

Envoyez vos sons sur Discord et dans votre casque en même temps, sans que
votre processeur ne travaille pendant la lecture.

[![Dernière version](https://img.shields.io/github/v/release/zubulmuk92/SidSoundboard?label=t%C3%A9l%C3%A9charger&style=for-the-badge&color=59E1D8)](https://github.com/zubulmuk92/SidSoundboard/releases/latest)
[![Plateforme](https://img.shields.io/badge/Windows-10%20%7C%2011-0A141B?style=for-the-badge)](https://github.com/zubulmuk92/SidSoundboard/releases/latest)

[Site du projet](https://zubulmuk92.github.io/SidSoundboard/) ·
[Télécharger](https://github.com/zubulmuk92/SidSoundboard/releases/latest) ·
[Signaler un bug](https://github.com/zubulmuk92/SidSoundboard/issues)

</div>

---

## Téléchargement

> ### ⬇️ [Télécharger `SidSoundboard.exe`](https://github.com/zubulmuk92/SidSoundboard/releases/latest/download/SidSoundboard.exe)
>
> Un seul fichier, rien à installer. Python, Qt et FFmpeg sont inclus.

**Prenez toujours la version publiée dans les [Releases](https://github.com/zubulmuk92/SidSoundboard/releases/latest).**
C'est la seule qui soit compilée, testée, et vérifiable par son empreinte
SHA-256.

Le bouton vert *Code → Download ZIP* télécharge l'état courant de la
branche `main`, qui n'est pas une version publiée : il peut contenir des
fonctionnalités à moitié terminées, ne pas se lancer, ou demander d'être
compilé. Ne l'utilisez que si vous comptez contribuer au code.

Au premier lancement, Windows affiche un avertissement SmartScreen
« éditeur inconnu », parce que l'exécutable n'est pas signé. Cliquez sur
*Informations complémentaires*, puis *Exécuter quand même*.

---

## Pourquoi celle-ci plutôt qu'une autre

La plupart des soundboards appliquent leurs effets en temps réel, pendant
que vous jouez. Chaque son déclenché consomme alors du processeur au pire
moment : en pleine partie.

SidSoundboard fait l'inverse. Dès qu'un réglage change, FFmpeg reconstruit
le fichier en arrière-plan, une seule fois. Déclencher un son n'ouvre
ensuite qu'un flux depuis le disque vers la carte son.

| | |
|---|---|
| **Pendant la lecture** | aucun calcul audio, aucun échantillon traité |
| **En mémoire** | les fichiers sont streamés, jamais chargés entièrement |
| **Sur le disque** | les caches devenus inutiles sont nettoyés au démarrage |

Le corollaire compte autant : puisque le rendu est unique, la sortie casque
et la sortie câble virtuel jouent **exactement le même fichier**. Ce que
vous entendez est ce que vos amis entendent.

---

## Fonctionnalités

### Moteur audio
- Double sortie simultanée : casque **et** micro virtuel, effets identiques
- Volume de la sortie câble réglable à part, lui aussi pré-calculé
- Fondus d'entrée et de sortie, fondu enchaîné entre deux sons
- Arrêt d'urgence global, mode solo

### Éditeur de son
- Volume jusqu'à 400 %, vitesse et hauteur, bass booster, reverb
- Découpe à la souris directement sur la forme d'onde
- Fondus propres à chaque son
- **Édition non destructive** : le fichier importé n'est jamais modifié,
  chaque réglage reste réversible

### Organisation
- **Scènes** : chaque scène a ses sons et ses raccourcis. Un jeu, un stream
  et un appel privé n'appellent pas les mêmes sons — on bascule d'un clic
- **Pads** : une grille de grandes cibles pour déclencher en pleine partie,
  sans risque de cliquer à côté
- Recherche, filtre par catégorie, réordonnancement par glisser-déposer
- Les raccourcis en conflit sont signalés au lieu de s'écraser en silence

### Import
- Fichiers locaux : MP3, WAV, OGG, FLAC, M4A
- Téléchargement direct depuis YouTube en collant une URL
- Normalisation automatique du niveau, pour que tous vos sons se valent

### Interface
- Français et anglais, changement immédiat sans redémarrage
- Thème clair ou sombre, suivant le réglage de Windows

---

## Premiers pas

1. Lancez `SidSoundboard.exe` depuis un dossier où il peut écrire.
2. Dans **Réglages**, choisissez votre périphérique principal (votre casque).
3. Dans **Bibliothèque**, importez un fichier ou collez une URL YouTube.
4. Cliquez sur la touche affichée sur une carte pour lui assigner un
   raccourci clavier global.

### Envoyer le son vers Discord

Il faut un câble audio virtuel, que SidSoundboard n'installe pas :

1. Installez [VB-Cable](https://vb-audio.com/Cable/), puis redémarrez Windows.
2. Dans **Réglages**, activez la double sortie et choisissez `CABLE Input`
   comme sortie secondaire.
3. Dans Discord, sélectionnez `CABLE Output` comme périphérique d'entrée.

L'écran **Aide** vérifie ces trois points et indique lequel manque.

---

## Où sont rangées mes données

À côté de l'exécutable, s'il peut y écrire — l'application est portable,
déplacer le dossier suffit à la déplacer.

Si l'emplacement est protégé en écriture (`Program Files`, par exemple),
tout bascule vers `%APPDATA%\SidSoundboard`.

```
SidSoundboard.exe
config.json          réglages, scènes, sons
downloads/           fichiers audio et rendus
```

---

## Compiler depuis les sources

Pour contribuer au code. **Si vous voulez seulement utiliser
l'application, prenez la [release](https://github.com/zubulmuk92/SidSoundboard/releases/latest).**

```bash
git clone https://github.com/zubulmuk92/SidSoundboard.git
cd SidSoundboard
pip install -r requirements.txt
```

FFmpeg n'est pas dans le dépôt : le binaire pèse 99 Mo. Récupérez un build
Windows sur [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) et placez-le
dans `bin/win32/ffmpeg.exe`.

```bash
python main.py
python -m unittest discover -s tests -t .
python -m PyInstaller --noconfirm --clean SidSoundboard.spec
```

Développé avec Python 3.14 et PySide6.

---

## Composants tiers

SidSoundboard embarque FFmpeg (GPLv3), PySide6 (LGPLv3), miniaudio,
yt-dlp, pystray et Pillow. Licences et accès aux sources dans
[THIRD-PARTY.md](THIRD-PARTY.md).

---

## Auteur

Créé et maintenu par **[zubulmuk92](https://github.com/zubulmuk92)**.

Bugs et suggestions sont les bienvenus dans les
[issues](https://github.com/zubulmuk92/SidSoundboard/issues).
