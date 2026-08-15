import Image from "next/image";
import { asset, liens, site } from "@/lib/site";

const colonnes = [
  {
    titre: "Produit",
    liens: [
      { href: liens.telechargement, label: "Télécharger pour Windows" },
      { href: liens.versions, label: "Toutes les versions" },
      { href: "#editeur", label: "Fonctionnalités" },
      { href: "#installation", label: "Installation" },
    ],
  },
  {
    titre: "Technique",
    liens: [
      { href: "#moteur", label: "Le moteur zéro latence" },
      { href: "#routage", label: "Double sortie audio" },
      { href: `${liens.depot}#readme`, label: "Documentation" },
    ],
  },
  {
    titre: "Code",
    liens: [
      { href: liens.depot, label: "Dépôt GitHub" },
      { href: liens.bugs, label: "Signaler un bug" },
      { href: liens.versions, label: "Journal des versions" },
    ],
  },
];

export function PiedDePage() {
  const annee = 2026;

  return (
    <footer className="relative z-3 border-t border-gel/12 bg-[#040B12]">
      <div className="conteneur grid gap-10 py-14 md:grid-cols-[minmax(0,1.4fr)_repeat(3,minmax(0,1fr))] md:gap-8">
        <div>
          <div className="flex items-center gap-3">
            <Image src={asset("/sid.png")} alt="" width={677} height={369} className="h-auto w-22" />
            <span className="font-display text-[23px] font-black uppercase">{site.nom}</span>
          </div>
          <p className="mt-4 max-w-[34ch] text-[14px] text-brume">
            La table de mixage des streamers pressés : vos sons partent sur Discord sans coûter un seul
            pourcent de processeur.
          </p>
          <a className="btn btn-azur mt-6 text-[14px]" href={liens.telechargement}>
            Télécharger
          </a>
        </div>

        {colonnes.map((col) => (
          <nav key={col.titre} aria-label={col.titre}>
            <h2 className="mb-4 font-mono text-[11px] tracking-[0.16em] text-gel-sombre uppercase">
              {col.titre}
            </h2>
            <ul className="grid gap-2.5">
              {col.liens.map((l) => (
                <li key={l.label}>
                  <a
                    href={l.href}
                    rel="noopener"
                    className="text-[14px] text-brume transition-colors hover:text-neige"
                  >
                    {l.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        ))}
      </div>

      <div className="border-t border-gel/10">
        <div className="conteneur flex flex-wrap items-center justify-between gap-x-8 gap-y-4 py-7">
          <p className="text-[13px] text-brume">
            © {annee} <span className="font-semibold text-neige">SidDev Corporation</span> — Tous droits
            réservés.
          </p>
          <p className="font-mono text-[11px] tracking-[0.12em] text-gel-sombre uppercase">
            Python · PySide6 · miniaudio · FFmpeg
          </p>
        </div>
        <div className="conteneur pb-10">
          <p className="max-w-[80ch] text-[11.5px] leading-relaxed text-[#5C6E7C]">
            SidDev Corporation est le nom sous lequel est publié ce projet personnel. Il n&apos;a aucun lien
            avec 20th Century Studios : Sid et L&apos;Âge de glace appartiennent à leurs ayants droit, et la
            mascotte n&apos;est ici qu&apos;un clin d&apos;œil. SidSoundboard est distribué tel quel, sans
            garantie.
          </p>
        </div>
      </div>
    </footer>
  );
}
