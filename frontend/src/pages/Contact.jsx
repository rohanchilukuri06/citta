import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, Phone, Mail, MapPin, Clock, CheckCircle2, AlertCircle } from "lucide-react";
import { CONTACT_PAGE, CONTACT } from "@/data/content";
import { rise } from "@/components/SectionHeader";
import Scene from "@/three/Scene";
import { API_BASE_URL } from "@/apiConfig";

const ICONS = [Phone, Mail, MapPin];
const field = "mt-1.5 w-full rounded-xl border border-line/15 bg-surface px-3.5 py-2.5 text-ink placeholder:text-ink-muted/70 focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/20 transition";
const label = "font-mono text-[11px] uppercase tracking-widest text-ink-muted";

export default function Contact() {
  const C = CONTACT_PAGE;
  const [status, setStatus] = useState({ state: "idle" });

  const submit = async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.currentTarget).entries());
    setStatus({ state: "sending" });
    try {
      const res = await fetch(`${API_BASE_URL}/api/contact`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data),
      });
      const body = await res.json().catch(() => ({}));
      if (res.status === 422) {
        const bad = body?.detail?.invalid;
        setStatus({ state: "error", msg: Array.isArray(bad) ? `Please check your ${bad.join(", ")}.` : "Please check the form fields." });
        return;
      }
      if (!res.ok) throw new Error(String(res.status));
      if (body.company_email === "sent") {
        e.target.reset();
        setStatus({ state: "sent", msg: body.visitor_email === "sent"
          ? `Thank you! Our team will be in touch shortly — a confirmation is on its way to ${data.email}.`
          : "Thank you! Our team has your message and will be in touch shortly." });
      } else {
        setStatus({ state: "error", msg: `We saved your message (ref ${body.reference}) but couldn't email the team right now. Please also reach us at ${CONTACT.email}.` });
      }
    } catch (err) {
      setStatus({ state: "error", msg: `Couldn't send right now. Please email ${CONTACT.email} or call ${CONTACT.phone}.` });
    }
  };

  return (
    <div data-testid="contact-page" data-accent="coral">
      <section className="relative overflow-hidden pt-28 lg:pt-32 pb-12">
        <div className="wash" />
        <div className="absolute inset-0 dotgrid opacity-60 pointer-events-none" />
        <div className="relative container-x grid lg:grid-cols-[1.05fr_1fr] gap-10 items-center">
          <div>
            <motion.div {...rise()} className="eyebrow mb-5">{C.eyebrow}</motion.div>
            <motion.h1 {...rise(0.05)} className="h-display text-[clamp(2.4rem,5.4vw,4.6rem)] text-ink">
              {C.title} <span className="text-accent-grad">{C.titleAccent}</span>
            </motion.h1>
            <motion.p {...rise(0.1)} className="mt-6 lead max-w-xl">{C.lead}</motion.p>
            <motion.p {...rise(0.15)} className="mt-6 pill"><Clock className="h-3.5 w-3.5 text-accent" /> {CONTACT.hours} · {CONTACT.response}</motion.p>
          </div>
          <Scene
            name="globe"
            className="h-[360px] sm:h-[460px] rounded-[2rem]"
            overlay={<span className="scene-label left-4 bottom-4">HQ · HITEC City, Hyderabad</span>}
          />
        </div>
      </section>

      <section className="pb-24">
        <div className="container-x grid lg:grid-cols-[1fr_1.35fr] gap-6 items-start">
          <div className="space-y-4">
            {C.cards.map((c, i) => {
              const Icon = ICONS[i];
              const inner = (
                <>
                  <div className="flex items-center gap-3">
                    <div className="icon-tile"><Icon className="h-5 w-5" /></div>
                    <span className={label}>{c.t}</span>
                  </div>
                  <div className="mt-4 font-display text-lg font-semibold text-ink">{c.v}</div>
                  <p className="mt-1.5 text-sm text-ink-soft leading-relaxed">{c.sub}</p>
                </>
              );
              return (
                <motion.div key={c.t} {...rise(0.06 * i)} data-testid={`contact-card-${i}`}>
                  {c.href ? <a href={c.href} className="block card card-hover p-6">{inner}</a> : <div className="card p-6">{inner}</div>}
                </motion.div>
              );
            })}
          </div>

          <motion.form {...rise(0.1)} onSubmit={submit} className="card p-7 sm:p-9" data-testid="contact-form">
            <h2 className="font-display text-2xl font-semibold text-ink">Send us a message</h2>
            <p className="mt-1 text-sm text-ink-soft">Fill out the form and we'll get back to you shortly.</p>
            <div className="mt-6 grid sm:grid-cols-2 gap-4">
              <label className="sm:col-span-2 block">
                <span className={label}>Inquiry type</span>
                <select name="inquiry" className={field} defaultValue={C.inquiryTypes[0]} data-testid="contact-inquiry">
                  {C.inquiryTypes.map((t) => <option key={t}>{t}</option>)}
                </select>
              </label>
              <label className="block"><span className={label}>Name</span><input required name="name" autoComplete="name" className={field} data-testid="contact-name" /></label>
              <label className="block"><span className={label}>Phone</span><input required name="phone" type="tel" autoComplete="tel" className={field} data-testid="contact-phone" /></label>
              <label className="block"><span className={label}>Business email</span><input required name="email" type="email" autoComplete="email" className={field} data-testid="contact-email" /></label>
              <label className="block"><span className={label}>Company</span><input name="company" autoComplete="organization" className={field} data-testid="contact-company" /></label>
              <label className="sm:col-span-2 block"><span className={label}>Convenient time (optional)</span><input name="timing" placeholder="e.g. Weekdays after 3pm" className={field} /></label>
              <label className="sm:col-span-2 block"><span className={label}>Message</span><textarea required name="message" rows={5} className={field} data-testid="contact-message" /></label>
            </div>
            <button type="submit" disabled={status.state === "sending"} className="btn btn-solid w-full mt-6 disabled:opacity-60" data-testid="contact-submit">
              {status.state === "sending" ? "Sending…" : <>Send message <ArrowRight className="h-4 w-4" /></>}
            </button>
            {status.msg && (
              <p role="status" className={`mt-4 flex items-start gap-2 text-sm ${status.state === "sent" ? "text-jade" : "text-coral"}`}>
                {status.state === "sent" ? <CheckCircle2 className="h-4 w-4 mt-0.5 shrink-0" /> : <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />}
                {status.msg}
              </p>
            )}
          </motion.form>
        </div>
      </section>
    </div>
  );
}
