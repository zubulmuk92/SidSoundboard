import type { ReactNode } from "react";

const etapes: { titre: string; texte: ReactNode }[] = [
  {
    titre: "Lancez le .exe",
    texte: (
      <>
        Un seul fichier autonome, rien à installer. Windows peut afficher un avertissement SmartScreen tant
        que l&apos;exécutable n&apos;est pas signé :{" "}
        <span className="whitespace-nowrap">&laquo; Informations complémentaires &raquo;</span> puis{" "}
        <span className="whitespace-nowrap">&laquo; Exécuter quand même &raquo;</span>.
      </>
    ),
  },
  {
    titre: "Choisissez vos sorties",
    texte: (
      <>
        Dans <strong className="font-semibold text-pelage">Réglages</strong>, sélectionnez votre casque comme
        sortie principale. Activez la double sortie et pointez la seconde vers VB-Cable si vous voulez
        alimenter Discord.
      </>
    ),
  },
  {
    titre: "Remplissez la bibliothèque",
    texte: (
      <>
        Importez vos MP3 et WAV ou collez une URL YouTube, réglez chaque son dans l&apos;éditeur, assignez vos
        touches. C&apos;est prêt.
      </>
    ),
  },
];

export function Installation() {
  return (
    <section id="installation" className="section section-alt">
      <div className="conteneur">
        <p className="eyebrow reveal">Installation</p>
        <h2 className="titre-section reveal">Trois étapes, dans cet ordre.</h2>

        <ol>
          {etapes.map((e, i) => (
            <li
              key={e.titre}
              className="reveal grid gap-5 border-t border-gel/14 py-7 last:border-b sm:grid-cols-[84px_1fr]"
            >
              <span
                aria-hidden="true"
                className="font-display text-[34px] leading-[0.8] font-black text-transparent [-webkit-text-stroke:1px_var(--color-gel-sombre)] sm:text-[52px]"
              >
                {String(i + 1).padStart(2, "0")}
              </span>
              <div>
                <h3 className="mb-2 text-[19px] font-semibold">{e.titre}</h3>
                <p className="max-w-[68ch] text-[15px] text-brume">{e.texte}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
