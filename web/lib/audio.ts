/** Moteur audio des dalles de démonstration.
 *
 *  Tout est synthétisé à la volée (oscillateurs, bruit filtré, formants) :
 *  aucun fichier audio n'est téléchargé, et le contexte n'est créé qu'au
 *  premier geste de l'utilisateur — jamais au chargement de la page.
 */

type Voix = { gain: GainNode; sources: AudioScheduledSourceNode[] };

export type NomSon = "crac" | "mammouth" | "corne" | "bleh" | "gland" | "blizzard";

export type Dalle = { son: NomSon; touche: string; nom: string };

export const DALLES: readonly Dalle[] = [
  { son: "crac", touche: "a", nom: "Craquement" },
  { son: "mammouth", touche: "z", nom: "Mammouth" },
  { son: "corne", touche: "e", nom: "Corne de brume" },
  { son: "bleh", touche: "r", nom: "Bleh" },
  { son: "gland", touche: "t", nom: "Le gland" },
  { son: "blizzard", touche: "y", nom: "Blizzard" },
];

let ac: AudioContext | null = null;
let master: GainNode | null = null;
let analyseur: AnalyserNode | null = null;
let vivants: Voix[] = [];

/** Crée (ou réveille) le contexte audio. À n'appeler que depuis un geste utilisateur. */
function demarrer(): boolean {
  if (ac) {
    if (ac.state === "suspended") void ac.resume();
    return true;
  }
  const Ctor = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!Ctor) return false;

  ac = new Ctor();
  master = ac.createGain();
  master.gain.value = 0.5;
  analyseur = ac.createAnalyser();
  analyseur.fftSize = 128;
  analyseur.smoothingTimeConstant = 0.72;
  master.connect(analyseur);
  analyseur.connect(ac.destination);
  return true;
}

function bruit(ctx: AudioContext, duree: number): AudioBuffer {
  const n = Math.floor(ctx.sampleRate * duree);
  const buf = ctx.createBuffer(1, n, ctx.sampleRate);
  const d = buf.getChannelData(0);
  for (let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1;
  return buf;
}

/** Garde une trace de la voix pour pouvoir la couper d'un coup (touche panique). */
function suivre(gain: GainNode, sources: AudioScheduledSourceNode[], fin: number) {
  const v: Voix = { gain, sources };
  vivants.push(v);
  window.setTimeout(() => {
    const i = vivants.indexOf(v);
    if (i > -1) vivants.splice(i, 1);
  }, fin * 1000 + 120);
}

const synthes: Record<NomSon, (ctx: AudioContext, sortie: GainNode, t: number) => void> = {
  // Glace qui cède : claquement large qui descend, plus une résonance grave.
  crac(ctx, sortie, t) {
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.9, t);
    g.gain.exponentialRampToValueAtTime(0.001, t + 0.45);
    g.connect(sortie);

    const n = ctx.createBufferSource();
    n.buffer = bruit(ctx, 0.45);
    const hp = ctx.createBiquadFilter();
    hp.type = "highpass";
    hp.frequency.setValueAtTime(2600, t);
    hp.frequency.exponentialRampToValueAtTime(420, t + 0.4);
    hp.Q.value = 3;
    n.connect(hp);
    hp.connect(g);

    const o = ctx.createOscillator();
    o.type = "sine";
    o.frequency.setValueAtTime(180, t);
    o.frequency.exponentialRampToValueAtTime(42, t + 0.35);
    const og = ctx.createGain();
    og.gain.setValueAtTime(0.7, t);
    og.gain.exponentialRampToValueAtTime(0.001, t + 0.35);
    o.connect(og);
    og.connect(g);

    n.start(t);
    n.stop(t + 0.45);
    o.start(t);
    o.stop(t + 0.4);
    suivre(g, [n, o], 0.45);
  },

  // Barrissement : deux dents de scie graves sous un filtre qui s'ouvre.
  mammouth(ctx, sortie, t) {
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.linearRampToValueAtTime(0.55, t + 0.12);
    g.gain.setValueAtTime(0.55, t + 0.6);
    g.gain.exponentialRampToValueAtTime(0.001, t + 1.05);
    g.connect(sortie);

    const lp = ctx.createBiquadFilter();
    lp.type = "lowpass";
    lp.Q.value = 6;
    lp.frequency.setValueAtTime(300, t);
    lp.frequency.linearRampToValueAtTime(1300, t + 0.4);
    lp.frequency.linearRampToValueAtTime(500, t + 1);
    lp.connect(g);

    const a = ctx.createOscillator();
    const b = ctx.createOscillator();
    a.type = "sawtooth";
    b.type = "sawtooth";
    a.frequency.setValueAtTime(88, t);
    a.frequency.linearRampToValueAtTime(112, t + 0.25);
    a.frequency.linearRampToValueAtTime(96, t + 1);
    b.frequency.setValueAtTime(132, t);
    b.frequency.linearRampToValueAtTime(168, t + 0.25);
    b.frequency.linearRampToValueAtTime(144, t + 1);
    const bg = ctx.createGain();
    bg.gain.value = 0.4;
    a.connect(lp);
    b.connect(bg);
    bg.connect(lp);

    a.start(t);
    a.stop(t + 1.05);
    b.start(t);
    b.stop(t + 1.05);
    suivre(g, [a, b], 1.05);
  },

  // Corne de brume : deux scies désaccordées dans un passe-bande étroit.
  corne(ctx, sortie, t) {
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.linearRampToValueAtTime(0.42, t + 0.04);
    g.gain.setValueAtTime(0.42, t + 0.5);
    g.gain.exponentialRampToValueAtTime(0.001, t + 0.72);
    g.connect(sortie);

    const bp = ctx.createBiquadFilter();
    bp.type = "bandpass";
    bp.frequency.value = 1150;
    bp.Q.value = 3.5;
    bp.connect(g);

    const a = ctx.createOscillator();
    const b = ctx.createOscillator();
    a.type = "sawtooth";
    b.type = "sawtooth";
    a.frequency.value = 415;
    b.frequency.value = 421;
    a.connect(bp);
    b.connect(bp);

    a.start(t);
    a.stop(t + 0.72);
    b.start(t);
    b.stop(t + 0.72);
    suivre(g, [a, b], 0.72);
  },

  // « Bleh » : une scie sous deux formants qui glissent de « è » vers « a ».
  bleh(ctx, sortie, t) {
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.linearRampToValueAtTime(0.6, t + 0.05);
    g.gain.setValueAtTime(0.6, t + 0.3);
    g.gain.exponentialRampToValueAtTime(0.001, t + 0.55);
    g.connect(sortie);

    const o = ctx.createOscillator();
    o.type = "sawtooth";
    o.frequency.setValueAtTime(196, t);
    o.frequency.linearRampToValueAtTime(150, t + 0.5);

    ([
      [720, 500, 1],
      [1750, 1150, 0.7],
    ] as const).forEach(([depart, arrivee, niveau]) => {
      const bp = ctx.createBiquadFilter();
      bp.type = "bandpass";
      bp.Q.value = 9;
      bp.frequency.setValueAtTime(depart, t);
      bp.frequency.linearRampToValueAtTime(arrivee, t + 0.5);
      const fg = ctx.createGain();
      fg.gain.value = niveau;
      o.connect(bp);
      bp.connect(fg);
      fg.connect(g);
    });

    o.start(t);
    o.stop(t + 0.55);
    suivre(g, [o], 0.55);
  },

  // Le gland : un « pop » sec qui chute d'une octave et demie.
  gland(ctx, sortie, t) {
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.85, t);
    g.gain.exponentialRampToValueAtTime(0.001, t + 0.18);
    g.connect(sortie);

    const o = ctx.createOscillator();
    o.type = "sine";
    o.frequency.setValueAtTime(940, t);
    o.frequency.exponentialRampToValueAtTime(180, t + 0.15);
    o.connect(g);

    const n = ctx.createBufferSource();
    n.buffer = bruit(ctx, 0.05);
    const ng = ctx.createGain();
    ng.gain.setValueAtTime(0.35, t);
    ng.gain.exponentialRampToValueAtTime(0.001, t + 0.05);
    n.connect(ng);
    ng.connect(g);

    o.start(t);
    o.stop(t + 0.2);
    n.start(t);
    n.stop(t + 0.05);
    suivre(g, [o, n], 0.2);
  },

  // Blizzard : souffle filtré, balayage montant puis descendant.
  blizzard(ctx, sortie, t) {
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.linearRampToValueAtTime(0.5, t + 0.4);
    g.gain.linearRampToValueAtTime(0.0001, t + 1.5);
    g.connect(sortie);

    const n = ctx.createBufferSource();
    n.buffer = bruit(ctx, 1.6);
    const bp = ctx.createBiquadFilter();
    bp.type = "bandpass";
    bp.Q.value = 4.5;
    bp.frequency.setValueAtTime(320, t);
    bp.frequency.exponentialRampToValueAtTime(3800, t + 0.8);
    bp.frequency.exponentialRampToValueAtTime(400, t + 1.5);
    n.connect(bp);
    bp.connect(g);

    n.start(t);
    n.stop(t + 1.5);
    suivre(g, [n], 1.5);
  },
};

export function jouer(nom: NomSon): void {
  if (!demarrer() || !ac || !master) return;
  synthes[nom](ac, master, ac.currentTime + 0.001);
}

/** Touche panique : coupe toutes les voix en 30 ms. */
export function couperTout(): void {
  if (!ac) return;
  const t = ac.currentTime;
  for (const v of vivants) {
    try {
      v.gain.gain.cancelScheduledValues(t);
      v.gain.gain.setValueAtTime(v.gain.gain.value, t);
      v.gain.gain.linearRampToValueAtTime(0.0001, t + 0.03);
      for (const s of v.sources) {
        try {
          s.stop(t + 0.05);
        } catch {
          /* déjà arrêtée */
        }
      }
    } catch {
      /* voix déjà libérée */
    }
  }
  vivants = [];
}

export function joue(): boolean {
  return vivants.length > 0;
}

/** Spectre courant, ou null si rien ne joue. */
export function spectre(): Uint8Array | null {
  if (!analyseur || vivants.length === 0) return null;
  const data = new Uint8Array(analyseur.frequencyBinCount);
  analyseur.getByteFrequencyData(data);
  return data;
}
