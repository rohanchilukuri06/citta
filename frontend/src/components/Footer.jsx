import { Link } from "react-router-dom";
import { Linkedin, Twitter, Youtube, Instagram, Phone, Mail, MapPin } from "lucide-react";
import { BRAND, FOOTER } from "@/data/content";

const socialIcons = { LinkedIn: Linkedin, X: Twitter, YouTube: Youtube, Instagram: Instagram };

export default function Footer() {
  return (
    <footer className="relative border-t border-line/10 bg-canvas2 pt-20 pb-10 overflow-hidden" data-testid="site-footer">
      <div className="relative container-x">
        <div className="grid grid-cols-2 lg:grid-cols-12 gap-y-12 gap-x-8">
          <div className="col-span-2 lg:col-span-4">
            <Link to="/" className="inline-block rounded-xl bg-white px-3 py-1.5 border border-line/10" aria-label="CittaAI home">
              <img src={BRAND.logoWide} alt="CittaAI — Driven by Fixity" className="h-12 w-auto object-contain mix-blend-multiply" />
            </Link>
            <p className="mt-5 text-sm text-ink-soft max-w-xs leading-relaxed">
              The intelligence layer for the modern enterprise. Engineering autonomy from the ground up.
            </p>
            <p className="mt-4 font-display text-accent text-sm font-medium">{BRAND.tagline}</p>
            <div className="mt-6 flex items-center gap-2.5">
              {FOOTER.socials.map(({ l, href }) => {
                const Ico = socialIcons[l] || Linkedin;
                return (
                  <a key={l} href={href} aria-label={l} className="h-9 w-9 rounded-full border border-line/15 grid place-items-center text-ink-soft hover:text-accent hover:border-accent transition-colors">
                    <Ico className="h-4 w-4" />
                  </a>
                );
              })}
            </div>
          </div>

          {FOOTER.columns.map((col) => (
            <div key={col.h} className="lg:col-span-2">
              <h4 className="eyebrow mb-4">{col.h}</h4>
              <ul className="space-y-2.5">
                {col.links.map((l) => (
                  <li key={l.l}><Link to={l.to} className="text-sm text-ink-soft hover:text-accent transition-colors">{l.l}</Link></li>
                ))}
              </ul>
            </div>
          ))}

          <div className="col-span-2 lg:col-span-2">
            <h4 className="eyebrow mb-4">Contact</h4>
            <ul className="space-y-3 text-sm text-ink-soft">
              <li className="flex items-start gap-2"><Phone className="h-4 w-4 mt-0.5 text-accent shrink-0" /><a href={`tel:${FOOTER.contact.phoneRaw}`} className="hover:text-accent">{FOOTER.contact.phone}</a></li>
              <li className="flex items-start gap-2"><Mail className="h-4 w-4 mt-0.5 text-accent shrink-0" /><a href={`mailto:${FOOTER.contact.email}`} className="hover:text-accent">{FOOTER.contact.email}</a></li>
              <li className="flex items-start gap-2"><MapPin className="h-4 w-4 mt-0.5 text-accent shrink-0" /><span className="leading-relaxed">{FOOTER.contact.address}</span></li>
            </ul>
          </div>
        </div>

        <div className="mt-14 pt-8 border-t border-line/10 flex flex-wrap items-center gap-3">
          <span className="font-mono text-[11px] uppercase tracking-widest text-ink-muted mr-2">Certified</span>
          {FOOTER.badges.map((b) => (
            <div key={b.alt} className="h-12 rounded-xl bg-white px-4 flex items-center justify-center border border-line/10" title={b.alt}>
              <img src={b.src} alt={b.alt} className="h-7 w-auto object-contain" />
            </div>
          ))}
        </div>

        <div className="mt-8 pt-6 border-t border-line/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <p className="text-xs text-ink-muted font-mono">{FOOTER.legal.copy}</p>
          <div className="flex flex-wrap gap-5">
            {FOOTER.legal.links.map((l) => (
              <Link key={l.l} to={l.to} className="text-xs text-ink-muted hover:text-accent">{l.l}</Link>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}
