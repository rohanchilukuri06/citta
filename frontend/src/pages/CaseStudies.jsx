import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { CASESTUDIES } from "@/data/content";
import { rise } from "@/components/SectionHeader";
import Scene from "@/three/Scene";

const CASE_ACCENT = ["saffron", "coral", "cobalt"]; // the three bar rows in the 3D chart

export default function CaseStudies() {
  const C = CASESTUDIES;
  return (
    <div data-testid="case-studies-page" data-accent="jade">
      <section className="relative overflow-hidden pt-28 lg:pt-32 pb-12">
        <div className="wash" />
        <div className="absolute inset-0 dotgrid opacity-60 pointer-events-none" />
        <div className="relative container-x grid lg:grid-cols-[1.05fr_1fr] gap-10 items-center">
          <div>
            <motion.div {...rise()} className="eyebrow mb-5">{C.eyebrow}</motion.div>
            <motion.h1 {...rise(0.05)} className="h-display text-[clamp(2.4rem,5.6vw,4.8rem)] text-ink">{C.title}</motion.h1>
            <motion.p {...rise(0.1)} className="mt-6 lead max-w-xl">
              We engineer measurable outcomes. Here is the impact of deploying autonomous cognitive architectures in the real world.
            </motion.p>
          </div>
          <Scene name="growth" accent="cobalt" className="h-[340px] sm:h-[440px] rounded-[2rem]" />
        </div>
      </section>
      <section className="pb-20">
        <div className="container-x grid md:grid-cols-3 gap-5">
          {C.cases.map((c, i) => (
            <motion.article key={c.brand} {...rise(0.08 * i)} data-accent={CASE_ACCENT[i]} className="card card-hover p-8">
              <span className="pill pill-accent">{c.brand}</span>
              <div className="mt-6 font-display text-5xl font-semibold text-accent tabular-nums">{c.metric}</div>
              <div className="mt-2 font-medium text-ink">{c.label}</div>
              <p className="mt-4 text-sm text-ink-soft leading-relaxed">{c.desc}</p>
            </motion.article>
          ))}
        </div>
        <div className="container-x mt-10 text-center">
          <Link to="/contact" className="btn btn-solid">Build your success story <ArrowRight className="h-4 w-4" /></Link>
        </div>
      </section>
    </div>
  );
}
