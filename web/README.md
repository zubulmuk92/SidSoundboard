# Site vitrine SidSoundboard

Next.js 16 (App Router) · React 19 · Tailwind CSS 4 · TypeScript.
Export **100 % statique** : `next build` produit `out/`, un dossier de fichiers
HTML/CSS/JS servable par n'importe quel hébergeur, sans serveur Node.

```bash
npm install
npm run dev     # http://localhost:3000
npm run build   # génère out/
npx eslint .
```

## Structure

```
app/
├── layout.tsx              polices, metadata, JSON-LD SoftwareApplication
├── page.tsx                assemblage des sections
├── globals.css             jetons de design (@theme) + classes de composants
├── sitemap.ts robots.ts    générés au build
├── opengraph-image.png     vignette de partage 1200×630
└── favicon.ico
components/
├── Soundboard.tsx          ⚡ client — les dalles jouables, clavier, panique
├── Neige.tsx               ⚡ client — neige sur canvas
├── Revelations.tsx         ⚡ client — un seul IntersectionObserver
└── Nav, Hero, Moteur, Routage, Editeur, Installation, FeuDeCamp, PiedDePage
lib/
├── audio.ts                synthèse Web Audio des six sons de démo
└── site.ts                 liens, constantes, helper `asset()`
```

Seuls trois composants sont clients. Tout le texte est rendu côté serveur au
build : il est présent tel quel dans `out/index.html`, donc lisible par les
crawlers même sans exécution de JavaScript.

## SEO

- `metadata` complet : title, description, canonical, Open Graph, Twitter Card,
  `robots`, mots-clés.
- Données structurées JSON-LD `SoftwareApplication` (prix, OS, version, lien de
  téléchargement, liste de fonctionnalités).
- `sitemap.xml` et `robots.txt` générés au build.
- Polices auto-hébergées via `next/font` : aucune requête vers Google au
  chargement, et pas de décalage de mise en page.
- Une page unique, entièrement pré-rendue : rien à attendre côté client.

### Régénérer la vignette Open Graph

`app/opengraph-image.png` est figée volontairement : un hébergeur statique sert
mal un fichier sans extension, ce que produirait la route `opengraph-image.tsx`.
Pour la refaire, recréez temporairement ce fichier avec `ImageResponse`
(`next/og`), lancez `npm run build`, puis copiez `out/opengraph-image` vers
`app/opengraph-image.png` et supprimez le `.tsx`.

## Déploiement

### GitHub Pages

`.github/workflows/pages.yml` construit et publie à chaque push sur `main`.
Activez ensuite *Settings → Pages → Source : GitHub Actions*.

Le workflow passe deux variables, parce que Pages sert le site sous un
sous-chemin :

| Variable                   | Valeur                          |
| -------------------------- | ------------------------------- |
| `NEXT_PUBLIC_BASE_PATH`    | `/SidSoundboard`                |
| `NEXT_PUBLIC_SITE_ORIGIN`  | `https://zubulmuk92.github.io`  |

`SITE_ORIGIN` ne contient **que** l'origine : Next ajoute le `basePath` de son
côté aux URL de metadata. Les deux ensemble produiraient un chemin en double.

### Netlify, Cloudflare Pages, Vercel

Commande `npm run build`, dossier publié `web/out`, aucune variable à définir
(le site est alors à la racine du domaine). Renseignez `NEXT_PUBLIC_SITE_ORIGIN`
avec votre domaine pour que le canonical et l'Open Graph pointent au bon endroit.

## Le lien de téléchargement

Le bouton pointe vers :

```
https://github.com/zubulmuk92/SidSoundboard/releases/latest/download/SidSoundboard.exe
```

GitHub ne résout cette URL **que si une release publiée contient un asset nommé
exactement `SidSoundboard.exe`**. Sans cela, le lien renvoie une 404 :

```bash
gh release create v1.0.0 dist/SidSoundboard.exe --title "SidSoundboard 1.0.0" --notes "Première version publique"
```

Le poids annoncé (`~150 Mo`) et le numéro de version vivent dans `lib/site.ts`.

## La soundboard du hero

Les six sons sont **synthétisés** à la volée par la Web Audio API (oscillateurs,
bruit filtré, formants) : aucun fichier audio n'est téléchargé, et le contexte
audio n'est créé qu'au premier clic — jamais au chargement.

Touches `A Z E R T Y` pour les dalles, `Espace` ou `Échap` pour tout couper,
comme la touche panique de l'application.

`prefers-reduced-motion: reduce` coupe la neige, les dérives lumineuses et les
révélations au scroll ; la waveform reste alors figée.
