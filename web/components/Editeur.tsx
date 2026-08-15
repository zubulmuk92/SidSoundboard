const cartes = [
  {
    titre: "Découpe à la souris",
    texte:
      "Attrapez les poignées sur la waveform et gardez uniquement le passage qui compte. La coupe est exacte à l'échantillon près.",
  },
  {
    titre: "Volume, vitesse, basses, réverb",
    texte: "Quatre réglages par son. Un rendu boosté est limité proprement au lieu de saturer.",
  },
  {
    titre: "Fondus par son",
    texte:
      "Entrée et sortie réglables individuellement, plus un crossfade global entre deux sons enchaînés.",
  },
  {
    titre: "Import YouTube",
    texte:
      "Collez une URL YouTube ou YT Music : le son atterrit dans la bibliothèque, prêt à être découpé.",
  },
  {
    titre: "Raccourcis globaux",
    texte:
      "Vos touches fonctionnent même quand le jeu a le focus. Une touche panique arrête tout, instantanément.",
  },
  {
    titre: "Édition non destructive",
    texte:
      "Le fichier d'origine n'est jamais modifié. Vous pouvez revenir sur n'importe quel réglage, à tout moment.",
  },
];

export function Editeur() {
  return (
    <section id="editeur" className="section">
      <div className="conteneur">
        <p className="eyebrow reveal">Dans la boîte</p>
        <h2 className="titre-section reveal">Chaque son se règle, se coupe et se garde intact.</h2>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {cartes.map((c, i) => (
            <article
              key={c.titre}
              className="reveal carte-3d rounded-xl border border-gel/13 bg-[linear-gradient(170deg,rgb(20_49_72/0.5),rgb(6_16_25/0.3))] px-6 pt-6.5 pb-7 hover:border-gel/40"
              style={{ transitionDelay: `${(i % 3) * 60}ms` }}
            >
              <h3 className="mb-2.5 font-display text-[21px] font-bold tracking-[0.02em] text-gel uppercase">
                {c.titre}
              </h3>
              <p className="text-[14.5px] text-brume">{c.texte}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
