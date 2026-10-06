import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";
import { SERVICES } from "@/data/services";
import { rise } from "@/components/SectionHeader";
import Scene from "@/three/Scene";

export default function Services() {
  return (
    <div data-testid="services-index-page" data-accent="cobalt">
      <section className="relative overflow-hidden pt-28 lg:pt-32 pb-10">
        <div className="wash" />
        <div className="absolute inset-0 dotgrid opacity-60 pointer-events-none" />
        <div className="relative container-x">
          <motion.div {...rise()} className="eyebrow mb-5">Our Services</motion.div>
          <motion.h1 {...rise(0.05)} className="h-display text-[clamp(2.4rem,5.6vw,4.8rem)] text-ink max-w-4xl">
            What we build: <span className="text-accent-grad">end-to-end AI transformation.</span>
          </motion.h1>
          <motion.p {...rise(0.1)} className="mt-6 lead max-w-2xl">
            Strategy, data, engineering and marketing — everything needed to move enterprise AI from proof-of-concept to production.
          </motion.p>
        </div>
      </section>
      <section className="pb-24">
        <div className="container-x grid md:grid-cols-2 gap-6">
          {SERVICES.map((s, i) => (
            <motion.article key={s.slug} {...rise(0.06 * i)} data-accent={s.accent} className="card card-hover overflow-hidden flex flex-col" data-testid={`service-index-${s.slug}`}>
              <Scene name={s.scene} className="h-[260px] bg-accent/5" />
              <div className="p-7 flex flex-col flex-1">
                <span className="pill pill-accent self-start">{s.items.length} specialisations</span>
                <h2 className="mt-4 h-display text-3xl text-ink">{s.title}</h2>
                <p className="mt-2 font-medium text-accent">{s.subtitle}</p>
                <p className="mt-3 text-ink-soft leading-relaxed">{s.description}</p>
                <ul className="mt-5 flex flex-wrap gap-2">
                  {s.items.map((x) => <li key={x.id} className="pill">{x.title}</li>)}
                </ul>
                <Link to={`/services/${s.slug}`} className="mt-6 link-arrow">Explore {s.title} <ArrowUpRight className="h-4 w-4" /></Link>
              </div>
            </motion.article>
          ))}
        </div>
      </section>
    </div>
  );
}
