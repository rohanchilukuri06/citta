import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";
import { HOMEPAGE } from "@/data/content";
import SectionHeader, { rise } from "@/components/SectionHeader";
import Scene from "@/three/Scene";

const CASE_ACCENT = ["saffron", "coral", "cobalt"]; // same colours as the three bar rows in the 3D chart

export default function Results() {
  const R = HOMEPAGE.results;
  return (
    <section className="section section-alt" data-accent="jade" data-testid="results-section">
      <div className="container-x grid lg:grid-cols-[1fr_1.1fr] gap-14 items-center">
        <div>
          <SectionHeader eyebrow={R.eyebrow} title={R.title} lead={R.lead} />
          <Scene name="growth" accent="cobalt" className="mt-8 h-[320px] sm:h-[380px] rounded-[2rem] card" />
        </div>
        <div className="space-y-4">
          {R.cases.map((c, i) => (
            <motion.article key={c.brand} {...rise(0.08 * i)} data-accent={CASE_ACCENT[i]} className="card card-hover p-6 sm:p-7 flex gap-6 items-center">
              <div className="min-w-[8.5rem]">
                <div className="font-display text-3xl sm:text-4xl font-semibold text-accent tabular-nums">{c.metric}</div>
                <div className="text-xs text-ink-muted mt-1">{c.label}</div>
              </div>
              <div className="border-l border-line/10 pl-6">
                <h3 className="font-display text-lg font-semibold text-ink">{c.brand}</h3>
                <p className="mt-1.5 text-sm text-ink-soft leading-relaxed">{c.desc}</p>
              </div>
            </motion.article>
          ))}
          <Link to="/case-studies" className="link-arrow pt-2">Read case studies <ArrowUpRight className="h-4 w-4" /></Link>
        </div>
      </div>
    </section>
  );
}
