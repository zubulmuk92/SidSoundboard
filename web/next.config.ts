import type { NextConfig } from "next";

// Déploiement sur un sous-chemin (GitHub Pages projet : /SidSoundboard).
// Vide par défaut : la racine d'un domaine ou du dev local.
const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

const nextConfig: NextConfig = {
  // Export 100 % statique : chaque route devient un .html pré-rendu,
  // servable par n'importe quel hébergeur (Pages, Netlify, S3…).
  output: "export",
  basePath,
  // `next/image` a besoin d'un serveur pour optimiser à la volée : hors-jeu ici.
  images: { unoptimized: true },
  // /page -> /page/index.html : évite les 404 sur les hébergeurs statiques.
  trailingSlash: true,
};

export default nextConfig;
