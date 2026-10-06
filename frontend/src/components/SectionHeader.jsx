import { motion } from "framer-motion";

const rise = (delay = 0) => ({
  initial: { opacity: 0, y: 14 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "-60px" },
  transition: { duration: 0.6, delay, ease: [0.2, 0.7, 0.2, 1] },
});

/** Eyebrow + title (+ accent words) + optional sub/lead. Colours follow the theme and the section's accent. */
export default function SectionHeader({ eyebrow, title, titleAccent, sub, lead, align = "left", className = "" }) {
  const center = align === "center";
  return (
    <div className={`max-w-3xl ${center ? "mx-auto text-center" : ""} ${className}`}>
      {eyebrow && <motion.div {...rise()} className={`eyebrow mb-5 ${center ? "justify-center" : ""}`}>{eyebrow}</motion.div>}
      <motion.h2 {...rise(0.05)} className="h-display text-[clamp(2.1rem,4.4vw,3.6rem)] text-ink">
        {title}
        {titleAccent && <> <span className="text-accent-grad">{titleAccent}</span></>}
      </motion.h2>
      {sub && <motion.p {...rise(0.1)} className="mt-4 font-display text-xl text-ink-soft">{sub}</motion.p>}
      {lead && <motion.p {...rise(0.12)} className="mt-5 lead">{lead}</motion.p>}
    </div>
  );
}

export { rise };
