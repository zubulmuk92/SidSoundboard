import { liens } from "@/lib/site";

const nav = [
  { href: liens.depot, label: "Dépôt GitHub" },
  { href: liens.bugs, label: "Signaler un bug" },
  { href: liens.versions, label: "Versions" },
];

export function PiedDePage() {
  return (
    <footer className="relative z-3 border-t border-ambre/20 bg-[#0A0705] px-6 pt-10 pb-14">
      <div className="mx-auto grid max-w-[1120px] gap-4.5">
        <p className="font-mono text-[11.5px] tracking-[0.1em] text-ambre uppercase">
          Python · PySide6 · miniaudio · FFmpeg
        </p>

        <nav aria-label="Liens du projet" className="flex flex-wrap gap-6">
          {nav.map((l) => (
            <a key={l.href} href={l.href} className="text-sm text-gel hover:text-neige" rel="noopener">
              {l.label}
            </a>
          ))}
        </nav>

        <p className="max-w-[72ch] text-[11.5px] leading-relaxed text-[#6C7C88]">
          Projet personnel, sans aucun lien avec 20th Century Studios. Sid et L&apos;Âge de glace
          appartiennent à leurs ayants droit ; la mascotte n&apos;est ici qu&apos;un clin d&apos;œil.
        </p>
      </div>
    </footer>
  );
}
