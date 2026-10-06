import { useState } from "react";
import { useParams, Link, Navigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, ArrowRight, Check, ChevronDown, Trophy } from "lucide-react";
import { SERVICE_BY_SLUG } from "@/data/services";
import SectionHeader, { rise } from "@/components/SectionHeader";
import Scene from "@/three/Scene";

/** A service page built from cittaai.com's own service catalogue (data/services.js, generated from the live site). */
export default function ServiceSubPage() {
  const { slug } = useParams();
  const svc = SERVICE_BY_SLUG[slug];
  const [active, setActive] = useState(0);
  const [faq, setFaq] = useState(-1);
  if (!svc) return <Navigate to="/services" replace />;
  const item = svc.items[Math.min(active, svc.items.length - 1)];

  return (
    <div data-testid="service-sub-page" data-accent={svc.accent}>
      <section className="relative overflow-hidden pt-28 lg:pt-32 pb-14">
        <div className="wash" />
        <div className="absolute inset-0 dotgrid opacity-60 pointer-events-none" />
        <div className="relative container-x">
          <Link to="/services" className="inline-flex items-center gap-2 text-sm text-ink-muted hover:text-accent mb-8 group">
            <ArrowLeft className="h-4 w-4 group-hover:-translate-x-0.5 transition-transform" /> All services
          </Link>
          <div className="grid lg:grid-cols-[1fr_1.05fr] gap-10 items-center">
            <div>
              <motion.div {...rise()} className="eyebrow mb-5">Service</motion.div>
              <motion.h1 {...rise(0.05)} className="h-display text-[clamp(2.4rem,5.4vw,4.4rem)] text-ink">{svc.title}</motion.h1>
              <motion.p {...rise(0.1)} className="mt-4 font-display text-2xl text-accent">{svc.subtitle}</motion.p>
              <motion.p {...rise(0.15)} className="mt-5 lead max-w-xl">{svc.description}</motion.p>
              <motion.div {...rise(0.2)} className="mt-8 flex flex-wrap gap-3">
                <Link to="/contact" className="btn btn-solid">Book a consultation <ArrowRight className="h-4 w-4" /></Link>
                <a href="#specialisations" className="btn btn-outline">{svc.items.length} specialisations</a>
              </motion.div>
            </div>
            <Scene name={svc.scene} className="h-[360px] sm:h-[440px] rounded-[2rem] card bg-accent/5" />
          </div>
        </div>
      </section>

      <section id="specialisations" className="section section-alt">
        <div className="container-x">
          <SectionHeader eyebrow="Core capabilities" title="Specialisations" />
          <div className="mt-10 flex flex-wrap gap-2" role="tablist" aria-label={`${svc.title} specialisations`}>
            {svc.items.map((x, i) => (
              <button key={x.id} type="button" role="tab" aria-selected={active === i} onClick={() => { setActive(i); setFaq(-1); }}
                className={`pill !py-2 !px-4 !text-sm transition-all ${active === i ? "!bg-accent !text-accent-ink !border-accent" : "hover:!border-accent/50"}`}>
                {x.title}
              </button>
            ))}
          </div>

          <AnimatePresence mode="wait">
            <motion.div key={item.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.3 }}
              className="mt-8 grid lg:grid-cols-[1.2fr_1fr] gap-5">
              <div className="card p-8">
                <h2 className="h-display text-3xl text-ink">{item.title}</h2>
                {item.shortDescription && <p className="mt-2 font-medium text-accent">{item.shortDescription}</p>}
                <p className="mt-4 text-ink-soft leading-relaxed">{item.fullDescription}</p>
                {item.features && (
                  <ul className="mt-6 grid sm:grid-cols-2 gap-3">
                    {item.features.map((f) => (
                      <li key={f} className="flex gap-2.5 text-sm text-ink">
                        <span className="mt-0.5 h-5 w-5 shrink-0 rounded-full bg-accent/15 text-accent grid place-items-center"><Check className="h-3 w-3" /></span>{f}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <div className="space-y-4">
                {item.benefits?.map((b) => (
                  <div key={b.title} className="card p-6">
                    <div className="font-display text-lg font-semibold text-ink">{b.title}</div>
                    <div className="mt-1 text-sm text-ink-soft">{b.description}</div>
                  </div>
                ))}
                {item.caseStudies?.map((c) => (
                  <div key={c.title} className="card p-6 border-accent/30">
                    <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-accent"><Trophy className="h-3.5 w-3.5" /> Case study</div>
                    <div className="mt-2 font-display font-semibold text-ink">{c.title}</div>
                    <ul className="mt-2 space-y-1 text-sm text-ink-soft">{c.points?.map((p) => <li key={p}>• {p}</li>)}</ul>
                    {c.result && <div className="mt-3 font-display text-lg font-semibold text-accent">{c.result}</div>}
                  </div>
                ))}
              </div>
            </motion.div>
          </AnimatePresence>

          {item.process && (
            <div className="mt-14">
              <h3 className="eyebrow">Implementation roadmap</h3>
              <ol className="mt-6 grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                {item.process.map((st, i) => (
                  <li key={st.title} className="card p-6 relative">
                    <span className="font-mono text-xs text-accent">0{i + 1}</span>
                    <div className="mt-2 font-display font-semibold text-ink">{st.title}</div>
                    <p className="mt-2 text-sm text-ink-soft leading-relaxed">{st.description}</p>
                  </li>
                ))}
              </ol>
            </div>
          )}

          {item.faq && (
            <div className="mt-14 max-w-3xl">
              <h3 className="eyebrow">Frequently asked questions</h3>
              <div className="mt-6 space-y-3">
                {item.faq.map((f, i) => (
                  <div key={f.question} className="card">
                    <button type="button" onClick={() => setFaq(faq === i ? -1 : i)} aria-expanded={faq === i}
                      className="w-full flex items-center justify-between gap-4 p-5 text-left font-semibold text-ink">
                      {f.question}
                      <ChevronDown className={`h-4 w-4 shrink-0 transition-transform ${faq === i ? "rotate-180 text-accent" : ""}`} />
                    </button>
                    {faq === i && <p className="px-5 pb-5 -mt-1 text-sm text-ink-soft leading-relaxed">{f.answer}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
