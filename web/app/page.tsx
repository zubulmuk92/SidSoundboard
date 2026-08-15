import { AppelFinal } from "@/components/AppelFinal";
import { Editeur } from "@/components/Editeur";
import { Hero } from "@/components/Hero";
import { Horizon } from "@/components/Horizon";
import { Installation } from "@/components/Installation";
import { Moteur } from "@/components/Moteur";
import { Nav } from "@/components/Nav";
import { Neige } from "@/components/Neige";
import { PiedDePage } from "@/components/PiedDePage";
import { Revelations } from "@/components/Revelations";

export default function Page() {
  return (
    <>
      <a
        href="#contenu"
        className="btn btn-azur sr-only focus:not-sr-only focus:absolute focus:top-3 focus:left-3 focus:z-50"
      >
        Aller au contenu
      </a>

      <Neige />
      <Revelations />
      <Nav />

      <main id="contenu">
        <Hero />
        <Moteur />
        <Horizon />
        <Editeur />
        <Installation />
        <AppelFinal />
      </main>

      <PiedDePage />
    </>
  );
}
