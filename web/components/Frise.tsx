/** Frise de gravures rupestres.
 *
 *  Quatre motifs — mammouth, tigre à dents de sabre, gland, main en négatif —
 *  répétés à des échelles différentes et posés sur une même ligne de sol, à la
 *  manière d'une paroi de grotte. Les défenses et les crocs sont peints dans un
 *  ton plus clair : sur un aplat unique ils disparaissaient dans la masse. */

const SOL = 134;

function Mammouth() {
  return (
    <g fill="currentColor">
      <path d="M52 60 C48 32 62 12 84 10 C108 8 126 22 130 46 C133 60 128 70 116 70 L62 70 C54 70 52 66 52 60 Z" />
      <ellipse cx="36" cy="44" rx="25" ry="27" />
      <path d="M30 60 C24 78 26 94 32 108 C35 115 45 113 44 104 C41 90 40 74 46 58 Z" />
      <g stroke="currentColor" strokeWidth="15" strokeLinecap="round" fill="none">
        <path d="M66 68 V106" />
        <path d="M84 68 V102" />
        <path d="M108 68 V106" />
        <path d="M123 68 V102" />
      </g>
      <path d="M131 50 C141 52 144 61 139 69" stroke="currentColor" strokeWidth="5" fill="none" strokeLinecap="round" />
      <path className="ivoire" d="M28 68 C12 74 2 88 5 100 C6 106 14 105 13 98 C11 88 17 79 30 76 Z" />
    </g>
  );
}

function Tigre() {
  return (
    <g fill="currentColor">
      <path d="M34 44 C34 28 52 24 72 26 C92 28 104 34 104 48 C104 60 90 64 68 64 C46 64 34 56 34 44 Z" />
      <circle cx="24" cy="42" r="17" />
      <path d="M12 28 l2 -13 l11 7 Z" />
      <path d="M34 27 l11 -9 l1 12 Z" />
      <g stroke="currentColor" strokeWidth="10" strokeLinecap="round" fill="none">
        <path d="M44 62 V86" />
        <path d="M58 62 V83" />
        <path d="M86 62 V86" />
        <path d="M98 62 V83" />
      </g>
      <path d="M104 40 C118 33 124 18 116 6" stroke="currentColor" strokeWidth="6" fill="none" strokeLinecap="round" />
      <g className="ivoire-trait" strokeWidth="5" strokeLinecap="round" fill="none">
        <path d="M17 54 C16 63 16 69 18 74" />
        <path d="M28 55 C28 63 28 67 30 71" />
      </g>
    </g>
  );
}

function Main() {
  return (
    <g fill="currentColor">
      <ellipse cx="30" cy="54" rx="18" ry="20" />
      <g stroke="currentColor" strokeWidth="10" strokeLinecap="round" fill="none">
        <path d="M17 42 L13 14" />
        <path d="M27 40 L26 6" />
        <path d="M37 40 L40 8" />
        <path d="M46 44 L54 18" />
        <path d="M48 61 L66 52" />
      </g>
    </g>
  );
}

function Gland() {
  return (
    <g fill="currentColor">
      <path d="M4 22 C4 8 36 8 36 22 C36 25 4 25 4 22 Z" />
      <path d="M8 23 C8 42 14 55 20 55 C26 55 32 42 32 23 Z" />
      <path d="M20 9 C20 4 22 1 25 -1" stroke="currentColor" strokeWidth="3.5" fill="none" strokeLinecap="round" />
    </g>
  );
}

/** `sol` = ordonnée à laquelle la figure touche le sol, dans son propre repère.
 *  Les mains sont des pochoirs : elles flottent sur la paroi, hors de la ligne. */
const MOTIFS = {
  mammouth: { dessin: <Mammouth />, sol: 115 },
  tigre: { dessin: <Tigre />, sol: 88 },
  gland: { dessin: <Gland />, sol: 55 },
  main: { dessin: <Main />, sol: null },
} as const;

type Pose = { motif: keyof typeof MOTIFS; x: number; e: number; y?: number };

const PAROI: Pose[] = [
  { motif: "main", x: 30, e: 0.75, y: 22 },
  { motif: "mammouth", x: 95, e: 0.95 },
  { motif: "mammouth", x: 248, e: 0.5 },
  { motif: "tigre", x: 345, e: 0.85 },
  { motif: "gland", x: 465, e: 0.9 },
  { motif: "main", x: 520, e: 0.6, y: 40 },
  { motif: "mammouth", x: 585, e: 0.72 },
  { motif: "tigre", x: 710, e: 0.6 },
  { motif: "gland", x: 800, e: 0.7 },
  { motif: "mammouth", x: 845, e: 0.42 },
  { motif: "main", x: 930, e: 0.68, y: 30 },
  { motif: "tigre", x: 1000, e: 0.5 },
  { motif: "mammouth", x: 1085, e: 0.88 },
  { motif: "gland", x: 1235, e: 0.8 },
  { motif: "main", x: 1290, e: 0.72, y: 26 },
  { motif: "mammouth", x: 1360, e: 0.45 },
];

function Paroi() {
  return (
    <>
      {PAROI.map((pose, i) => {
        const { dessin, sol } = MOTIFS[pose.motif];
        const y = pose.y ?? SOL - (sol as number) * pose.e;
        return (
          <g key={i} transform={`translate(${pose.x} ${y.toFixed(1)}) scale(${pose.e})`}>
            {dessin}
          </g>
        );
      })}
    </>
  );
}

export function Frise() {
  return (
    <div
      aria-hidden="true"
      className="relative z-3 h-[clamp(112px,12vw,168px)] overflow-clip border-y border-gel/12 bg-[linear-gradient(180deg,#0A1B29_0%,#0C2233_55%,var(--color-nuit)_100%)]"
    >
      {/* `meet` plutôt que `slice` : jamais de figure rognée, et surtout jamais
          déformée — sur un dessin figuratif, une échelle non uniforme se voit. */}
      <svg
        viewBox="0 0 1440 150"
        preserveAspectRatio="xMidYMax meet"
        className="absolute inset-0 hidden h-full w-full text-gel/45 md:block"
      >
        <Paroi />
      </svg>

      {/* Sur petit écran, la paroi entière donnerait des figures minuscules :
          on cadre sur un groupe plutôt que de tout faire tenir. */}
      <svg
        viewBox="80 0 400 150"
        preserveAspectRatio="xMidYMax meet"
        className="absolute inset-0 h-full w-full text-gel/45 md:hidden"
      >
        <Paroi />
      </svg>
    </div>
  );
}
