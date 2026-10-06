import { motion } from "framer-motion";
import { Workflow, ShieldCheck, TrendingUp } from "lucide-react";
import { HOMEPAGE } from "@/data/content";
import SectionHeader, { rise } from "@/components/SectionHeader";

const ICONS = [Workflow, ShieldCheck, TrendingUp];
const ACCENT = ["cobalt", "jade", "saffron"];

export default function Why() {
  const W = HOMEPAGE.why;
  return (
    <section className="section section-alt" data-accent="cobalt" data-testid="why-section">
      <div className="container-x">
        <SectionHeader eyebrow={W.eyebrow} title={W.title} sub={W.sub} align="center" />
        <div className="mt-14 grid md:grid-cols-3 gap-5">
          {W.items.map((it, i) => {
            const Icon = ICONS[i];
            return (
              <motion.article key={it.title} {...rise(0.08 * i)} data-accent={ACCENT[i]} className="card card-hover p-8">
                <div className="icon-tile h-12 w-12 mb-6"><Icon className="h-5 w-5" /></div>
                <h3 className="font-display text-xl font-semibold text-ink">{it.title}</h3>
                <p className="mt-3 text-sm leading-relaxed text-ink-soft">{it.desc}</p>
              </motion.article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
