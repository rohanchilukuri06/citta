import { motion } from "framer-motion";
import { Database, FlaskConical, Unplug, Hourglass } from "lucide-react";
import { HOMEPAGE } from "@/data/content";
import SectionHeader, { rise } from "@/components/SectionHeader";
import Scene from "@/three/Scene";

const ICONS = [Database, FlaskConical, Unplug, Hourglass];

export default function Challenges() {
  const C = HOMEPAGE.challenges;
  return (
    <section className="section section-alt" data-accent="coral" data-testid="challenges-section">
      <div className="container-x grid lg:grid-cols-2 gap-14 items-center">
        <div>
          <SectionHeader eyebrow={C.eyebrow} title={C.title} />
          <div className="mt-10 grid sm:grid-cols-2 gap-4">
            {C.items.map((it, i) => {
              const Icon = ICONS[i];
              return (
                <motion.div key={it.title} {...rise(0.05 * i)} className="card card-hover p-5">
                  <div className="icon-tile mb-4"><Icon className="h-5 w-5" /></div>
                  <h3 className="font-display text-lg font-semibold text-ink">{it.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-ink-soft">{it.desc}</p>
                </motion.div>
              );
            })}
          </div>
        </div>
        <div className="relative">
          <Scene
            name="fragments"
            className="h-[380px] sm:h-[480px] rounded-[2rem] card"
            overlay={
              <>
                <span className="scene-label left-4 top-4 !text-coral">Fragmented: {C.contrast.left}</span>
                <span className="scene-label right-4 bottom-4" style={{ color: "rgb(var(--c-jade))" }}>Unified, AI-ready platform</span>
              </>
            }
          />
          <p className="mt-4 text-sm text-ink-muted text-center">Siloed data and isolated pilots, assembled into one platform that scales.</p>
        </div>
      </div>
    </section>
  );
}
