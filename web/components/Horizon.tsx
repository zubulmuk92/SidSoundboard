import { crete, stalactites } from "@/lib/dessin";

const RIDEAU = stalactites(1440, 7);
// Les cimes démarrent bas dans le viewBox : il faut du ciel entre le rideau
// de stalactites et la première crête, sinon la scène se referme.
const CRETE_LOINTAINE = crete({ sommets: 13, cime: 84, creux: 152, graine: 3 });
const CRETE_PROCHE = crete({ sommets: 9, cime: 126, creux: 196, graine: 11 });

/** Une gueule de grotte qui ouvre sur la banquise : stalactites suspendues au
 *  bord haut, deux crêtes glaciaires en contrebas. Sépare deux sections. */
export function Horizon() {
  return (
    <div
      aria-hidden="true"
      className="relative z-3 h-[clamp(150px,17vw,240px)] overflow-clip bg-[linear-gradient(180deg,var(--color-nuit-2)_0%,#0B2438_45%,var(--color-nuit)_100%)]"
    >
      {/* lueur froide au ras de l'horizon */}
      <div className="absolute inset-x-0 bottom-0 h-2/3 bg-[radial-gradient(60%_100%_at_50%_100%,rgb(47_168_255/0.16),transparent_70%)]" />

      <svg
        viewBox="0 0 1440 220"
        preserveAspectRatio="none"
        className="absolute inset-0 h-full w-full"
      >
        <path d={CRETE_LOINTAINE} fill="#0E2739" />
        <path d={CRETE_PROCHE} fill="var(--color-nuit)" />
      </svg>

      <svg
        viewBox="0 0 1440 66"
        preserveAspectRatio="none"
        className="absolute inset-x-0 top-0 h-[clamp(32px,4vw,56px)] w-full"
      >
        <path d={RIDEAU} fill="rgb(127 231 242 / 0.16)" stroke="rgb(127 231 242 / 0.28)" strokeWidth="0.6" />
      </svg>
    </div>
  );
}
