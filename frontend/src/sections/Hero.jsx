import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { ArrowRight, ArrowUpRight } from "lucide-react";
import { HOMEPAGE } from "@/data/content";
import Scene from "@/three/Scene";

const enter = (delay) => ({
  initial: { opacity: 0, y: 18 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.7, delay, ease: [0.2, 0.7, 0.2, 1] },
});

export default function Hero() {
  const H = HOMEPAGE.hero;
  return (
    <section id="hero" data-testid="hero-section" data-accent="cobalt" className="relative overflow-hidden pt-28 lg:pt-32 pb-16 lg:pb-24">
      <div className="wash" />
      <div className="absolute inset-0 dotgrid opacity-70 pointer-events-none" />

      <div className="relative container-x grid lg:grid-cols-[1.05fr_1fr] gap-10 items-center">
        <div className="relative z-10">
          <motion.div {...enter(0.05)} className="eyebrow mb-6" data-testid="hero-eyebrow">{H.eyebrow}</motion.div>
          <h1 className="h-display text-[clamp(2.6rem,6.2vw,5.4rem)] text-ink" data-testid="hero-title">
            <motion.span {...enter(0.12)} className="block">{H.titleLead}</motion.span>
            <motion.span {...enter(0.22)} className="block text-accent-grad pb-2">{H.titleAccent}</motion.span>
          </h1>
          <motion.p {...enter(0.35)} className="mt-6 max-w-xl lead" data-testid="hero-subtitle">{H.subtitle}</motion.p>
          <motion.div {...enter(0.45)} className="mt-9 flex flex-wrap gap-3">
            <Link to={H.ctas[0].to} data-testid="hero-cta-primary" className="btn btn-solid">
              {H.ctas[0].label} <ArrowRight className="h-4 w-4" />
            </Link>
            <a href="#products" data-testid="hero-cta-secondary" className="btn btn-outline">
              {H.ctas[1].label} <ArrowUpRight className="h-4 w-4" />
            </a>
          </motion.div>
          <motion.ul {...enter(0.6)} className="mt-10 flex flex-wrap gap-2.5" data-testid="hero-tags">
            {H.tags.map((t) => <li key={t} className="pill"><span className="h-1.5 w-1.5 rounded-full bg-jade" />{t}</li>)}
          </motion.ul>
        </div>

        <motion.div
          initial={{ opacity: 0, scale: 0.94 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 1.1, delay: 0.15 }}
          className="relative"
        >
          <Scene
            name="neural"
            className="h-[380px] sm:h-[460px] lg:h-[580px] rounded-[2rem]"
            overlay={
              <>
                <span className="scene-label left-[6%] top-[16%]">Knowledge graph</span>
                <span className="scene-label right-[4%] top-[44%]">Autonomous agents</span>
                <span className="scene-label left-[14%] bottom-[12%]">Reasoning core</span>
              </>
            }
          />
        </motion.div>
      </div>
    </section>
  );
}
