import { asset, liens, site } from "@/lib/site";
import { BordGlace } from "./BordGlace";
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
      className="relative flex min-h-[min(82vh,860px)] items-center overflow-clip bg-[linear-gradient(180deg,var(--color-nuit)_0%,var(--color-nuit-2)_100%)] pt-[clamp(48px,7vw,88px)] pb-[clamp(88px,10vw,136px)]"
    >
      {/* Une seule lueur, qui dérive lentement. */}
      <div
        aria-hidden="true"
        className="anim-derive absolute inset-x-0 -top-[25%] h-[65%] bg-[radial-gradient(45%_60%_at_30%_45%,rgb(127_231_242/0.14),transparent_70%)] blur-[40px]"
      />

      <div className="conteneur relative z-3 grid items-center gap-[clamp(36px,5vw,64px)] lg:grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)]">
        <div>
          <p className="eyebrow reveal">Soundboard Windows · open source</p>

          <h1
            className="reveal font-display leading-[0.82] font-black uppercase"
            style={{ transitionDelay: "60ms" }}
          >
            <span className="block text-[clamp(4.2rem,11vw,8rem)] tracking-[-0.015em] text-neige [font-variation-settings:'opsz'_72]">
              Sid
            </span>
            <span className="mt-1.5 block text-[clamp(1.4rem,3.2vw,2.5rem)] font-bold tracking-[0.16em] text-gel-sombre">
              Soundboard
            </span>
          </h1>

          <p
            className="reveal mt-7 mb-8 max-w-[46ch] text-[clamp(1.02rem,1.5vw,1.14rem)] text-brume"
            style={{ transitionDelay: "120ms" }}
          >
            Une soundboard qui balance vos sons sur Discord sans jamais toucher à vos FPS. Tous les effets
            sont calculés <em className="text-pelage italic">avant</em> la lecture : quand vous appuyez sur
            une touche, le processeur n&apos;a plus rien à faire.
          </p>

          <div className="reveal flex flex-wrap gap-3" style={{ transitionDelay: "180ms" }}>
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
            className="reveal mt-8 flex flex-wrap gap-x-7 gap-y-2 font-mono text-[12.5px]"
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

      <BordGlace className="fill-nuit" />
    </section>
  );
}
