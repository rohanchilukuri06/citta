import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";
import { HOMEPAGE, WHATSAPP, INFLUENCER } from "@/data/content";
import SectionHeader, { rise } from "@/components/SectionHeader";
import Scene from "@/three/Scene";

const CONFIG = { "/products/whatsapp-marketing": WHATSAPP, "/products/influencer-marketing": INFLUENCER };

export default function ProductsGrid() {
  const P = HOMEPAGE.products;
  return (
    <section id="products" className="section" data-testid="products-section">
      <div className="container-x">
        <SectionHeader eyebrow={P.eyebrow} title={P.title} lead={P.lead} />
        <div className="mt-14 grid lg:grid-cols-2 gap-6">
          {P.items.map((it, i) => {
            const cfg = CONFIG[it.to];
            return (
              <motion.article key={it.to} {...rise(0.08 * i)} data-accent={cfg.accent} className="card card-hover overflow-hidden flex flex-col">
                <Scene name={cfg.scene} className="h-[300px] sm:h-[340px] bg-accent/5" />
                <div className="p-7 flex flex-col flex-1">
                  <div className="flex items-center justify-between gap-3">
                    <span className="pill pill-accent">{cfg.eyebrow}</span>
                    <span className="font-mono text-xs text-ink-muted">{it.n}</span>
                  </div>
                  <h3 className="mt-4 h-display text-3xl text-ink">{cfg.name}</h3>
                  <p className="mt-3 text-ink-soft leading-relaxed">{it.desc}</p>
                  <dl className="mt-6 grid grid-cols-4 gap-3 border-t border-line/10 pt-5">
                    {cfg.stats.map((s) => (
                      <div key={s.l}>
                        <dt className="text-[11px] text-ink-muted leading-tight">{s.l}</dt>
                        <dd className="font-display text-lg font-semibold text-accent mt-1">{s.v}</dd>
                      </div>
                    ))}
                  </dl>
                  <Link to={it.to} className="mt-6 link-arrow" data-testid={`product-link-${cfg.slug}`}>
                    Explore {cfg.name} <ArrowUpRight className="h-4 w-4" />
                  </Link>
                </div>
              </motion.article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
