/** Constantes partagées : liens, chiffres et textes qui apparaissent
 *  à plusieurs endroits (page, metadata, JSON-LD, sitemap). */

/** Sous-chemin de déploiement — « /SidSoundboard » sur GitHub Pages, vide ailleurs. */
export const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

/** Origine seule, sans sous-chemin : c'est ce qu'attend `metadataBase`,
 *  qui ajoute le basePath de son côté (sinon il apparaît deux fois). */
const origine = process.env.NEXT_PUBLIC_SITE_ORIGIN ?? "https://zubulmuk92.github.io";

export const site = {
  nom: "SidSoundboard",
  titre: "SidSoundboard — la soundboard Windows qui ne touche pas à vos FPS",
  accroche:
    "Soundboard Windows open source pour Discord et le stream : rendu audio pré-calculé, 0 % de CPU pendant la lecture, double sortie casque + micro virtuel, éditeur de son intégré.",
  origine,
  url: `${origine}${basePath}`,
  langue: "fr-FR",
  auteur: "zubulmuk92",
  version: "1.0.0",
  poids: "~150 Mo",
} as const;

/** Chemin d'un fichier de `public/`, préfixé du sous-chemin de déploiement.
 *  `next/image` en mode `unoptimized` ne le fait pas tout seul. */
export function asset(chemin: string): string {
  return `${basePath}${chemin}`;
}

export const liens = {
  depot: "https://github.com/zubulmuk92/SidSoundboard",
  telechargement:
    "https://github.com/zubulmuk92/SidSoundboard/releases/latest/download/SidSoundboard.exe",
  versions: "https://github.com/zubulmuk92/SidSoundboard/releases",
  bugs: "https://github.com/zubulmuk92/SidSoundboard/issues",
} as const;

export const sections = [
  { href: "#moteur", label: "Le moteur" },
  { href: "#editeur", label: "L'éditeur" },
  { href: "#installation", label: "Installation" },
] as const;
