import { motion } from "framer-motion";
import { Trophy } from "lucide-react";
import { RECOGNITION } from "@/data/content";
import { rise } from "@/components/SectionHeader";
import Scene from "@/three/Scene";

export default function Recognition() {
  const R = RECOGNITION;
  return (
    <div data-testid="recognition-page" data-accent="gold">
      <section className="relative overflow-hidden pt-28 lg:pt-32 pb-12">
        <div className="wash" />
        <div className="absolute inset-0 dotgrid opacity-60 pointer-events-none" />
        <div className="relative container-x grid lg:grid-cols-[1.05fr_1fr] gap-10 items-center">
          <div>
            <motion.div {...rise()} className="eyebrow mb-5">{R.eyebrow}</motion.div>
            <motion.h1 {...rise(0.05)} className="h-display text-[clamp(2.4rem,5.6vw,4.8rem)] text-ink">
              {R.title} <span className="text-accent-grad">{R.titleAccent}</span>
            </motion.h1>
            <motion.p {...rise(0.1)} className="mt-6 lead max-w-xl">
              Recognized by leading industry bodies for our transformative impact on enterprise AI.
            </motion.p>
          </div>
          <Scene name="trophy" className="h-[360px] sm:h-[460px] rounded-[2rem]" />
        </div>
      </section>
      <section className="pb-24">
        <div className="container-x space-y-6">
          {R.awards.map((a, i) => (
            <motion.article key={a.name} {...rise(0.08 * i)} className="card overflow-hidden grid md:grid-cols-[0.9fr_1.1fr]">
              <div className="bg-canvas2 grid place-items-center p-6">
                <img src={a.image} alt={a.name} loading="lazy" className="max-h-80 w-auto rounded-2xl object-contain shadow-[var(--shadow-card)]" />
              </div>
              <div className="p-8 sm:p-10 flex flex-col justify-center">
                <span className="pill pill-accent self-start"><Trophy className="h-3.5 w-3.5" /> {a.subtitle}</span>
                <h2 className="mt-4 h-display text-3xl text-ink">{a.name}</h2>
                <p className="mt-2 text-sm text-ink-muted">{a.org}</p>
                {a.wins?.length ? (
                  <ul className="mt-6 space-y-3">
                    {a.wins.map((w) => (
                      <li key={w} className="flex items-center gap-3 card-soft p-4 font-medium text-ink">
                        <span className="h-3 w-3 rotate-45 rounded-[3px] bg-accent" /> {w}
                      </li>
                    ))}
                  </ul>
                ) : <p className="mt-5 text-ink-soft leading-relaxed">{a.body}</p>}
              </div>
            </motion.article>
          ))}
        </div>
      </section>
    </div>
  );
}
