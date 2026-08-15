const LEGENDE =
  "Schéma : SidSoundboard envoie le même rendu vers le casque à volume réduit et vers un câble virtuel à plein volume, qui alimente Discord.";

function Fleches({ suffixe }: { suffixe: string }) {
  return (
    <defs>
      <marker id={`fleche-gel${suffixe}`} markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto">
        <path d="M0 0.5 8 4.5 0 8.5z" fill="var(--color-gel)" />
      </marker>
      <marker id={`fleche-ambre${suffixe}`} markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto">
        <path d="M0 0.5 8 4.5 0 8.5z" fill="var(--color-ambre)" />
      </marker>
    </defs>
  );
}

export function Routage() {
  return (
    <section id="routage" className="section section-alt">
      <div className="conteneur">
        <p className="eyebrow reveal">Double sortie</p>
        <h2 className="titre-section reveal">
          Vous l&apos;entendez doucement. Vos potes le prennent en pleine face.
        </h2>
        <p className="chapo reveal">
          SidSoundboard pilote deux cartes son en même temps et garde les deux flux synchronisés. Votre casque
          reçoit un volume confortable, le câble virtuel envoie le son à Discord au niveau que vous voulez.
        </p>

        <div className="panneau reveal p-[clamp(16px,3vw,32px)]">
          {/* Version large */}
          <svg viewBox="0 0 790 260" role="img" aria-label={LEGENDE} className="hidden h-auto w-full md:block">
            <Fleches suffixe="" />

            <g className="rt-noeud">
              <rect x="8" y="98" width="176" height="64" rx="10" />
              <text x="96" y="124" className="rt-titre">
                SidSoundboard
              </text>
              <text x="96" y="145" className="rt-meta">
                rendu unique
              </text>
            </g>

            <path className="rt-fil rt-fil-gel" d="M188 122h84c14 0 14-56 28-56h140" markerEnd="url(#fleche-gel)" />
            <path
              className="rt-fil rt-fil-ambre"
              d="M188 138h84c14 0 14 56 28 56h140"
              markerEnd="url(#fleche-ambre)"
            />

            <g className="rt-noeud rt-noeud-gel">
              <rect x="452" y="38" width="180" height="56" rx="10" />
              <text x="542" y="62" className="rt-titre">
                Casque
              </text>
              <text x="542" y="81" className="rt-meta">
                volume 25 %
              </text>
            </g>

            <g className="rt-noeud rt-noeud-ambre">
              <rect x="452" y="166" width="180" height="56" rx="10" />
              <text x="542" y="190" className="rt-titre">
                Câble virtuel
              </text>
              <text x="542" y="209" className="rt-meta">
                volume 100 %
              </text>
            </g>

            <path className="rt-fil rt-fil-ambre" d="M636 194h44" markerEnd="url(#fleche-ambre)" />
            <text x="690" y="199" className="rt-meta fill-ambre [text-anchor:start]">
              Discord
            </text>
          </svg>

          {/* Même schéma, empilé, pour les petits écrans */}
          <svg viewBox="0 0 340 268" role="img" aria-label={LEGENDE} className="h-auto w-full md:hidden">
            <Fleches suffixe="-c" />

            <g className="rt-noeud">
              <rect x="70" y="6" width="200" height="58" rx="10" />
              <text x="170" y="32" className="rt-titre">
                SidSoundboard
              </text>
              <text x="170" y="51" className="rt-meta">
                rendu unique
              </text>
            </g>

            <path className="rt-fil rt-fil-gel" d="M170 64v32H90v28" markerEnd="url(#fleche-gel-c)" />
            <path className="rt-fil rt-fil-ambre" d="M170 64v32h80v28" markerEnd="url(#fleche-ambre-c)" />

            <g className="rt-noeud rt-noeud-gel">
              <rect x="16" y="130" width="148" height="56" rx="10" />
              <text x="90" y="155" className="rt-titre">
                Casque
              </text>
              <text x="90" y="174" className="rt-meta">
                volume 25 %
              </text>
            </g>

            <g className="rt-noeud rt-noeud-ambre">
              <rect x="176" y="130" width="148" height="56" rx="10" />
              <text x="250" y="155" className="rt-titre">
                Câble virtuel
              </text>
              <text x="250" y="174" className="rt-meta">
                volume 100 %
              </text>
            </g>

            <path className="rt-fil rt-fil-ambre" d="M250 186v34" markerEnd="url(#fleche-ambre-c)" />
            <text x="250" y="248" className="rt-meta fill-ambre">
              Discord
            </text>
          </svg>
        </div>

        <p className="reveal mt-6.5 max-w-[70ch] border-l-2 border-gel/30 pl-4 font-mono text-xs leading-relaxed text-brume">
          VB-Cable s&apos;installe séparément — SidSoundboard ne l&apos;installe pas à votre place et ne
          touche pas à vos périphériques système.
        </p>
      </div>
    </section>
  );
}
