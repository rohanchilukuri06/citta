import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { Sun, Moon } from "lucide-react";

/** Light ⇄ dark switch. Starts from the visitor's system setting; the choice is remembered. */
export default function ThemeToggle({ className = "" }) {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const dark = mounted && resolvedTheme === "dark";
  return (
    <button
      type="button"
      onClick={() => setTheme(dark ? "light" : "dark")}
      aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
      title={dark ? "Light theme" : "Dark theme"}
      className={`relative h-10 w-10 rounded-full grid place-items-center border border-line/15 bg-surface/70 text-ink-soft hover:text-accent hover:border-accent/50 transition-colors ${className}`}
      data-testid="theme-toggle"
    >
      <Sun className={`h-[18px] w-[18px] absolute transition-all duration-300 ${dark ? "opacity-0 rotate-90 scale-50" : "opacity-100"}`} />
      <Moon className={`h-[18px] w-[18px] absolute transition-all duration-300 ${dark ? "opacity-100" : "opacity-0 -rotate-90 scale-50"}`} />
    </button>
  );
}
