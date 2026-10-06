/**
 * Shared 3D infrastructure for every scene on the site.
 *
 *  - <SceneCanvas>: mounts its scene only when it's near the viewport, stops rendering when it scrolls away,
 *    renders a single still frame for visitors who prefer reduced motion, and shows a soft gradient where WebGL
 *    is unavailable.
 *  - useScenePalette(): the active theme's colours (read from the CSS tokens), so scenes recolour with the theme
 *    and with the page's accent.
 *  - pointer: one window-level pointer feed (−1…1) so scenes can react to the mouse even behind page content.
 */
import { createContext, Suspense, useContext, useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { useTheme } from "next-themes";
import * as THREE from "three";

// ------------------------------------------------------------------ pointer
export const pointer = { x: 0, y: 0 };
if (typeof window !== "undefined") {
  window.addEventListener("pointermove", (e) => {
    pointer.x = (e.clientX / window.innerWidth) * 2 - 1;
    pointer.y = -((e.clientY / window.innerHeight) * 2 - 1);
  }, { passive: true });
}

// ------------------------------------------------------------------ environment checks
let webglSupport;
export function hasWebGL() {
  if (webglSupport !== undefined) return webglSupport;
  try {
    const c = document.createElement("canvas");
    webglSupport = !!(window.WebGLRenderingContext && (c.getContext("webgl2") || c.getContext("webgl")));
  } catch (e) {
    webglSupport = false;
  }
  return webglSupport;
}

export function useReducedMotion() {
  const [reduced, setReduced] = useState(() =>
    typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches);
  useEffect(() => {
    const mq = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    if (!mq) return undefined;
    const on = () => setReduced(mq.matches);
    mq.addEventListener?.("change", on);
    return () => mq.removeEventListener?.("change", on);
  }, []);
  return reduced;
}

// ------------------------------------------------------------------ palette
const TOKENS = ["canvas", "canvas-2", "surface", "surface-2", "ink", "ink-soft", "ink-muted", "line",
  "accent", "cobalt", "jade", "saffron", "coral", "sky", "terracotta", "leaf", "gold"];

function readPalette(el) {
  const cs = getComputedStyle(el);
  const out = {};
  for (const t of TOKENS) {
    const raw = cs.getPropertyValue(`--c-${t}`).trim().split(/\s+/).map(Number);
    const key = t.replace(/-([a-z0-9])/g, (_, c) => c.toUpperCase()); // ink-soft → inkSoft, canvas-2 → canvas2
    out[key] = raw.length === 3 && raw.every((n) => !Number.isNaN(n))
      ? `rgb(${raw[0]}, ${raw[1]}, ${raw[2]})` : "#888888";
  }
  return out;
}

const PaletteContext = createContext(null);
const MotionContext = createContext({ reduced: false });

/** Theme colours inside a scene: { accent, jade, saffron, coral, sky, ink, inkMuted, surface, canvas, dark, … } */
export function usePalette() {
  return useContext(PaletteContext);
}
export function useMotion() {
  return useContext(MotionContext);
}

// ------------------------------------------------------------------ canvas
/**
 * @param camera   three.js camera props, default { position: [0, 0, 7], fov: 45 }
 * @param className sizing classes for the frame (give it a height)
 * @param label    accessible description of what the scene shows
 */
export function SceneCanvas({ children, className = "", camera, label, overlay = null, dpr = [1, 1.75], accent }) {
  const frame = useRef(null);
  const [near, setNear] = useState(false);
  const [visible, setVisible] = useState(false);
  const [palette, setPalette] = useState(null);
  const { resolvedTheme } = useTheme();
  const reduced = useReducedMotion();
  const supported = typeof window !== "undefined" && hasWebGL();

  useEffect(() => {
    const el = frame.current;
    if (!el) return undefined;
    const io = new IntersectionObserver(([entry]) => {
      setVisible(entry.isIntersecting);
      if (entry.isIntersecting) setNear(true);
    }, { rootMargin: "240px 0px" });
    io.observe(el);
    return () => io.disconnect();
  }, []);

  // Re-read colours whenever the theme flips (the html class is already updated when this runs)
  useEffect(() => {
    if (!frame.current) return undefined;
    const update = () => {
      if (!frame.current) return;
      const dark = document.documentElement.classList.contains("dark");
      const pal = readPalette(frame.current);
      // 3D bodies need mid-tones: very dark sRGB colours turn almost black under WebGL lighting
      pal.solid = dark ? "rgb(84, 128, 119)" : pal.surface;   // buildings, tiles, blocks
      pal.ground = dark ? "rgb(40, 72, 66)" : pal.canvas2;    // platforms and ground planes
      setPalette({ ...pal, dark });
    };
    update();
    const id = requestAnimationFrame(update);
    return () => cancelAnimationFrame(id);
  }, [resolvedTheme, accent]);

  const frameloop = !visible ? "never" : reduced ? "demand" : "always";

  return (
    <div ref={frame} className={`scene-frame ${className}`} role="img" aria-label={label} data-accent={accent}>
      {(!supported || !near || !palette) && <div className="scene-fallback" aria-hidden="true" />}
      {supported && near && palette && (
        <Canvas
          dpr={dpr}
          frameloop={frameloop}
          camera={{ position: [0, 0, 7], fov: 45, near: 0.1, far: 100, ...camera }}
          gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
          style={{ position: "absolute", inset: 0 }}
          aria-hidden="true"
        >
          <PaletteContext.Provider value={palette}>
            <MotionContext.Provider value={{ reduced }}>
              <Suspense fallback={null}>{children}</Suspense>
            </MotionContext.Provider>
          </PaletteContext.Provider>
        </Canvas>
      )}
      {overlay}
    </div>
  );
}

// ------------------------------------------------------------------ scene helpers
/** Moves the camera when one canvas switches between scenes (no new WebGL context needed). */
export function CameraRig({ position = [0, 0, 7], fov = 45 }) {
  const camera = useThree((st) => st.camera);
  const invalidate = useThree((st) => st.invalidate);
  useEffect(() => {
    camera.position.set(position[0], position[1], position[2]);
    camera.fov = fov;
    camera.lookAt(0, 0, 0);
    camera.updateProjectionMatrix();
    invalidate();
  }, [camera, invalidate, position, fov]);
  return null;
}

/** Elapsed time that stands still for reduced-motion visitors. */
export function useClock() {
  const { reduced } = useMotion();
  // dev-only: ?scenet=4 starts every scene 4 s in (for screenshot review of mid-animation states)
  const start = process.env.NODE_ENV !== "production" && typeof window !== "undefined"
    ? Number(new URLSearchParams(window.location.search).get("scenet")) || 0 : 0;
  const t = useRef(reduced ? 2.5 : start);
  useFrame((_, delta) => {
    if (!reduced) t.current += Math.min(delta, 0.05);
  });
  return t;
}

/** Group that leans gently toward the mouse. */
export function PointerTilt({ children, strength = 0.35, yaw = 0, pitch = 0 }) {
  const g = useRef();
  const { reduced } = useMotion();
  useFrame((_, delta) => {
    if (!g.current || reduced) return;
    const k = 1 - Math.exp(-delta * 3);
    g.current.rotation.y += (yaw + pointer.x * strength - g.current.rotation.y) * k;
    g.current.rotation.x += (pitch - pointer.y * strength * 0.6 - g.current.rotation.x) * k;
  });
  return <group ref={g} rotation={[pitch, yaw, 0]}>{children}</group>;
}

/** Standard light rig, tuned per theme. */
export function Lights({ intensity = 1 }) {
  const p = usePalette();
  return (
    <>
      <ambientLight intensity={(p?.dark ? 0.55 : 0.85) * intensity} />
      <directionalLight position={[4, 6, 5]} intensity={(p?.dark ? 1.2 : 1.6) * intensity} />
      <directionalLight position={[-5, -2, -4]} intensity={0.35 * intensity} color={p?.jade} />
    </>
  );
}

export const smooth = (x) => x * x * (3 - 2 * x);
export const clamp01 = (x) => Math.max(0, Math.min(1, x));
export const color = (c) => new THREE.Color(c);

/** Fibonacci sphere — evenly spread points. */
export function fibonacciSphere(count, radius = 1) {
  const pts = [];
  const phi = Math.PI * (Math.sqrt(5) - 1);
  for (let i = 0; i < count; i += 1) {
    const y = 1 - (i / Math.max(1, count - 1)) * 2;
    const r = Math.sqrt(1 - y * y);
    const th = phi * i;
    pts.push(new THREE.Vector3(Math.cos(th) * r * radius, y * radius, Math.sin(th) * r * radius));
  }
  return pts;
}

/** Deterministic pseudo-random (scenes look the same on every load). */
export function seeded(seed = 1) {
  let s = seed;
  return () => {
    s = (s * 16807) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

export function useInstanceMatrix(count) {
  return useMemo(() => ({ dummy: new THREE.Object3D(), color: new THREE.Color(), count }), [count]);
}
