import { useState } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";
import { HOMEPAGE } from "@/data/content";
import { SERVICE_BY_SLUG } from "@/data/services";
import SectionHeader, { rise } from "@/components/SectionHeader";
import Scene from "@/three/Scene";

/** Services: one 3D canvas whose model follows the service being explored (pipeline, agents, roadmap, funnel). */
export default function ServicesRow() {
  const S = HOMEPAGE.services;
  const items = S.items.map((it) => ({ ...it, svc: SERVICE_BY_SLUG[it.to.replace("/services/", "")] }));
  const [active, setActive] = useState(0);
  const cur = items[active].svc;
  return (
    <section className="section section-alt" data-accent={cur.accent} data-testid="services-section">
      <div className="container-x">
        <div className="flex flex-wrap items-end justify-between gap-6">
          <SectionHeader eyebrow={S.eyebrow} title={S.title} lead={S.lead} />
          <Link to={S.cta.to} className="btn btn-outline">{S.cta.label} <ArrowUpRight className="h-4 w-4" /></Link>
        </div>
        <div className="mt-12 grid lg:grid-cols-[1fr_1.1fr] gap-8 items-stretch">
          <ul className="space-y-3" role="tablist" aria-label="Services">
            {items.map((it, i) => (
              <motion.li key={it.to} {...rise(0.05 * i)}>
                <button
                  type="button"
                  role="tab"
                  aria-selected={active === i}
                  data-accent={it.svc.accent}
                  onMouseEnter={() => setActive(i)}
                  onFocus={() => setActive(i)}
                  onClick={() => setActive(i)}
                  className={`w-full text-left card p-5 transition-all ${active === i ? "!border-accent/60 shadow-[var(--shadow-lift)]" : "opacity-80 hover:opacity-100"}`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-display text-xl font-semibold text-ink">{it.title}</span>
                    <span className={`h-2.5 w-2.5 rotate-45 rounded-[3px] ${active === i ? "bg-accent" : "bg-line/20"}`} />
                  </div>
                  <span className="block mt-1 text-sm font-medium text-accent">{it.sub}</span>
                  {active === i && <span className="block mt-2 text-sm leading-relaxed text-ink-soft">{it.desc}</span>}
                </button>
              </motion.li>
            ))}
          </ul>
          <div className="card overflow-hidden flex flex-col">
            <Scene name={cur.scene} accent={cur.accent} className="h-[340px] sm:h-[400px] flex-1 bg-accent/5" />
            <div className="p-6 border-t border-line/10">
              <div className="flex flex-wrap gap-2">
                {cur.items.slice(0, 4).map((x) => <span key={x.id} className="pill">{x.title}</span>)}
                {cur.items.length > 4 && <span className="pill">+{cur.items.length - 4} more</span>}
              </div>
              <Link to={items[active].to} className="mt-5 link-arrow">Explore {items[active].title} <ArrowUpRight className="h-4 w-4" /></Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
