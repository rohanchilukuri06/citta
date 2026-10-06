import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowDown } from "lucide-react";
import { HOMEPAGE } from "@/data/content";
import SectionHeader, { rise } from "@/components/SectionHeader";
import Scene from "@/three/Scene";

const LAYER_ACCENT = ["sky", "cobalt", "saffron", "jade"]; // matches the layer colours in the 3D stack

export default function Stack() {
  const S = HOMEPAGE.stack;
  const [active, setActive] = useState(-1);
  return (
    <section className="section section-alt" data-accent="cobalt" data-testid="stack-section">
      <div className="container-x grid lg:grid-cols-[1fr_1.05fr] gap-14 items-center">
        <div className="order-2 lg:order-1">
          <Scene name="stack" props={{ active }} className="h-[380px] sm:h-[520px] rounded-[2rem] card" />
        </div>
        <div className="order-1 lg:order-2">
          <SectionHeader eyebrow={S.eyebrow} title={S.title} />
          <ol className="mt-10 space-y-3" onMouseLeave={() => setActive(-1)}>
            {S.steps.map((st, i) => (
              <motion.li key={st.n} {...rise(0.05 * i)}>
                <button
                  type="button"
                  data-accent={LAYER_ACCENT[i]}
                  onMouseEnter={() => setActive(i)}
                  onFocus={() => setActive(i)}
                  onBlur={() => setActive(-1)}
                  className={`w-full text-left card p-5 flex gap-4 items-start transition-all ${active === i ? "!border-accent/60 shadow-[var(--shadow-lift)] translate-x-1" : ""}`}
                >
                  <span className="icon-tile shrink-0 font-mono text-sm">{st.n}</span>
                  <span>
                    <span className="block font-display text-lg font-semibold text-ink">{st.title}</span>
                    <span className="block mt-1 text-sm leading-relaxed text-ink-soft">{st.desc}</span>
                  </span>
                </button>
              </motion.li>
            ))}
          </ol>
          <motion.p {...rise(0.2)} className="mt-6 inline-flex items-center gap-2 pill pill-accent">
            <ArrowDown className="h-3.5 w-3.5 -rotate-90" /> {S.outcome}
          </motion.p>
        </div>
      </div>
    </section>
  );
}
