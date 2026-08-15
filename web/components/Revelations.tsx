"use client";

import { useEffect } from "react";

/** Révèle les éléments portant la classe `reveal` à leur entrée dans le viewport.
 *
 *  Un seul observateur pour toute la page : le balisage reste rendu côté serveur
 *  (donc entièrement lisible par les crawlers), seule l'opacité est pilotée ici. */
export function Revelations() {
  useEffect(() => {
    const cibles = document.querySelectorAll<HTMLElement>(".reveal");

    const mouvementReduit = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (mouvementReduit || !("IntersectionObserver" in window)) {
      for (const el of cibles) el.dataset.visible = "true";
      return;
    }

    const io = new IntersectionObserver(
      (entrees) => {
        for (const e of entrees) {
          if (!e.isIntersecting) continue;
          (e.target as HTMLElement).dataset.visible = "true";
          io.unobserve(e.target);
        }
      },
      { threshold: 0.15, rootMargin: "0px 0px -8% 0px" },
    );

    for (const el of cibles) io.observe(el);
    return () => io.disconnect();
  }, []);

  return null;
}
