/** Générateurs de tracés SVG.
 *
 *  Tout est déterministe : un générateur pseudo-aléatoire à graine fixe donne
 *  le même dessin à chaque rendu. Indispensable ici — `Math.random()` ferait
 *  diverger le HTML du serveur et celui du client. Et chaque tracé se termine
 *  exactement sur la largeur du viewBox, sinon le motif s'arrête en route. */

function alea(graine: number): () => number {
  let x = graine || 1;
  return () => {
    x ^= x << 13;
    x ^= x >>> 17;
    x ^= x << 5;
    return Math.abs(x % 10000) / 10000;
  };
}

/** Rideau de stalactites suspendu au bord haut. */
export function stalactites(largeur = 1440, graine = 7): string {
  const r = alea(graine);
  const bord = 3;
  const morceaux = [`M0 ${bord}`];
  let x = 0;

  while (x < largeur) {
    const ecart = 14 + r() * 30;
    const base = 9 + r() * 15;
    const longueur = 12 + r() * 52;

    const depart = Math.min(x + ecart, largeur);
    const pointe = Math.min(depart + base / 2, largeur);
    const fin = Math.min(depart + base, largeur);

    morceaux.push(`L${depart.toFixed(1)} ${bord} L${pointe.toFixed(1)} ${longueur.toFixed(1)} L${fin.toFixed(1)} ${bord}`);
    x = fin;
  }

  morceaux.push(`L${largeur} ${bord} L${largeur} 0 L0 0 Z`);
  return morceaux.join(" ");
}

/** Chaîne de pics glaciaires : les sommets alternent creux et cimes. */
export function crete(
  { largeur = 1440, hauteur = 220, sommets = 11, cime = 60, creux = 150, graine = 3 } = {},
): string {
  const r = alea(graine);
  const pas = largeur / sommets;
  const y = (i: number) =>
    i % 2 === 0 ? creux - r() * 22 : cime + r() * 34;

  const morceaux = [`M0 ${hauteur}`, `L0 ${y(0).toFixed(1)}`];
  for (let i = 1; i <= sommets; i++) {
    morceaux.push(`L${(i * pas).toFixed(1)} ${y(i).toFixed(1)}`);
  }
  morceaux.push(`L${largeur} ${hauteur} Z`);
  return morceaux.join(" ");
}

/** Une branche de flocon, du centre vers le haut, avec ses ramifications.
 *  Répétée six fois à 60° d'écart, elle donne la symétrie d'un vrai cristal. */
export const BRANCHE_FLOCON = [
  "M100 100 V18",
  "M100 80 l-15 -15 M100 80 l15 -15",
  "M100 60 l-12 -12 M100 60 l12 -12",
  "M100 42 l-9 -9 M100 42 l9 -9",
  "M100 26 l-6 -6 M100 26 l6 -6",
].join(" ");

export const ANGLES_FLOCON = [0, 60, 120, 180, 240, 300];
