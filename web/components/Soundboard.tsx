"use client";

import Image from "next/image";
import { useCallback, useEffect, useRef, useState } from "react";
import { couperTout, DALLES, joue, jouer, spectre, type NomSon } from "@/lib/audio";

const BARRES = 48;

// Profil figé de la waveform au repos : une carotte de glace vue de côté.
const GELEE = Array.from({ length: BARRES }, (_, i) => {
  const p = i / (BARRES - 1);
  return 0.18 + Math.abs(Math.sin(p * 7.5)) * 0.14 + Math.abs(Math.sin(p * 2.1)) * 0.1;
});

/** La soundboard de glace jouable : six dalles, au clic ou au clavier,
 *  plus la touche panique de l'application. */
export function Soundboard({ sid }: { sid: string }) {
  const [frappee, setFrappee] = useState<NomSon | null>(null);
  const [enLecture, setEnLecture] = useState(false);
  const vizRef = useRef<HTMLCanvasElement>(null);
  const minuteur = useRef<number | undefined>(undefined);

  const declencher = useCallback((son: NomSon) => {
    jouer(son);
    setFrappee(son);
    window.clearTimeout(minuteur.current);
    minuteur.current = window.setTimeout(() => setFrappee(null), 90);
  }, []);

  const couper = useCallback(() => {
    couperTout();
    setEnLecture(false);
  }, []);

  // Raccourcis clavier : les touches des dalles, Espace/Échap pour tout couper.
  useEffect(() => {
    const surTouche = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey || e.repeat) return;

      const cible = document.activeElement;
      const surControle = cible instanceof HTMLElement && /^(BUTTON|A|INPUT|TEXTAREA|SELECT)$/.test(cible.tagName);

      if (e.key === "Escape" || (e.key === " " && !surControle)) {
        e.preventDefault();
        couper();
        return;
      }

      const dalle = DALLES.find((d) => d.touche === e.key.toLowerCase());
      if (dalle && !surControle) {
        e.preventDefault();
        declencher(dalle.son);
      }
    };

    document.addEventListener("keydown", surTouche);
    return () => document.removeEventListener("keydown", surTouche);
  }, [couper, declencher]);

  // Waveform : gelée au repos, vivante pendant la lecture.
  useEffect(() => {
    const toile = vizRef.current;
    if (!toile) return;
    const ctx = toile.getContext("2d");
    if (!ctx) return;

    const mouvementReduit = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let frame = 0;
    let vivantPrecedent = false;

    const caler = () => {
      const r = toile.getBoundingClientRect();
      if (r.width) {
        toile.width = Math.round(r.width);
        toile.height = Math.round(r.height);
      }
    };

    const dessiner = () => {
      const { width: w, height: h } = toile;
      ctx.clearRect(0, 0, w, h);
      const data = mouvementReduit ? null : spectre();
      const pas = w / BARRES;

      for (let i = 0; i < BARRES; i++) {
        let v = GELEE[i];
        if (data) {
          const idx = Math.floor((i / BARRES) * data.length);
          v = Math.max(GELEE[i], data[idx] / 255);
        }
        const haut = Math.max(3, v * h * 0.92);
        ctx.fillStyle = data
          ? `rgba(47, 168, 255, ${0.45 + v * 0.55})`
          : `rgba(127, 231, 242, ${0.18 + v * 0.5})`;
        ctx.fillRect(i * pas + 1, (h - haut) / 2, Math.max(2, pas - 3), haut);
      }
    };

    const boucle = () => {
      const vivant = joue();
      if (vivant !== vivantPrecedent) {
        vivantPrecedent = vivant;
        setEnLecture(vivant);
      }
      dessiner();
      frame = requestAnimationFrame(boucle);
    };

    const surRedimension = () => {
      caler();
      if (mouvementReduit) dessiner();
    };

    caler();
    window.addEventListener("resize", surRedimension);
    if (mouvementReduit) dessiner();
    else frame = requestAnimationFrame(boucle);

    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("resize", surRedimension);
    };
  }, []);

  return (
    <div className="relative overflow-hidden rounded-2xl border border-gel/15 bg-[linear-gradient(160deg,rgb(20_49_72/0.92),rgb(10_26_40/0.92))] p-6 shadow-[0_40px_80px_-40px_#000,inset_0_1px_0_rgb(255_255_255/0.08)] backdrop-blur-[6px] sm:p-8">
      <div className="flex flex-wrap items-baseline justify-between gap-4">
        <h2 className="font-display text-[22px] font-bold tracking-[0.04em] uppercase">Essayez-la ici</h2>
        <p className="font-mono text-[11.5px] text-brume">
          Cliquez une dalle, ou tapez sa touche.{" "}
          <kbd className="rounded border border-gel/30 bg-gel/10 px-1.5 py-px font-mono text-[11px] text-gel">
            Espace
          </kbd>{" "}
          coupe tout.
        </p>
      </div>

      <div className="my-7 grid grid-cols-2 gap-3.5 sm:grid-cols-3">
        {DALLES.map((d) => (
          <button
            key={d.son}
            type="button"
            className="dalle"
            data-frappee={frappee === d.son ? "true" : "false"}
            aria-label={`Jouer ${d.nom}, touche ${d.touche.toUpperCase()}`}
            onClick={() => declencher(d.son)}
          >
            <span
              aria-hidden="true"
              className="relative z-10 rounded bg-[rgb(190_235_245/0.85)] px-[7px] py-px font-mono text-[11px] font-semibold tracking-[0.04em] text-nuit"
            >
              {d.touche.toUpperCase()}
            </span>
            <span className="relative z-10 text-[13.5px] leading-tight font-semibold">{d.nom}</span>
          </button>
        ))}
      </div>

      {/* La waveform prend toute la largeur, la mascotte et la touche panique
          se partagent la ligne du dessous. */}
      <div className="border-t border-gel/12 pt-6">
        <canvas ref={vizRef} aria-hidden="true" className="h-14 w-full" />

        <div className="mt-4 flex items-center justify-between gap-4">
          <div className="relative w-24 flex-none">
            <Image
              src={sid}
              alt="Sid, la mascotte de SidSoundboard, casque sur les oreilles"
              width={677}
              height={369}
              priority
              className="block h-auto w-24"
            />
            {enLecture && (
              <>
                <span
                  aria-hidden="true"
                  className="anim-onde absolute top-[52%] left-1/2 -mt-[46px] -ml-[46px] h-[92px] w-[92px] rounded-full border border-gel"
                />
                <span
                  aria-hidden="true"
                  className="anim-onde absolute top-[52%] left-1/2 -mt-[46px] -ml-[46px] h-[92px] w-[92px] rounded-full border border-gel [animation-delay:0.38s]"
                />
              </>
            )}
          </div>

          <button
            type="button"
            onClick={couper}
            className="flex-none cursor-pointer rounded-lg border border-azur/50 px-3.5 py-2.5 font-mono text-[11px] tracking-[0.12em] text-azur uppercase transition-colors hover:bg-azur hover:text-azur-texte"
          >
            Panique
          </button>
        </div>
      </div>

      <p className="mt-5 font-mono text-[10.5px] leading-normal text-brume/70">
        Sons de démonstration synthétisés dans le navigateur. Dans l&apos;application, ce sont vos fichiers.
      </p>
    </div>
  );
}
