# SidSoundboard - Édition Studio Ultime

SidSoundboard est une table de mixage/soundboard développée en Python conçue spécifiquement pour les streamers, gamers et utilisateurs de Discord. L'application met un point d'honneur sur un design minimaliste "Studio" et une **optimisation radicale des performances**.

## 🚀 Le Secret de l'Optimisation "Zéro Latence"

Contrairement à 99% des soundboards du marché qui calculent les effets (volume, vitesse) en temps réel dans la mémoire vive, SidSoundboard utilise une architecture de **Rendu Pré-calculé (Lazy Rendering)**.

### Comment ça marche ?
1. **Zéro Impact CPU** : Lorsque vous jouez un son, l'application ne fait *aucun* calcul audio. Elle se contente d'ouvrir un flux direct vers la carte son. Votre processeur reste à 0% d'utilisation, évitant ainsi les drops de FPS en jeu.
2. **Mémoire RAM < 30 Mo** : Les fichiers ne sont pas chargés en mémoire. Ils sont lus en streaming directement depuis le disque via le moteur bas niveau `miniaudio`.
3. **Moteur FFmpeg Asynchrone** : Lorsque vous modifiez un volume ou une vitesse, l'application utilise FFmpeg en arrière-plan (de manière invisible) pour générer le fichier audio parfait.
4. **Garbage Collector Intégré** : Pour ne pas polluer votre disque, l'application supprime instantanément les anciens fichiers de cache dès qu'un réglage change, et nettoie automatiquement les fichiers orphelins à chaque démarrage.

## 🎛️ Routage Double (Virtual Cable)
Vous voulez entendre le son doucement dans votre casque, mais l'envoyer très fort sur Discord pour vos amis ?
- SidSoundboard gère deux cartes sons simultanément (ex: Casque + VB-Cable).
- Le volume de la sortie secondaire est réglable globalement dans les paramètres.
- Les deux flux sont streamés en parfaite synchronisation par le moteur C sous-jacent.

## 🎨 Interface Moderne
- Navigation par Sidebar latérale (façon Discord/VS Code).
- Waveform précalculée sur chaque son, cliquable pour naviguer dans la lecture.
- Fondus d'entrée/sortie et crossfade entre les sons.
- Page d'édition par son : volume, vitesse/pitch, bass booster, reverb,
  découpe à la souris sur la waveform, et fondus d'entrée/sortie propres
  à chaque son.
- Tous les effets sont rendus une seule fois par FFmpeg et joués à
  l'identique sur les **deux** sorties (casque et câble virtuel) — ce que
  vous entendez est exactement ce que vos amis entendent.
- Édition non destructive : le fichier original est conservé intact, vous
  pouvez revenir en arrière sur n'importe quel réglage à tout moment.
- Thème « âge de glace » : bleus de glacier profonds et turquoise de
  crevasse, conçu avec `PySide6` (Qt). Le rouge du bouton STOP est la seule
  couleur chaude de l'interface — impossible de le rater en pleine partie.
- S'adapte automatiquement au mode clair/sombre de Windows.
- Interface disponible en **français** et en **anglais** (Réglages → Langue).
  Le changement est immédiat, sans redémarrage.

## 🎬 Pads
La Bibliothèque sert à gérer vos sons ; l'écran **Pads** sert à les jouer. Une
grille de gros pads, une seule action possible : déclencher. Le pad en
cours de lecture affiche sa progression.

## 📁 Scènes
Un jeu, un stream et un appel privé n'appellent pas les mêmes sons. Chaque
**scène** a sa propre liste et ses propres raccourcis — la même touche F1
peut servir dans deux contextes. Le sélecteur « Scène active » est en haut
de la barre latérale, avec le bouton **+ Nouvelle scène** juste en dessous ;
renommer et supprimer se font dans **Réglages → Scènes**.

## 💾 Où sont mes données ?
À côté de l'exécutable, s'il peut y écrire (application portable), sinon
dans `%APPDATA%\SidSoundboard`. L'application retrouve donc sa
bibliothèque quel que soit le dossier depuis lequel on la lance.

## 🔧 Reconstruire l'exécutable
`bin/` est exclu du dépôt : le binaire FFmpeg pèse 99 Mo. Pour reconstruire
depuis un clone, placez `ffmpeg.exe` dans `bin/win32/`, puis lancez
`python -m PyInstaller --noconfirm --clean SidSoundboard.spec`.
Les licences des composants embarqués sont dans [THIRD-PARTY.md](THIRD-PARTY.md).

## 📦 Installation & Utilisation
Le projet est packagé en un seul fichier `.exe` autonome.
1. Lancez `SidSoundboard.exe` (situé dans le dossier `dist/`).
2. Installez *VB-Cable* séparément si vous voulez router le son vers un micro virtuel (l'app ne l'installe pas elle-même).
3. Dans **Réglages**, configurez votre sortie Principale (Casque), activez la Double Sortie et choisissez la sortie Secondaire (VB-Cable) si besoin.
4. Dans **Bibliothèque**, ajoutez vos sons (MP3, WAV) ou téléchargez-les directement depuis YouTube/YT Music en collant l'URL !
5. Assignez vos touches de raccourci (macros) et profitez d'un son instantané.
