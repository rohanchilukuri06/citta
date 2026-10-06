import { useState } from "react";
import { motion } from "framer-motion";
import { Linkedin, ShieldCheck, Timer, LifeBuoy, Cpu } from "lucide-react";
import { ABOUT } from "@/data/content";
import SectionHeader, { rise } from "@/components/SectionHeader";
import Scene from "@/three/Scene";

const WHY_ICONS = [ShieldCheck, Timer, LifeBuoy, Cpu];
const PRINCIPLE_ACCENT = ["cobalt", "jade", "saffron", "coral"];

function Person({ p, big }) {
  const [broken, setBroken] = useState(false);
  const initials = p.name.split(" ").map((w) => w[0]).slice(0, 2).join("");
  return (
    <motion.article {...rise()} className="card card-hover overflow-hidden">
      <div className={`${big ? "h-72" : "h-56"} bg-canvas2 relative`}>
        {!broken && p.photo
          ? <img src={p.photo} alt={p.name} loading="lazy" onError={() => setBroken(true)} className="h-full w-full object-cover object-top" />
          : <div className="h-full w-full grid place-items-center font-display text-5xl font-semibold text-accent bg-accent/10">{initials}</div>}
      </div>
      <div className="p-5 flex items-start justify-between gap-3">
        <div>
          <h3 className="font-display text-lg font-semibold text-ink">{p.name}</h3>
          <p className="text-sm text-accent font-medium">{p.title}</p>
        </div>
        {p.linkedin && p.linkedin !== "#" && (
          <a href={p.linkedin} aria-label={`${p.name} on LinkedIn`} className="h-9 w-9 rounded-full border border-line/15 grid place-items-center text-ink-soft hover:text-accent"><Linkedin className="h-4 w-4" /></a>
        )}
      </div>
    </motion.article>
  );
}

export default function About() {
  const A = ABOUT;
  return (
    <div data-testid="about-page" data-accent="cobalt">
      <section className="relative overflow-hidden pt-28 lg:pt-32 pb-12">
        <div className="wash" />
        <div className="absolute inset-0 dotgrid opacity-60 pointer-events-none" />
        <div className="relative container-x grid lg:grid-cols-[1.05fr_1fr] gap-10 items-center">
          <div>
            <motion.div {...rise()} className="eyebrow mb-5">{A.eyebrow}</motion.div>
            <motion.h1 {...rise(0.05)} className="h-display text-[clamp(2.6rem,6vw,5rem)] text-ink">
              {A.title} <span className="text-accent-grad">{A.titleAccent}</span>
            </motion.h1>
            <motion.p {...rise(0.1)} className="mt-6 lead max-w-xl">{A.lead}</motion.p>
          </div>
          <Scene name="neural" props={{ calm: true }} className="h-[360px] sm:h-[440px] rounded-[2rem]"
            label="A calm knowledge network: research-grade intelligence at enterprise scale." />
        </div>
        <div className="relative container-x mt-12 grid grid-cols-2 lg:grid-cols-4 gap-4">
          {A.stats.map((s) => (
            <div key={s.l} className="card p-6">
              <div className="font-display text-4xl font-semibold text-accent tabular-nums">{s.v}</div>
              <div className="mt-1 text-sm text-ink-soft">{s.l}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="section section-alt">
        <div className="container-x grid lg:grid-cols-2 gap-12 items-center">
          <div>
            <SectionHeader eyebrow="Our Story" title={A.storyTitle} />
            <motion.p {...rise(0.1)} className="mt-6 lead">{A.story}</motion.p>
          </div>
          <div className="grid sm:grid-cols-2 gap-4">
            {A.why.map((w, i) => {
              const Icon = WHY_ICONS[i];
              return (
                <motion.div key={w.t} {...rise(0.06 * i)} className="card p-6">
                  <div className="icon-tile mb-4"><Icon className="h-5 w-5" /></div>
                  <h3 className="font-display font-semibold text-ink">{w.t}</h3>
                  <p className="mt-2 text-sm text-ink-soft leading-relaxed">{w.d}</p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container-x">
          <SectionHeader eyebrow="Principles" title="The principles that" titleAccent="drive us." align="center"
            lead="We believe in engineering excellence, radical transparency, and the transformative power of intelligence." />
          <div className="mt-12 grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {A.principles.map((p, i) => (
              <motion.div key={p.t} {...rise(0.06 * i)} data-accent={PRINCIPLE_ACCENT[i]} className="card card-hover p-6">
                <span className="h-3 w-3 block rotate-45 rounded-[3px] bg-accent" />
                <h3 className="mt-5 font-display text-lg font-semibold text-ink">{p.t}</h3>
                <p className="mt-2 text-sm text-ink-soft leading-relaxed">{p.d}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section className="section section-alt">
        <div className="container-x">
          <SectionHeader eyebrow="The People" title="The minds behind" titleAccent="the intelligence." lead={A.team.subtitle} />
          <div className="mt-12 grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {A.team.leaders.map((p) => <Person key={p.name} p={p} big />)}
          </div>
          <div className="mt-5 grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {A.team.others.map((p) => <Person key={p.name} p={p} />)}
          </div>
        </div>
      </section>
    </div>
  );
}
