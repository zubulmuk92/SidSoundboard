# Site vitrine SidSoundboard

Page statique, sans build ni dépendance : trois fichiers plus le logo.

```
site/
├── index.html
├── styles.css
├── app.js
├── assets/sid.png        (copie de logo.png)
└── assets/favicon.ico    (copie de logo.ico)
```

## Regarder en local

```bash
python -m http.server 8123 --directory site
```

Puis <http://localhost:8123>. (Un `.claude/launch.json` fait la même chose depuis
Claude Code. `file://` ne suffit pas : les polices et le module audio ont besoin
d'un vrai serveur.)

## Le lien de téléchargement

Le bouton pointe vers :

```
https://github.com/zubulmuk92/SidSoundboard/releases/latest/download/SidSoundboard.exe
```

GitHub ne résout cette URL **que si une release publiée contient un asset nommé
exactement `SidSoundboard.exe`**. Tant que ce n'est pas fait, le lien renvoie une
404. Pour créer la release :

```bash
gh release create v1.0.0 dist/SidSoundboard.exe --title "SidSoundboard 1.0.0" --notes "Première version publique"
```

Le poids annoncé sur la page (`~150 Mo`) correspond au binaire actuel — à
corriger dans `index.html` si l'exécutable change de taille.

## Mettre en ligne

**GitHub Pages** ne sert que la racine du dépôt ou `docs/`. Deux options :

- renommer `site/` en `docs/` (ou y copier les fichiers), puis
  *Settings → Pages → Deploy from a branch → main /docs* ;
- ou déposer le dossier `site/` sur Netlify / Cloudflare Pages / Vercel, qui
  acceptent n'importe quel sous-dossier comme racine de publication.

## Détails d'implémentation

- Les six sons de démonstration sont **synthétisés** par la Web Audio API
  (oscillateurs, bruit filtré, formants). Aucun fichier audio n'est chargé, et
  rien ne joue avant un clic ou une frappe.
- Touches `A Z E R T Y` pour les dalles, `Espace` ou `Échap` pour tout couper —
  le même geste que la touche panique de l'application.
- `prefers-reduced-motion` coupe la neige, les dérives lumineuses et les
  révélations au scroll ; la waveform reste alors figée.
- Les polices viennent de Google Fonts avec une pile de repli système : la page
  reste lisible hors ligne.
- `styles.css?v=1` / `app.js?v=1` : incrémentez le numéro après une modification
  pour forcer les navigateurs à recharger les fichiers.
