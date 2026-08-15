/** Petit bloc de banquise en 3D, en fond de décor.
 *  Même mécanique que le grand, sans mascotte à l'intérieur. */
export function EclatGlace({ className = "", duree = "34s" }: { className?: string; duree?: string }) {
  return (
    <div
      aria-hidden="true"
      className={`scene scene-eclat pointer-events-none absolute ${className}`}
      style={{ ["--duree" as string]: duree }}
    >
      <div className="glacon">
        <span className="facette facette-avant" />
        <span className="facette facette-arriere" />
        <span className="facette facette-droite" />
        <span className="facette facette-gauche" />
        <span className="facette facette-haut" />
        <span className="facette facette-bas" />
      </div>
    </div>
  );
}
