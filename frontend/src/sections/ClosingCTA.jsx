import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { ArrowRight, ArrowUpRight } from "lucide-react";
import { HOMEPAGE } from "@/data/content";
import { rise } from "@/components/SectionHeader";

export default function ClosingCTA({ data = HOMEPAGE.closing }) {
  return (
    <section className="section" data-accent="cobalt" data-testid="closing-cta">
      <div className="container-x">
        <motion.div {...rise()} className="relative overflow-hidden rounded-[2.5rem] card p-10 sm:p-16 text-center">
          <div className="wash" />
          <div className="absolute inset-0 dotgrid opacity-60 pointer-events-none" />
          <div className="relative">
            <span className="eyebrow">Next step</span>
            <h2 className="mt-5 h-display text-[clamp(2.2rem,5vw,4rem)] text-ink">{data.title}</h2>
            <p className="mt-5 lead max-w-2xl mx-auto">{data.desc}</p>
            <div className="mt-9 flex flex-wrap justify-center gap-3">
              {data.ctas.map((c) => (
                <Link key={c.label} to={c.to} className={`btn ${c.primary ? "btn-solid" : "btn-outline"}`}>
                  {c.label} {c.primary ? <ArrowRight className="h-4 w-4" /> : <ArrowUpRight className="h-4 w-4" />}
                </Link>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
