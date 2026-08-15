/** Bord de banquise entre deux sections.
 *
 *  Le tracé couvre exactement les 1440 unités du viewBox — sans quoi la
 *  fracture s'arrête en cours de route et le raccord redevient rectiligne
 *  sur la fin. `preserveAspectRatio="none"` l'étire ensuite à la largeur
 *  réelle de l'écran, quelle qu'elle soit. */
export function BordGlace({ className = "" }: { className?: string }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 1440 90"
      preserveAspectRatio="none"
      className={`absolute inset-x-0 -bottom-px z-3 h-[clamp(38px,4.5vw,64px)] w-full ${className}`}
    >
      <path d="M0 90V62l196-18 176 14 188-22 184 18 194-14 188 18 172-16 142 14v34z" />
    </svg>
  );
}
