// Product / solution page sections — one template driven by the page config in data/content.js.
// Every page wrapper sets data-accent, so all colours here follow that product's accent in both themes.
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { ArrowLeft, ArrowRight, ArrowUpRight, Check, UserRound } from "lucide-react";
import CapabilityIcon from "@/components/CapabilityIcon";
import SectionHeader, { rise } from "@/components/SectionHeader";
import Scene from "@/three/Scene";

export function PSHero({ cfg, backTo, backLabel }) {
  return (
    <section className="relative overflow-hidden pt-28 lg:pt-32 pb-16" data-testid="ps-hero">
      <div className="wash" />
      <div className="absolute inset-0 dotgrid opacity-60 pointer-events-none" />
      <div className="relative container-x">
        <Link to={backTo} className="inline-flex items-center gap-2 text-sm text-ink-muted hover:text-accent mb-8 group" data-testid="ps-back">
          <ArrowLeft className="h-4 w-4 group-hover:-translate-x-0.5 transition-transform" /> {backLabel}
        </Link>
        <div className="grid lg:grid-cols-[1fr_1.05fr] gap-10 items-center">
          <div>
            <motion.div {...rise()} className="eyebrow mb-5">{cfg.eyebrow}</motion.div>
            <motion.h1 {...rise(0.05)} className="h-display text-[clamp(2.4rem,5.4vw,4.6rem)] text-ink" data-testid="ps-title">
              {cfg.name}
            </motion.h1>
            <motion.p {...rise(0.1)} className="mt-4 font-display text-2xl text-accent">{cfg.hero}</motion.p>
            <motion.p {...rise(0.15)} className="mt-5 lead max-w-xl">{cfg.subtitle}</motion.p>
            <motion.div {...rise(0.2)} className="mt-8 flex flex-wrap gap-3">
              <Link to="/contact" className="btn btn-solid">Talk to our team <ArrowRight className="h-4 w-4" /></Link>
              <a href="#capabilities" className="btn btn-outline">See capabilities <ArrowUpRight className="h-4 w-4" /></a>
            </motion.div>
          </div>
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 1, delay: 0.1 }}>
            <Scene name={cfg.scene} className="h-[360px] sm:h-[440px] lg:h-[500px] rounded-[2rem] card bg-accent/5" />
          </motion.div>
        </div>
        <motion.dl {...rise(0.25)} className="mt-12 grid grid-cols-2 lg:grid-cols-4 gap-4" data-testid="ps-stats">
          {cfg.stats.map((s) => (
            <div key={s.l} className="card p-5">
              <dd className="font-display text-3xl font-semibold text-accent tabular-nums">{s.v}</dd>
              <dt className="mt-1 text-sm text-ink-soft">{s.l}</dt>
            </div>
          ))}
        </motion.dl>
      </div>
    </section>
  );
}

export function PSStakeholders({ stakeholders }) {
  return (
    <section className="section !py-16 section-alt" data-testid="ps-stakeholders">
      <div className="container-x">
        <SectionHeader eyebrow="Core Stakeholders" title="Tailored roles for every user" />
        <div className="mt-10 grid grid-cols-2 md:grid-cols-4 gap-4">
          {stakeholders.map((s, i) => (
            <motion.div key={s} {...rise(0.06 * i)} className="card p-6 flex items-center gap-4">
              <div className="icon-tile"><UserRound className="h-5 w-5" /></div>
              <div>
                <div className="font-display text-lg font-semibold text-ink">{s}</div>
                <div className="text-xs text-ink-muted">Role-based access</div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

export function PSCapabilities({ cfg }) {
  return (
    <section id="capabilities" className="section" data-testid="ps-capabilities">
      <div className="container-x">
        <SectionHeader eyebrow="Capabilities" title="Everything in one platform," titleAccent={`built into ${cfg.name}.`} />
        <div className="mt-12 grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {cfg.capabilities.map((c, i) => (
            <motion.article key={c.t} {...rise(0.03 * i)} className="card card-hover p-6">
              <CapabilityIcon label={c.t} className="mb-5" />
              <h3 className="font-display text-lg font-semibold text-ink">{c.t.trim()}</h3>
              <p className="mt-2 text-sm leading-relaxed text-ink-soft">{c.d}</p>
            </motion.article>
          ))}
        </div>
      </div>
    </section>
  );
}

export function PSBestOutcomes({ bestFor, outcomes }) {
  return (
    <section className="section !py-16 section-alt" data-testid="ps-best-outcomes">
      <div className="container-x grid md:grid-cols-2 gap-5">
        <motion.div {...rise()} className="card p-8">
          <span className="eyebrow">Best for</span>
          <div className="mt-6 flex flex-wrap gap-2.5">
            {bestFor.map((b) => <span key={b} className="pill pill-accent !text-sm !py-2 !px-4">{b}</span>)}
          </div>
        </motion.div>
        <motion.div {...rise(0.08)} className="card p-8">
          <span className="eyebrow">Outcomes</span>
          <ul className="mt-6 space-y-3">
            {outcomes.map((o) => (
              <li key={o} className="flex items-center gap-3 text-ink">
                <span className="h-7 w-7 rounded-full bg-accent/15 text-accent grid place-items-center"><Check className="h-4 w-4" /></span>
                <span className="font-medium">{o}</span>
              </li>
            ))}
          </ul>
        </motion.div>
      </div>
    </section>
  );
}

export function PSWhyGrid({ cfg }) {
  return (
    <section className="section" data-testid="ps-why">
      <div className="container-x">
        <SectionHeader eyebrow={`Why ${cfg.name}`} title="One platform," titleAccent="measurable outcomes." align="center" />
        <div className="mt-12 grid grid-cols-2 md:grid-cols-3 gap-4">
          {cfg.whyGrid.map((w, i) => (
            <motion.div key={w} {...rise(0.04 * i)} className="card card-hover p-6 flex items-center gap-3">
              <span className="h-3 w-3 rotate-45 rounded-[3px] bg-accent shrink-0" />
              <span className="font-display text-lg font-semibold text-ink">{w}</span>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

export function PSClosing({ cfg }) {
  return (
    <section className="section !pt-4" data-testid="ps-closing">
      <div className="container-x">
        <motion.div {...rise()} className="relative overflow-hidden rounded-[2.5rem] card p-10 sm:p-14 text-center">
          <div className="wash" />
          <div className="relative">
            <span className="eyebrow">Ready to scale?</span>
            <h2 className="mt-4 h-display text-[clamp(2rem,4.4vw,3.4rem)] text-ink">See {cfg.name} on your workflows.</h2>
            <p className="mt-4 lead max-w-xl mx-auto">Book a consultation with our AI experts today.</p>
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              <Link to="/contact" className="btn btn-solid">Say Hello! <ArrowRight className="h-4 w-4" /></Link>
              <Link to="/case-studies" className="btn btn-outline">See case studies <ArrowUpRight className="h-4 w-4" /></Link>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
