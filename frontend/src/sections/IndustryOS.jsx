import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";
import { HOMEPAGE, NAV, PAGE_CONFIGS } from "@/data/content";
import SectionHeader from "@/components/SectionHeader";
import Scene from "@/three/Scene";

/** Industry Operating Systems: pick an OS, its own 3D model and accent take over the stage. */
export default function IndustryOS() {
  const S = HOMEPAGE.solutions;
  const list = NAV.primary.find((x) => x.label === "Solutions").children
    .map((c) => PAGE_CONFIGS[c.to.split("/").pop()]).filter(Boolean);
  const [active, setActive] = useState(0);
  const cur = list[active];
  return (
    <section id="solutions" className="section" data-accent={cur.accent} data-testid="industry-os-section">
      <div className="container-x">
        <SectionHeader eyebrow={S.eyebrow} title={S.title} lead={S.lead} />
        <div className="mt-10 flex flex-wrap gap-2" role="tablist" aria-label="Industry operating systems">
          {list.map((c, i) => (
            <button
              key={c.slug}
              type="button"
              role="tab"
              aria-selected={active === i}
              data-accent={c.accent}
              onClick={() => setActive(i)}
              onMouseEnter={() => setActive(i)}
              className={`pill !py-2 !px-4 !text-sm transition-all ${active === i ? "!bg-accent !text-accent-ink !border-accent" : "hover:!border-accent/50"}`}
            >
              <span className={`h-2 w-2 rotate-45 rounded-[2px] ${active === i ? "bg-accent-ink" : "bg-accent"}`} />
              {c.eyebrow}
            </button>
          ))}
        </div>
        <div className="mt-8 card overflow-hidden grid lg:grid-cols-[1.15fr_1fr]">
          <Scene name={cur.scene} accent={cur.accent} className="h-[360px] sm:h-[460px] bg-accent/5" />
          <div className="p-8 lg:p-10 flex flex-col justify-center">
            <AnimatePresence mode="wait">
              <motion.div key={cur.slug} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.3 }}>
                <span className="eyebrow">{cur.name}</span>
                <h3 className="mt-4 h-display text-3xl sm:text-4xl text-ink">{cur.hero}</h3>
                <p className="mt-4 text-ink-soft leading-relaxed">{cur.subtitle}</p>
                <dl className="mt-7 grid grid-cols-2 gap-4">
                  {cur.stats.map((s) => (
                    <div key={s.l} className="card-soft p-4">
                      <dd className="font-display text-2xl font-semibold text-accent">{s.v}</dd>
                      <dt className="text-xs text-ink-muted mt-1">{s.l}</dt>
                    </div>
                  ))}
                </dl>
                <Link to={`/solutions/${cur.slug}`} className="mt-7 btn btn-solid">Explore {cur.name} <ArrowUpRight className="h-4 w-4" /></Link>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
}
