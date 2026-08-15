import type { Metadata, Viewport } from "next";
import { Big_Shoulders, IBM_Plex_Mono, IBM_Plex_Sans } from "next/font/google";
import { basePath, liens, site } from "@/lib/site";
import "./globals.css";

// Polices auto-hébergées au build : aucun appel à Google au chargement.
const display = Big_Shoulders({
  subsets: ["latin"],
  axes: ["opsz"],
  variable: "--police-display",
  display: "swap",
});

const texte = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "600"],
  style: ["normal", "italic"],
  variable: "--police-sans",
  display: "swap",
});

const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--police-mono",
  display: "swap",
});

export const metadata: Metadata = {
  // Origine seule : Next ajoute lui-même le basePath aux chemins d'images.
  metadataBase: new URL(site.origine),
  title: {
    default: site.titre,
    template: `%s — ${site.nom}`,
  },
  description: site.accroche,
  applicationName: site.nom,
  authors: [{ name: site.auteur, url: liens.depot }],
  creator: site.auteur,
  keywords: [
    "soundboard",
    "soundboard Discord",
    "soundboard Windows",
    "soundboard gratuite",
    "soundboard open source",
    "VB-Cable",
    "micro virtuel",
    "sons Discord",
    "streaming",
    "raccourcis clavier",
    "SidSoundboard",
  ],
  category: "technology",
  alternates: { canonical: `${basePath}/` },
  openGraph: {
    type: "website",
    locale: "fr_FR",
    url: site.url,
    siteName: site.nom,
    title: site.titre,
    description: site.accroche,
  },
  twitter: {
    card: "summary_large_image",
    title: site.titre,
    description: site.accroche,
  },
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true, "max-image-preview": "large" },
  },
};

export const viewport: Viewport = {
  themeColor: "#061019",
  colorScheme: "dark",
};

/** Fiche produit lisible par les moteurs de recherche. */
const donneesStructurees = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: site.nom,
  description: site.accroche,
  url: site.url,
  applicationCategory: "MultimediaApplication",
  applicationSubCategory: "Soundboard",
  operatingSystem: "Windows 10, Windows 11",
  softwareVersion: site.version,
  downloadUrl: liens.telechargement,
  installUrl: liens.versions,
  fileSize: site.poids,
  inLanguage: "fr-FR",
  author: { "@type": "Person", name: site.auteur, url: `https://github.com/${site.auteur}` },
  offers: { "@type": "Offer", price: "0", priceCurrency: "EUR" },
  featureList: [
    "Rendu audio pré-calculé, 0 % de CPU pendant la lecture",
    "Double sortie simultanée casque et câble virtuel",
    "Éditeur par son : découpe, fondus, volume, vitesse, basses, réverb",
    "Import depuis YouTube et YouTube Music",
    "Raccourcis clavier globaux et touche panique",
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="fr"
      data-scroll-behavior="smooth"
      className={`${display.variable} ${texte.variable} ${mono.variable}`}
    >
      <body>
        {/* Sans JavaScript, rien ne doit rester invisible. */}
        <noscript>
          <style>{`.reveal{opacity:1;transform:none}`}</style>
        </noscript>
        {children}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(donneesStructurees) }}
        />
      </body>
    </html>
  );
}
