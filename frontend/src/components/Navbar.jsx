import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, ChevronDown, ArrowUpRight } from "lucide-react";
import { NAV } from "@/data/content";
import ThemeToggle from "@/components/ThemeToggle";

const slug = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-");

function MenuGroup({ item }) {
  const [open, setOpen] = useState(false);
  const wide = item.children.length > 4;
  return (
    <div className="relative" onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        data-testid={`nav-menu-${slug(item.label)}`}
        className="inline-flex items-center gap-1 px-3 py-2 rounded-full text-sm font-medium text-ink-soft hover:text-ink hover:bg-ink/5 transition-colors"
      >
        {item.label}
        <ChevronDown className={`h-3.5 w-3.5 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 6 }}
            transition={{ duration: 0.18 }}
            className="absolute left-1/2 -translate-x-1/2 top-full pt-3 z-50"
          >
            <div className={`card p-2.5 grid gap-1 ${wide ? "grid-cols-2 w-[540px]" : "w-[320px]"}`}>
              {item.children.map((c) => (
                <Link
                  key={c.label}
                  to={c.to}
                  data-accent={c.accent}
                  className="group flex items-start gap-3 rounded-xl px-3 py-2.5 hover:bg-accent/10 transition-colors"
                >
                  <span className="mt-1.5 h-2.5 w-2.5 rounded-[4px] rotate-45 bg-accent shrink-0" />
                  <span>
                    <span className="block text-sm font-semibold text-ink group-hover:text-accent transition-colors">{c.label}</span>
                    {c.note && <span className="block text-xs text-ink-muted mt-0.5">{c.note}</span>}
                  </span>
                </Link>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  useEffect(() => { setOpen(false); }, [pathname]);

  return (
    <header className="fixed top-0 inset-x-0 z-50" data-testid="site-navbar">
      <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 btn btn-solid">Skip to main content</a>
      <div className="container-x mt-3">
        <div className={`flex items-center justify-between gap-4 rounded-full pl-4 pr-2 py-2 transition-all duration-300 ${scrolled ? "glass shadow-[var(--shadow-card)]" : "bg-transparent border border-transparent"}`}>
          <Link to="/" data-testid="nav-brand" className="shrink-0" aria-label="CittaAI home">
            <span className="block rounded-xl dark:bg-white dark:px-2 dark:py-0.5">
              <img src="/assets/brand/logo-wide.png" alt="CittaAI — Driven by Fixity" className="h-11 w-auto object-contain mix-blend-multiply" />
            </span>
          </Link>

          <nav className="hidden lg:flex items-center gap-0.5" aria-label="Main">
            {NAV.primary.map((item) => (item.children?.length
              ? <MenuGroup key={item.label} item={item} />
              : (
                <Link
                  key={item.label}
                  to={item.to}
                  data-testid={`nav-link-${slug(item.label)}`}
                  className={`px-3 py-2 rounded-full text-sm font-medium transition-colors ${pathname === item.to ? "text-accent bg-accent/10" : "text-ink-soft hover:text-ink hover:bg-ink/5"}`}
                >
                  {item.label}
                </Link>
              )))}
          </nav>

          <div className="flex items-center gap-2">
            <ThemeToggle />
            <Link to={NAV.cta.to} data-testid="nav-cta" className="hidden sm:inline-flex btn btn-solid !h-10 !px-4 !text-[13px]">
              {NAV.cta.label} <ArrowUpRight className="h-3.5 w-3.5" />
            </Link>
            <button
              type="button"
              onClick={() => setOpen((v) => !v)}
              data-testid="nav-mobile-toggle"
              className="lg:hidden h-10 w-10 rounded-full grid place-items-center border border-line/15 text-ink"
              aria-label={open ? "Close menu" : "Open menu"}
              aria-expanded={open}
            >
              {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

        <AnimatePresence>
          {open && (
            <motion.nav
              initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}
              className="lg:hidden mt-2 card p-3 max-h-[75vh] overflow-y-auto"
              data-testid="mobile-menu"
              aria-label="Mobile"
            >
              {NAV.primary.map((item) => (
                <div key={item.label} className="border-b border-line/10 last:border-0">
                  {item.children?.length ? (
                    <details className="group">
                      <summary className="flex items-center justify-between cursor-pointer list-none py-3 px-2 font-semibold text-ink">
                        {item.label}
                        <ChevronDown className="h-4 w-4 transition-transform group-open:rotate-180" />
                      </summary>
                      <div className="pb-2">
                        {item.children.map((c) => (
                          <Link key={c.label} to={c.to} data-accent={c.accent} className="flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-accent/10">
                            <span className="h-2 w-2 rotate-45 rounded-[3px] bg-accent" />
                            <span className="text-sm text-ink-soft">{c.label}</span>
                          </Link>
                        ))}
                      </div>
                    </details>
                  ) : (
                    <Link to={item.to} className="block py-3 px-2 font-semibold text-ink">{item.label}</Link>
                  )}
                </div>
              ))}
              <Link to={NAV.cta.to} className="btn btn-solid w-full mt-3">{NAV.cta.label}</Link>
            </motion.nav>
          )}
        </AnimatePresence>
      </div>
    </header>
  );
}
