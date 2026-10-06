import { motion } from "framer-motion";
import { HOMEPAGE } from "@/data/content";
import SectionHeader, { rise } from "@/components/SectionHeader";

// Client logo files in /public/assets/clients, matched by a keyword in the client's name
const LOGO_FILES = {
  aurum: "Aurum_street-DCJLaXXK.png",
  devarasa: "Devarasa-FbIBTtGK.png",
  green: "Green_Leaves-DGqJH5ZS.png",
  mahas: "Nails_by_Mahas_logo-D9n-iPR_.png",
  olive: "Olive_Mithai_Logo_Green_1_Large-B_tXP-Gq.png",
  jawa: "SRK_jawa-BwItJrVI.png",
  svs: "SVS_logo-HM8dvI6k.png",
  shilpa: "Shilpa_botanica_logo-CwuXVVGb.png",
  vegasri: "Vegasri-D-4mxSCL.png",
  fixity: "cropped-Fixity-EDX-Website-Logo-Bs77BqaI.jpeg",
};
const logoFor = (name) => {
  const key = Object.keys(LOGO_FILES).find((k) => name.toLowerCase().includes(k));
  return key ? `/assets/clients/${LOGO_FILES[key]}` : null;
};

function LogoChip({ name }) {
  const src = logoFor(name);
  return (
    <div className="logo-chip h-20 w-44 shrink-0 grid place-items-center px-5" title={name}>
      {src ? <img src={src} alt={name} loading="lazy" className="max-h-12 max-w-full object-contain" />
        : <span className="font-display font-semibold text-[#18282A] text-sm text-center">{name}</span>}
    </div>
  );
}

export default function Fueling() {
  const F = HOMEPAGE.fueling;
  const logos = F.logos;
  return (
    <section className="section overflow-hidden" data-accent="jade" data-testid="fueling-section">
      <div className="container-x grid lg:grid-cols-[1.3fr_1fr] gap-10 items-end">
        <SectionHeader eyebrow={F.eyebrow} title={F.title.replace("\n", " ")} lead={F.desc} />
        <div className="grid grid-cols-2 gap-4">
          {F.stats.map((s, i) => (
            <motion.div key={s.l} {...rise(0.08 * i)} className="card p-6">
              <div className="font-display text-5xl font-semibold text-accent tabular-nums">{s.v}</div>
              <div className="mt-2 text-sm text-ink-soft">{s.l}</div>
            </motion.div>
          ))}
        </div>
      </div>
      <div className="mt-14 marquee-mask">
        <div className="flex gap-4 w-max animate-marquee hover:[animation-play-state:paused]">
          {[...logos, ...logos].map((n, i) => <LogoChip key={`${n}-${i}`} name={n} />)}
        </div>
      </div>
    </section>
  );
}
