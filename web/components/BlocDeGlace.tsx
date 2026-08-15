/* eslint-disable @next/next/no-img-element */

/** Sid pris dans un bloc de banquise, en 3D.
 *
 *  Six facettes givrées en CSS `preserve-3d`, et la mascotte sur deux plans
 *  croisés pour qu'elle reste visible quel que soit l'angle de rotation.
 *  `next/image` n'apporterait rien ici : la taille est fixée par le CSS et
 *  l'élément est purement décoratif. */
export function BlocDeGlace({ sid }: { sid: string }) {
  return (
    <div className="scene" aria-hidden="true">
      <div className="glacon">
        <span className="facette facette-avant" />
        <span className="facette facette-arriere" />
        <span className="facette facette-droite" />
        <span className="facette facette-gauche" />
        <span className="facette facette-haut" />
        <span className="facette facette-bas" />
        <img className="prisonnier" src={sid} alt="" />
        <img className="prisonnier prisonnier-croix" src={sid} alt="" />
      </div>
    </div>
  );
}
