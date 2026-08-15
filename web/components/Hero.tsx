import { asset, liens, site } from "@/lib/site";
import { Soundboard } from "./Soundboard";

const specs = [
  { cle: "Fichier", valeur: "SidSoundboard.exe" },
  { cle: "Poids", valeur: site.poids },
  { cle: "Installateur", valeur: "aucun" },
  { cle: "Prix", valeur: "0 €" },
];

export function Hero() {
  return (
    <section
      id="haut"
      className="relative flex min-h-[min(84vh,880px)] items-center overflow-clip bg-[radial-gradient(120%_80%_at_12%_0%,#10293D_0%,transparent_58%),linear-gradient(180deg,var(--color-nuit)_0%,var(--color-nuit-2)_100%)] px-6 pt-[clamp(56px,9vw,96px)] pb-[clamp(96px,11vw,150px)]"
    >
      {/* aurore boréale, dérivant lentement */}
      <div
        aria-hidden="true"
        className="anim-derive absolute inset-x-0 -top-[30%] h-[70%] bg-[radial-gradient(50%_60%_at_25%_40%,rgb(127_231_242/0.16),transparent_70%),radial-gradient(40%_50%_at_68%_30%,rgb(107_58_99/0.28),transparent_70%)] blur-[30px]"
      />

      <div className="relative z-3 mx-auto grid w-full max-w-[1120px] items-center gap-[clamp(32px,5vw,64px)] lg:grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)]">
        <div>
          <p className="eyebrow reveal">Soundboard Windows · open source</p>

          <h1
            className="reveal font-display leading-[0.8] font-black uppercase [background:linear-gradient(168deg,#FFFFFF_0%,#CFEAF4_46%,var(--color-gel-sombre)_100%)] bg-clip-text text-transparent"
            style={{ transitionDelay: "60ms" }}
          >
            <span className="block text-[clamp(4.6rem,12vw,8.6rem)] tracking-[-0.015em] [font-variation-settings:'opsz'_72]">
              Sid
            </span>
            <span className="mt-1 block pl-[0.1em] text-[clamp(1.5rem,3.5vw,2.7rem)] font-bold tracking-[0.14em]">
              Soundboard
            </span>
          </h1>

          <p
            className="reveal my-8 max-w-[46ch] border-l-2 border-ambre pl-[18px] text-[clamp(1.02rem,1.5vw,1.14rem)] text-brume"
            style={{ transitionDelay: "120ms" }}
          >
            Une soundboard qui balance vos sons sur Discord sans jamais toucher à vos FPS. Tous les effets
            sont calculés <em className="text-pelage italic">avant</em> la lecture : quand vous appuyez sur
            une touche, le processeur n&apos;a plus rien à faire.
          </p>

          <div className="reveal flex flex-wrap gap-3.5" style={{ transitionDelay: "180ms" }}>
            <a className="btn btn-braise max-sm:flex-1 max-sm:justify-center" href={liens.telechargement}>
              <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
                <path
                  d="M12 3v11m0 0 4.5-4.5M12 14l-4.5-4.5M4 17v2.5A1.5 1.5 0 0 0 5.5 21h13a1.5 1.5 0 0 0 1.5-1.5V17"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              Télécharger pour Windows
            </a>
            <a className="btn btn-gel max-sm:flex-1 max-sm:justify-center" href={liens.depot} rel="noopener">
              Voir le code source
            </a>
          </div>

          <ul
            className="reveal mt-9 flex flex-wrap gap-x-7 gap-y-2.5 font-mono text-[12.5px]"
            style={{ transitionDelay: "240ms" }}
          >
            {specs.map((s) => (
              <li key={s.cle} className="flex items-baseline gap-2">
                <span className="text-[11px] tracking-[0.06em] text-gel-sombre uppercase">{s.cle}</span>
                {s.valeur}
              </li>
            ))}
          </ul>
        </div>

        <div className="reveal" style={{ transitionDelay: "120ms" }}>
          <Soundboard sid={asset("/sid.png")} />
        </div>
      </div>

      {/* bord de banquise */}
      <svg
        aria-hidden="true"
        viewBox="0 0 1440 90"
        preserveAspectRatio="none"
        className="absolute inset-x-0 -bottom-px z-3 h-[clamp(48px,6vw,90px)] w-full fill-nuit"
      >
        <path d="M0 90V52l112-19 96 26 128-33 104 21 141-30 118 27 121-22 105 25 118-31 97 22 100-16v108z" />
      </svg>
    </section>
  );
}
