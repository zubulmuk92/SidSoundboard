import Image from "next/image";
import { asset, liens, sections, site } from "@/lib/site";

export function Nav() {
  return (
    <header className="sticky top-0 z-40 border-b border-gel/10 bg-nuit/70 backdrop-blur-[14px]">
      <div className="conteneur flex items-center gap-7 py-2.5">
        <a href="#haut" className="flex items-center gap-3 font-display text-[23px] font-black uppercase">
          <Image src={asset("/sid.png")} alt="" width={677} height={369} className="h-auto w-20" priority />
          <span>{site.nom}</span>
        </a>

        <nav aria-label="Sections de la page" className="ml-auto hidden gap-6 lg:flex">
          {sections.map((s) => (
            <a
              key={s.href}
              href={s.href}
              className="font-mono text-[12.5px] tracking-[0.06em] text-brume transition-colors hover:text-gel"
            >
              {s.label}
            </a>
          ))}
        </nav>

        <a href={liens.depot} className="btn btn-gel ml-auto px-4 py-2 text-sm lg:ml-0" rel="noopener">
          GitHub
        </a>
      </div>
    </header>
  );
}
