const autres = [
  "Le fichier est chargé en RAM",
  "Volume et vitesse recalculés à chaque lecture",
  "Le CPU travaille pendant que vous jouez",
  "Ce que vous entendez ≠ ce que Discord entend",
];

const sid = [
  "Le fichier est lu en streaming depuis le disque",
  "Les effets sont rendus une fois, puis mis en cache",
  "Lecture = ouvrir un flux, rien d'autre",
  "Les deux sorties jouent exactement le même rendu",
];

const chiffres = [
  { cle: "CPU pendant la lecture", valeur: "~0 %" },
  { cle: "RAM au repos", valeur: "< 30 Mo" },
  { cle: "Moteur audio", valeur: "miniaudio" },
  { cle: "Nettoyage du cache", valeur: "automatique" },
];

export function Moteur() {
  return (
    <section id="moteur" className="section">
      <div className="conteneur">
        <p className="eyebrow reveal">Le moteur</p>
        <h2 className="titre-section reveal">Rien à calculer au moment où ça joue.</h2>
        <p className="chapo reveal">
          La quasi-totalité des soundboards applique le volume, la vitesse et les effets en temps réel,
          pendant la lecture. C&apos;est du calcul, donc du CPU, donc des micro-freezes en jeu. SidSoundboard
          fait l&apos;inverse : FFmpeg fabrique le fichier définitif en arrière-plan quand vous réglez le son,
          une seule fois.
        </p>

        <div className="reveal mb-12 grid gap-4.5 md:grid-cols-2">
          <article className="panneau p-6.5 opacity-80">
            <h3 className="font-display text-[26px] font-black tracking-[0.02em] uppercase">Les autres</h3>
            <p className="mt-1 mb-5 font-mono text-[11px] tracking-[0.14em] text-brume uppercase">
              Calcul en temps réel
            </p>
            <ul>
              {autres.map((t) => (
                <li
                  key={t}
                  className="relative border-t border-white/5 py-2.5 pl-6.5 text-[15px] text-brume before:absolute before:top-2.5 before:left-0 before:font-mono before:text-[#7C93A6] before:content-['×']"
                >
                  {t}
                </li>
              ))}
            </ul>
          </article>

          <article className="panneau border-ambre/35 bg-[rgb(30_22_16/0.4)] p-6.5">
            <h3 className="font-display text-[26px] font-black tracking-[0.02em] uppercase">SidSoundboard</h3>
            <p className="mt-1 mb-5 font-mono text-[11px] tracking-[0.14em] text-ambre uppercase">
              Rendu pré-calculé
            </p>
            <ul>
              {sid.map((t) => (
                <li
                  key={t}
                  className="relative border-t border-white/5 py-2.5 pl-6.5 text-[15px] before:absolute before:top-2.5 before:left-0 before:font-mono before:text-ambre before:content-['→']"
                >
                  {t}
                </li>
              ))}
            </ul>
          </article>
        </div>

        <dl className="reveal grid gap-px overflow-hidden rounded-xl border border-gel/14 bg-gel/14 sm:grid-cols-2 lg:grid-cols-4">
          {chiffres.map((c) => (
            <div key={c.cle} className="bg-nuit px-5 py-5.5">
              <dt className="mb-2.5 font-mono text-[10.5px] tracking-[0.12em] text-gel-sombre uppercase">
                {c.cle}
              </dt>
              <dd className="font-display text-[34px] leading-none font-black">{c.valeur}</dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}
