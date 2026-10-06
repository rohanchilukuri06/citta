import { motion } from "framer-motion";
import { HOMEPAGE } from "@/data/content";
import { rise } from "@/components/SectionHeader";

export default function Positioning() {
  const P = HOMEPAGE.positioning;
  const [first, second] = P.title.split(/\s{2,}/);
  return (
    <section className="section" data-accent="cobalt" data-testid="positioning-section">
      <div className="container-x">
        <motion.div {...rise()} className="eyebrow mb-6">{P.eyebrow}</motion.div>
        <motion.h2 {...rise(0.05)} className="h-display text-[clamp(2.4rem,6vw,5rem)] text-ink max-w-5xl">
          {first} <span className="text-accent-grad">{second}</span>
        </motion.h2>
        <motion.p {...rise(0.1)} className="mt-6 lead max-w-3xl">{P.lead}</motion.p>
        <div className="mt-14 grid md:grid-cols-3 gap-5">
          {P.pillars.map((pl, i) => (
            <motion.article key={pl.n} {...rise(0.08 * i)} className="card card-hover p-7 relative overflow-hidden">
              <span className="absolute -right-2 -top-6 font-display text-[7rem] font-bold text-accent/10 leading-none select-none">{pl.n}</span>
              <div className="relative">
                <div className="font-mono text-xs text-accent mb-3">{pl.n}</div>
                <h3 className="font-display text-xl font-semibold text-ink">{pl.title}</h3>
                <p className="mt-3 text-sm leading-relaxed text-ink-soft">{pl.desc}</p>
              </div>
            </motion.article>
          ))}
        </div>
      </div>
    </section>
  );
}
