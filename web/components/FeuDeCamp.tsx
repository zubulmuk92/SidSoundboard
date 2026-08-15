import Image from "next/image";
import { asset, liens } from "@/lib/site";

/** Appel à l'action final : le seul endroit chaud de la page. */
export function FeuDeCamp() {
  return (
    <section className="relative z-3 overflow-clip bg-[linear-gradient(180deg,var(--color-nuit)_0%,#150E0A_100%)] px-6 py-[clamp(72px,11vw,128px)] text-center">
      <div
        aria-hidden="true"
        className="anim-braise absolute bottom-[-40%] left-1/2 aspect-square w-[min(900px,110%)] -translate-x-1/2 bg-[radial-gradient(circle,rgb(255_138_61/0.3)_0%,rgb(255_138_61/0.07)_40%,transparent_68%)]"
      />

      <div className="relative z-10 mx-auto max-w-[1120px]">
        <Image
          src={asset("/sid.png")}
          alt=""
          width={677}
          height={369}
          className="mx-auto mb-4.5 h-auto w-[clamp(120px,16vw,190px)]"
        />
        <h2 className="reveal mx-auto mb-3.5 max-w-[16ch] font-display text-[clamp(2.4rem,6.5vw,4.6rem)] leading-[0.9] font-black text-balance uppercase">
          Il fait &minus;30 dehors. Allumez le son.
        </h2>
        <p className="reveal mb-8.5 text-[1.05rem] text-pelage">
          Gratuit, open source, sans compte et sans télémétrie.
        </p>
        <div className="reveal flex flex-wrap justify-center gap-3.5">
          <a className="btn btn-braise max-sm:flex-1 max-sm:justify-center" href={liens.telechargement}>
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
