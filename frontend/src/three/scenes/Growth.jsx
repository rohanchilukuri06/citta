// Proven Results / Case Studies — "Real ROI with AI Systems": three columns of bars climbing (the three published
// case studies), a rising ROI line threading their tops, and an arrow marking the trend.
import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { usePalette, useClock, PointerTilt, Lights, smooth, clamp01 } from "@/three/core";

const BARS = 7;

export default function Growth() {
  const p = usePalette();
  const t = useClock();
  const groups = useRef([]);
  const line = useRef();
  const arrow = useRef();
  const lanes = useMemo(() => [-1.1, 0, 1.1], []);
  const heights = useMemo(() => lanes.map((_, li) => Array.from({ length: BARS }, (__, i) => 0.25 + Math.pow(i / (BARS - 1), 1.7) * (2.0 + li * 0.35))), [lanes]);
  const linePos = useMemo(() => new Float32Array(BARS * 3), []);
  const colours = [p.saffron, p.coral, p.accent];

  useFrame(() => {
    const time = t.current;
    const cyc = (time % 8) / 8;
    const g = cyc < 0.75 ? smooth(clamp01(cyc / 0.6)) : 1 - smooth(clamp01((cyc - 0.85) / 0.15));
    groups.current.forEach((grp, li) => {
      if (!grp) return;
      grp.children.forEach((bar, i) => {
        const h = heights[li][i] * clamp01(g * 1.4 - i * 0.06);
        bar.scale.y = Math.max(0.001, h);
        bar.position.y = h / 2;
      });
    });
    for (let i = 0; i < BARS; i += 1) {
      const h = heights[2][i] * clamp01(g * 1.4 - i * 0.06);
      linePos.set([(i - (BARS - 1) / 2) * 0.48, h + 0.15, 1.1], i * 3);
    }
    if (line.current) line.current.geometry.attributes.position.needsUpdate = true;
    if (arrow.current) {
      arrow.current.position.set(((BARS - 1) / 2) * 0.48 + 0.25, heights[2][BARS - 1] * clamp01(g * 1.4 - (BARS - 1) * 0.06) + 0.35, 1.1);
      arrow.current.visible = g > 0.6;
    }
  });

  return (
    <>
      <Lights />
      <PointerTilt strength={0.28} pitch={0.32} yaw={-0.55}>
        <group position={[0, -1.3, 0]}>
          <mesh position={[0, -0.04, 0]}>
            <boxGeometry args={[4.0, 0.08, 3.6]} />
            <meshStandardMaterial color={p.ground} roughness={0.85} />
          </mesh>
          {lanes.map((z, li) => (
            <group key={z} ref={(el) => { groups.current[li] = el; }} position={[0, 0, z]}>
              {Array.from({ length: BARS }).map((_, i) => (
                <mesh key={i} position={[(i - (BARS - 1) / 2) * 0.48, 0, 0]}>
                  <boxGeometry args={[0.3, 1, 0.3]} />
                  <meshStandardMaterial color={colours[li]} roughness={0.4} transparent opacity={0.55 + (i / BARS) * 0.45} />
                </mesh>
              ))}
            </group>
          ))}
          <line ref={line}>
            <bufferGeometry>
              <bufferAttribute attach="attributes-position" args={[linePos, 3]} />
            </bufferGeometry>
            <lineBasicMaterial color={p.jade} toneMapped={false} />
          </line>
          <mesh ref={arrow} rotation={[0, 0, -Math.PI / 4]}>
            <coneGeometry args={[0.13, 0.3, 16]} />
            <meshStandardMaterial color={p.jade} emissive={p.jade} emissiveIntensity={0.5} />
          </mesh>
        </group>
      </PointerTilt>
    </>
  );
}
