const MOTS = [
  "Mammouth",
  "Craquement",
  "Tigre à dents de sabre",
  "Corne de brume",
  "Paresseux",
  "Dérive des continents",
  "Blizzard",
  "Le gland",
  "Banquise",
  "−30 °C",
];

/** Bandeau défilant, purement décoratif : le vocabulaire de la banquise en
 *  travers de la page. Masqué aux lecteurs d'écran, où il ne serait qu'une
 *  liste de mots sans contexte. */
export function Bandeau() {
  return (
    <div
      aria-hidden="true"
      className="relative z-3 overflow-clip border-y border-gel/12 bg-nuit-2 py-3.5"
    >
      <div className="bandeau-piste">
        {/* deux passes identiques : la boucle se referme sans saut */}
        {[0, 1].map((passe) => (
          <div key={passe} className="flex shrink-0">
            {MOTS.map((mot) => (
              <span
                key={mot}
                className="flex items-center gap-6 pr-6 font-mono text-[12px] tracking-[0.22em] whitespace-nowrap text-brume uppercase"
              >
                {mot}
                <span className="text-azur">◆</span>
              </span>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
