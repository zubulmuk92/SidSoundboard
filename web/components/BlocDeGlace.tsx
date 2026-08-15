/* eslint-disable @next/next/no-img-element */

/** Sid pris dans un bloc de banquise, en 3D.
 *
 *  Six facettes givrées en CSS `preserve-3d`. La mascotte est un plan unique
 *  qui contre-tourne à l'inverse du cube, donc elle fait toujours face à la
 *  caméra pendant que la glace tourne autour d'elle.
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
      </div>
    </div>
  );
}
