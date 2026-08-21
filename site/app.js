/* ============================================================
   SidSoundboard — site vitrine
   Tout est synthétisé à la volée : aucun fichier audio à charger.
   Rien ne joue avant un clic ou une frappe de l'utilisateur.
   ============================================================ */
(function () {
  "use strict";

  var reduit = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ── 1. Révélations au scroll ─────────────────────────── */
  var aReveler = document.querySelectorAll(".reveal");
  if (reduit || !("IntersectionObserver" in window)) {
    Array.prototype.forEach.call(aReveler, function (el) { el.classList.add("is-in"); });
  } else {
    var obs = new IntersectionObserver(function (entrees) {
      entrees.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("is-in"); obs.unobserve(e.target); }
      });
    }, { threshold: 0.15, rootMargin: "0px 0px -8% 0px" });
    Array.prototype.forEach.call(aReveler, function (el, i) {
      el.style.transitionDelay = (Math.min(i, 6) * 45) + "ms";
      obs.observe(el);
    });
  }

  /* ── 2. Neige ambiante ────────────────────────────────── */
  var toile = document.getElementById("neige");
  if (toile && !reduit) {
    var ctx2d = toile.getContext("2d");
    var flocons = [];
    var L = 0, H = 0;

    function dimensionner() {
      L = toile.width = window.innerWidth;
      H = toile.height = window.innerHeight;
      var cible = Math.round(Math.min(90, L / 16));
      flocons = [];
      for (var i = 0; i < cible; i++) {
        flocons.push({
          x: Math.random() * L,
          y: Math.random() * H,
          r: 0.7 + Math.random() * 1.9,
          v: 0.25 + Math.random() * 0.75,
          d: Math.random() * Math.PI * 2
        });
      }
    }

    function tomber() {
      ctx2d.clearRect(0, 0, L, H);
      ctx2d.fillStyle = "#DCEEF6";
      for (var i = 0; i < flocons.length; i++) {
        var f = flocons[i];
        f.d += 0.008;
        f.y += f.v;
        f.x += Math.sin(f.d) * 0.4;
        if (f.y > H + 4) { f.y = -4; f.x = Math.random() * L; }
        ctx2d.globalAlpha = 0.25 + (f.r / 2.6) * 0.5;
        ctx2d.beginPath();
        ctx2d.arc(f.x, f.y, f.r, 0, Math.PI * 2);
        ctx2d.fill();
      }
      requestAnimationFrame(tomber);
    }

    dimensionner();
    window.addEventListener("resize", dimensionner);
    tomber();
  }

  /* ── 3. Moteur audio ──────────────────────────────────── */
  var AC = window.AudioContext || window.webkitAudioContext;
  var ac = null, master = null, analyseur = null, vivants = [];
  var board = document.querySelector(".board");
  var timerLive = null;

  function demarrer() {
    if (ac) { if (ac.state === "suspended") { ac.resume(); } return true; }
    if (!AC) { return false; }
    ac = new AC();
    master = ac.createGain();
    master.gain.value = 0.5;
    analyseur = ac.createAnalyser();
    analyseur.fftSize = 128;
    analyseur.smoothingTimeConstant = 0.72;
    master.connect(analyseur);
    analyseur.connect(ac.destination);
    return true;
  }

  function bruit(duree) {
    var n = Math.floor(ac.sampleRate * duree);
    var buf = ac.createBuffer(1, n, ac.sampleRate);
    var d = buf.getChannelData(0);
    for (var i = 0; i < n; i++) { d[i] = Math.random() * 2 - 1; }
    return buf;
  }

  // Enregistre une voix pour pouvoir la couper d'un coup (touche panique).
  function voix(gain, sources, fin) {
    var v = { gain: gain, sources: sources };
    vivants.push(v);
    setTimeout(function () {
      var i = vivants.indexOf(v);
      if (i > -1) { vivants.splice(i, 1); }
    }, fin * 1000 + 120);
    return v;
  }

  function couperTout() {
    if (!ac) { return; }
    var t = ac.currentTime;
    vivants.forEach(function (v) {
      try {
        v.gain.gain.cancelScheduledValues(t);
        v.gain.gain.setValueAtTime(v.gain.gain.value, t);
        v.gain.gain.linearRampToValueAtTime(0.0001, t + 0.03);
        v.sources.forEach(function (s) { try { s.stop(t + 0.05); } catch (e) {} });
      } catch (e) {}
    });
    vivants = [];
    marquerLive();
  }

  function marquerLive() {
    if (!board) { return; }
    if (vivants.length) {
      board.classList.add("is-live");
      clearTimeout(timerLive);
      timerLive = setTimeout(marquerLive, 400);
    } else {
      board.classList.remove("is-live");
    }
  }

  /* ── 4. Les six sons ──────────────────────────────────── */
  var sons = {
    // Glace qui cède : claquement large + résonance grave.
    crac: function (t) {
      var g = ac.createGain();
      g.gain.setValueAtTime(0.9, t);
      g.gain.exponentialRampToValueAtTime(0.001, t + 0.45);
      g.connect(master);

      var n = ac.createBufferSource();
      n.buffer = bruit(0.45);
      var hp = ac.createBiquadFilter();
      hp.type = "highpass";
      hp.frequency.setValueAtTime(2600, t);
      hp.frequency.exponentialRampToValueAtTime(420, t + 0.4);
      hp.Q.value = 3;
      n.connect(hp); hp.connect(g);

      var o = ac.createOscillator();
      o.type = "sine";
      o.frequency.setValueAtTime(180, t);
      o.frequency.exponentialRampToValueAtTime(42, t + 0.35);
      var og = ac.createGain();
      og.gain.setValueAtTime(0.7, t);
      og.gain.exponentialRampToValueAtTime(0.001, t + 0.35);
      o.connect(og); og.connect(g);

      n.start(t); n.stop(t + 0.45);
      o.start(t); o.stop(t + 0.4);
      return voix(g, [n, o], 0.45);
    },

    // Barrissement : dents de scie graves sous un filtre qui s'ouvre.
    mammouth: function (t) {
      var g = ac.createGain();
      g.gain.setValueAtTime(0.0001, t);
      g.gain.linearRampToValueAtTime(0.55, t + 0.12);
      g.gain.setValueAtTime(0.55, t + 0.6);
      g.gain.exponentialRampToValueAtTime(0.001, t + 1.05);
      var lp = ac.createBiquadFilter();
      lp.type = "lowpass"; lp.Q.value = 6;
      lp.frequency.setValueAtTime(300, t);
      lp.frequency.linearRampToValueAtTime(1300, t + 0.4);
      lp.frequency.linearRampToValueAtTime(500, t + 1);
      lp.connect(g); g.connect(master);

      var a = ac.createOscillator(), b = ac.createOscillator();
      a.type = "sawtooth"; b.type = "sawtooth";
      a.frequency.setValueAtTime(88, t);
      a.frequency.linearRampToValueAtTime(112, t + 0.25);
      a.frequency.linearRampToValueAtTime(96, t + 1);
      b.frequency.setValueAtTime(132, t);
      b.frequency.linearRampToValueAtTime(168, t + 0.25);
      b.frequency.linearRampToValueAtTime(144, t + 1);
      var bg = ac.createGain(); bg.gain.value = 0.4;
      a.connect(lp); b.connect(bg); bg.connect(lp);

      a.start(t); a.stop(t + 1.05);
      b.start(t); b.stop(t + 1.05);
      return voix(g, [a, b], 1.05);
    },

    // Corne de brume : deux scies désaccordées dans un passe-bande.
    corne: function (t) {
      var g = ac.createGain();
      g.gain.setValueAtTime(0.0001, t);
      g.gain.linearRampToValueAtTime(0.42, t + 0.04);
      g.gain.setValueAtTime(0.42, t + 0.5);
      g.gain.exponentialRampToValueAtTime(0.001, t + 0.72);
      var bp = ac.createBiquadFilter();
      bp.type = "bandpass"; bp.frequency.value = 1150; bp.Q.value = 3.5;
      bp.connect(g); g.connect(master);

      var a = ac.createOscillator(), b = ac.createOscillator();
      a.type = "sawtooth"; b.type = "sawtooth";
      a.frequency.value = 415; b.frequency.value = 421;
      a.connect(bp); b.connect(bp);
      a.start(t); a.stop(t + 0.72);
      b.start(t); b.stop(t + 0.72);
      return voix(g, [a, b], 0.72);
    },

    // « Bleh » : une scie sous deux formants qui glissent.
    bleh: function (t) {
      var g = ac.createGain();
      g.gain.setValueAtTime(0.0001, t);
      g.gain.linearRampToValueAtTime(0.6, t + 0.05);
      g.gain.setValueAtTime(0.6, t + 0.3);
      g.gain.exponentialRampToValueAtTime(0.001, t + 0.55);
      g.connect(master);

      var o = ac.createOscillator();
      o.type = "sawtooth";
      o.frequency.setValueAtTime(196, t);
      o.frequency.linearRampToValueAtTime(150, t + 0.5);

      [[720, 500, 1], [1750, 1150, 0.7]].forEach(function (f) {
        var bp = ac.createBiquadFilter();
        bp.type = "bandpass"; bp.Q.value = 9;
        bp.frequency.setValueAtTime(f[0], t);
        bp.frequency.linearRampToValueAtTime(f[1], t + 0.5);
        var fg = ac.createGain(); fg.gain.value = f[2];
        o.connect(bp); bp.connect(fg); fg.connect(g);
      });

      o.start(t); o.stop(t + 0.55);
      return voix(g, [o], 0.55);
    },

    // Le gland : un « pop » sec qui chute d'une octave et demie.
    gland: function (t) {
      var g = ac.createGain();
      g.gain.setValueAtTime(0.85, t);
      g.gain.exponentialRampToValueAtTime(0.001, t + 0.18);
      g.connect(master);

      var o = ac.createOscillator();
      o.type = "sine";
      o.frequency.setValueAtTime(940, t);
      o.frequency.exponentialRampToValueAtTime(180, t + 0.15);
      o.connect(g);

      var n = ac.createBufferSource();
      n.buffer = bruit(0.05);
      var ng = ac.createGain();
      ng.gain.setValueAtTime(0.35, t);
      ng.gain.exponentialRampToValueAtTime(0.001, t + 0.05);
      n.connect(ng); ng.connect(g);

      o.start(t); o.stop(t + 0.2);
      n.start(t); n.stop(t + 0.05);
      return voix(g, [o, n], 0.2);
    },

    // Blizzard : souffle filtré, balayage montant puis descendant.
    blizzard: function (t) {
      var g = ac.createGain();
      g.gain.setValueAtTime(0.0001, t);
      g.gain.linearRampToValueAtTime(0.5, t + 0.4);
      g.gain.linearRampToValueAtTime(0.0001, t + 1.5);
      g.connect(master);

      var n = ac.createBufferSource();
      n.buffer = bruit(1.6);
      var bp = ac.createBiquadFilter();
      bp.type = "bandpass"; bp.Q.value = 4.5;
      bp.frequency.setValueAtTime(320, t);
      bp.frequency.exponentialRampToValueAtTime(3800, t + 0.8);
      bp.frequency.exponentialRampToValueAtTime(400, t + 1.5);
      n.connect(bp); bp.connect(g);

      n.start(t); n.stop(t + 1.5);
      return voix(g, [n], 1.5);
    }
  };

  /* ── 5. Les dalles ────────────────────────────────────── */
  var pads = Array.prototype.slice.call(document.querySelectorAll(".pad"));

  function jouer(pad) {
    if (!pad || !demarrer()) { return; }
    var f = sons[pad.dataset.son];
    if (!f) { return; }
    f(ac.currentTime + 0.001);
    marquerLive();

    pad.classList.remove("is-hit");
    void pad.offsetWidth;          // relance la transition de la fissure
    pad.classList.add("is-hit");
    setTimeout(function () { pad.classList.remove("is-hit"); }, 90);
  }

  pads.forEach(function (pad) {
    pad.addEventListener("click", function () { jouer(pad); });
  });

  var parTouche = {};
  pads.forEach(function (pad) { parTouche[pad.dataset.touche] = pad; });

  document.addEventListener("keydown", function (e) {
    if (e.metaKey || e.ctrlKey || e.altKey || e.repeat) { return; }

    var actif = document.activeElement;
    var surControle = actif && /^(BUTTON|A|INPUT|TEXTAREA|SELECT)$/.test(actif.tagName);

    if (e.key === "Escape" || (e.key === " " && !surControle)) {
      e.preventDefault();
      couperTout();
      return;
    }

    var pad = parTouche[String(e.key).toLowerCase()];
    if (pad && !surControle) {
      e.preventDefault();
      jouer(pad);
    }
  });

  var boutonPanique = document.getElementById("panique");
  if (boutonPanique) { boutonPanique.addEventListener("click", couperTout); }

  /* ── 6. Waveform : gelée au repos, vivante à la lecture ── */
  var viz = document.getElementById("viz");
  if (viz) {
    var vc = viz.getContext("2d");
    var barres = 48;
    var gelee = [];
    for (var i = 0; i < barres; i++) {
      // Profil figé, symétrique : une carotte de glace vue de côté.
      var p = i / (barres - 1);
      gelee.push(0.18 + Math.abs(Math.sin(p * 7.5)) * 0.14 + Math.abs(Math.sin(p * 2.1)) * 0.1);
    }

    function calerViz() {
      var r = viz.getBoundingClientRect();
      if (r.width) {
        viz.width = Math.round(r.width);
        viz.height = Math.round(r.height);
      }
    }

    function dessinerViz() {
      var w = viz.width, h = viz.height;
      vc.clearRect(0, 0, w, h);

      var data = null;
      if (analyseur && vivants.length) {
        data = new Uint8Array(analyseur.frequencyBinCount);
        analyseur.getByteFrequencyData(data);
      }

      var pas = w / barres;
      for (var i = 0; i < barres; i++) {
        var v = gelee[i];
        if (data) {
          var idx = Math.floor(i / barres * data.length);
          v = Math.max(gelee[i], data[idx] / 255);
        }
        var haut = Math.max(3, v * h * 0.92);
        var x = i * pas;
        var y = (h - haut) / 2;
        vc.fillStyle = data ? "rgba(255, 138, 61, " + (0.4 + v * 0.6) + ")"
                            : "rgba(127, 231, 242, " + (0.18 + v * 0.5) + ")";
        vc.fillRect(x + 1, y, Math.max(2, pas - 3), haut);
      }
      requestAnimationFrame(dessinerViz);
    }

    function geler() {
      // Une seule passe : la waveform reste figée dans la glace.
      var w0 = viz.width, h0 = viz.height, pas0 = w0 / barres;
      vc.clearRect(0, 0, w0, h0);
      for (var j = 0; j < barres; j++) {
        var ht = Math.max(3, gelee[j] * h0 * 0.92);
        vc.fillStyle = "rgba(127, 231, 242, " + (0.18 + gelee[j] * 0.5) + ")";
        vc.fillRect(j * pas0 + 1, (h0 - ht) / 2, Math.max(2, pas0 - 3), ht);
      }
    }

    calerViz();
    window.addEventListener("resize", function () {
      calerViz();
      if (reduit) { geler(); }
    });

    if (reduit) { geler(); } else { dessinerViz(); }
  }
})();
