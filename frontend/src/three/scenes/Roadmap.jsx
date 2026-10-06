// AI Strategy & Advisory — "Designing Enterprise AI with Clarity, Governance, and Impact": the strategic roadmap as
// a rising staircase of phases (readiness → roadmap → use-case prioritisation → governance → scale). A marker climbs
// phase by phase; each milestone flag lights as it is reached.
import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { usePalette, useClock, PointerTilt, Lights, smooth, clamp01 } from "@/three/core";

const STEPS = 5;

export default function Roadmap() {
  const p = usePalette();
  const t = useClock();
  const marker = useRef();
  const flags = useRef([]);
  const steps = useMemo(() => Array.from({ length: STEPS }, (_, i) => new THREE.Vector3((i - 2) * 1.15, i * 0.42 - 0.9, (i % 2 ? -0.25 : 0.25))), []);
  const path = useMemo(() => new THREE.CatmullRomCurve3(steps.map((s) => s.clone().add(new THREE.Vector3(0, 0.24, 0)))), [steps]);
  const pathGeo = useMemo(() => new THREE.TubeGeometry(path, 120, 0.025, 6, false), [path]);
  const colours = [p.sky, p.accent, p.saffron, p.coral, p.jade];

  useFrame(() => {
    const time = t.current;
    const cyc = (time % 9) / 9;
    // dwell on each step, then move to the next
    const raw = cyc * (STEPS + 1);
    const step = Math.min(STEPS - 1, Math.floor(raw));
    const frac = smooth(clamp01((raw - step - 0.55) / 0.45));
    const u = Math.min(1, (step + (step < STEPS - 1 ? frac : 0)) / (STEPS - 1));
    if (marker.current) {
      path.getPointAt(u, marker.current.position);
      marker.current.position.y += 0.12 + Math.abs(Math.sin(time * 6)) * 0.05 * (1 - frac);
    }
    flags.current.forEach((f, i) => {
      if (!f) return;
      const reached = i <= step;
      f.scale.y += ((reached ? 1 : 0.25) - f.scale.y) * 0.12;
      f.children[0].material.emissiveIntensity = reached ? 0.6 : 0.05;
    });
  });

  return (
    <>
      <Lights />
      <PointerTilt strength={0.3} pitch={0.32} yaw={-0.35}>
        {steps.map((s, i) => (
          <group key={i} position={s}>
            <mesh>
              <boxGeometry args={[1.0, 0.36, 1.0]} />
              <meshStandardMaterial color={p.solid} roughness={0.6} />
            </mesh>
            <mesh position={[0, 0.185, 0]} rotation={[-Math.PI / 2, 0, 0]}>
              <planeGeometry args={[0.96, 0.96]} />
              <meshStandardMaterial color={colours[i]} transparent opacity={0.35} />
            </mesh>
            <group ref={(el) => { flags.current[i] = el; }} position={[0.32, 0.18, -0.32]}>
              <mesh position={[0.12, 0.42, 0]}>
                <boxGeometry args={[0.24, 0.16, 0.02]} />
                <meshStandardMaterial color={colours[i]} emissive={colours[i]} emissiveIntensity={0.05} />
              </mesh>
              <mesh position={[0, 0.25, 0]}>
                <cylinderGeometry args={[0.012, 0.012, 0.5, 6]} />
                <meshStandardMaterial color={p.inkMuted} />
              </mesh>
            </group>
          </group>
        ))}
        <mesh geometry={pathGeo}>
          <meshBasicMaterial color={p.inkMuted} transparent opacity={0.5} />
        </mesh>
        <mesh ref={marker}>
          <sphereGeometry args={[0.13, 20, 20]} />
          <meshStandardMaterial color={p.accent} emissive={p.accent} emissiveIntensity={0.5} />
        </mesh>
      </PointerTilt>
    </>
  );
}
