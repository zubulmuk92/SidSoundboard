"use client";

import { useEffect, useRef } from "react";

type Flocon = { x: number; y: number; r: number; v: number; d: number };

/** Neige ambiante sur toute la page. Coupée si l'utilisateur limite les animations. */
export function Neige() {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const toile = ref.current;
    if (!toile) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const ctx = toile.getContext("2d");
    if (!ctx) return;

    let flocons: Flocon[] = [];
    let L = 0;
    let H = 0;
    let frame = 0;

    const dimensionner = () => {
      L = toile.width = window.innerWidth;
      H = toile.height = window.innerHeight;
      const cible = Math.round(Math.min(90, L / 16));
      flocons = Array.from({ length: cible }, () => ({
        x: Math.random() * L,
        y: Math.random() * H,
        r: 0.7 + Math.random() * 1.9,
        v: 0.25 + Math.random() * 0.75,
        d: Math.random() * Math.PI * 2,
      }));
    };

    const tomber = () => {
      ctx.clearRect(0, 0, L, H);
      ctx.fillStyle = "#DCEEF6";
      for (const f of flocons) {
        f.d += 0.008;
        f.y += f.v;
        f.x += Math.sin(f.d) * 0.4;
        if (f.y > H + 4) {
          f.y = -4;
          f.x = Math.random() * L;
        }
        ctx.globalAlpha = 0.25 + (f.r / 2.6) * 0.5;
        ctx.beginPath();
        ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2);
        ctx.fill();
      }
      frame = requestAnimationFrame(tomber);
    };

    dimensionner();
    window.addEventListener("resize", dimensionner);
    frame = requestAnimationFrame(tomber);

    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("resize", dimensionner);
    };
  }, []);

  return (
    <canvas
      ref={ref}
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 z-[2] h-full w-full opacity-55"
    />
  );
}
