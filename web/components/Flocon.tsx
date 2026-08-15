import { ANGLES_FLOCON, BRANCHE_FLOCON } from "@/lib/dessin";

/** Cristal à six branches, construit par rotation d'une seule branche.
 *  Décoratif : il tourne très lentement en fond de section. */
export function Flocon({ className = "", duree = "120s" }: { className?: string; duree?: string }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 200 200"
      className={`anim-cristal pointer-events-none absolute ${className}`}
      style={{ animationDuration: duree }}
    >
      <g fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
        {ANGLES_FLOCON.map((angle) => (
          <path key={angle} d={BRANCHE_FLOCON} transform={`rotate(${angle} 100 100)`} />
        ))}
      </g>
      <circle cx="100" cy="100" r="4.5" fill="currentColor" />
    </svg>
  );
}
