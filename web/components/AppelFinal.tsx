import { asset, liens } from "@/lib/site";
import { BlocDeGlace } from "./BlocDeGlace";

/** Dernier appel à l'action, sous une lueur d'aurore. */
export function AppelFinal() {
  return (
    <section className="section overflow-clip bg-[linear-gradient(180deg,var(--color-nuit)_0%,#07202F_100%)] text-center">
      <div
        aria-hidden="true"
        className="anim-halo absolute bottom-[-40%] left-1/2 aspect-square w-[min(900px,110%)] -translate-x-1/2 bg-[radial-gradient(circle,rgb(47_168_255/0.26)_0%,rgb(127_231_242/0.06)_40%,transparent_68%)]"
      />

      <div className="conteneur relative z-10">
        <BlocDeGlace sid={asset("/sid.png")} />

        <h2 className="reveal mx-auto mt-10 mb-3.5 max-w-[16ch] font-display text-[clamp(2.4rem,6.5vw,4.6rem)] leading-[0.9] font-black text-balance uppercase">
          Il fait &minus;30 dehors. Allumez le son.
        </h2>
        <p className="reveal mb-8 text-[1.05rem] text-brume">
          Gratuit, open source, sans compte et sans télémétrie.
        </p>
        <div className="reveal flex flex-wrap justify-center gap-3">
          <a className="btn btn-azur max-sm:flex-1 max-sm:justify-center" href={liens.telechargement}>
            Télécharger SidSoundboard
          </a>
          <a className="btn btn-gel max-sm:flex-1 max-sm:justify-center" href={liens.versions} rel="noopener">
            Toutes les versions
          </a>
        </div>
      </div>
    </section>
  );
}
