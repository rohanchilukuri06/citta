// Education OS — "The Complete Learning + Assessment + Coding Ecosystem for Colleges": an open book, knowledge
// spiralling up to a graduation cap, and the six modules (LMS, cohorts, courses, test series, coding, video)
// orbiting as tiles, each with its own mark.
import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { usePalette, useClock, PointerTilt, Lights } from "@/three/core";

const SPARKS = 90;

function ModuleMark({ kind, p }) {
  // tiny 3D glyph per module
  switch (kind) {
    case "lms": return <mesh position={[0, 0, 0.08]}><boxGeometry args={[0.32, 0.22, 0.04]} /><meshStandardMaterial color={p.accent} /></mesh>;
    case "cohort": return <group position={[0, 0, 0.08]}>{[-0.12, 0, 0.12].map((x) => <mesh key={x} position={[x, x === 0 ? 0.05 : -0.02, 0]}><sphereGeometry args={[0.07, 12, 12]} /><meshStandardMaterial color={p.coral} /></mesh>)}</group>;
    case "course": return <mesh position={[0, 0, 0.08]} rotation={[0, 0, Math.PI / 4]}><torusGeometry args={[0.12, 0.035, 8, 24]} /><meshStandardMaterial color={p.jade} /></mesh>;
    case "test": return <group position={[0, 0, 0.08]}>{[0.07, -0.02, -0.11].map((y) => <mesh key={y} position={[0, y, 0]}><boxGeometry args={[0.28, 0.04, 0.03]} /><meshStandardMaterial color={p.saffron} /></mesh>)}</group>;
    case "code": return <group position={[0, 0, 0.08]}>{[-1, 1].map((s) => <mesh key={s} position={[s * 0.1, 0, 0]} rotation={[0, 0, s * 0.6]}><boxGeometry args={[0.04, 0.24, 0.03]} /><meshStandardMaterial color={p.sky} /></mesh>)}</group>;
    default: return <mesh position={[0.02, 0, 0.08]} rotation={[0, 0, -Math.PI / 2]}><coneGeometry args={[0.13, 0.2, 3]} /><meshStandardMaterial color={p.terracotta} /></mesh>;
  }
}

export default function Learning() {
  const p = usePalette();
  const t = useClock();
  const ring = useRef();
  const cap = useRef();
  const sparkGeo = useRef();
  const sparks = useMemo(() => new Float32Array(SPARKS * 3), []);
  const modules = ["lms", "cohort", "course", "test", "code", "video"];

  useFrame(() => {
    const time = t.current;
    if (ring.current) {
      ring.current.rotation.y = time * 0.3;
      ring.current.children.forEach((tile) => { tile.rotation.y = -ring.current.rotation.y; });
    }
    if (cap.current) {
      cap.current.position.y = 1.55 + Math.sin(time * 1.4) * 0.08;
      cap.current.rotation.y = time * 0.6;
    }
    for (let i = 0; i < SPARKS; i += 1) {
      const u = (i / SPARKS + time * 0.12) % 1;
      const a = u * Math.PI * 6 + i;
      const r = 0.55 * (1 - u) + 0.08;
      sparks.set([Math.cos(a) * r, -0.15 + u * 1.6, Math.sin(a) * r], i * 3);
    }
    if (sparkGeo.current) sparkGeo.current.attributes.position.needsUpdate = true;
  });

  return (
    <>
      <Lights />
      <PointerTilt strength={0.3} pitch={0.28}>
        <group position={[0, -0.55, 0]}>
          {/* open book */}
          {[-1, 1].map((s) => (
            <group key={s} rotation={[0, 0, s * -0.16]}>
              <mesh position={[s * 0.62, -0.3, 0]}>
                <boxGeometry args={[1.2, 0.08, 0.9]} />
                <meshStandardMaterial color={p.solid} roughness={0.7} />
              </mesh>
              <mesh position={[s * 0.62, -0.36, 0]}>
                <boxGeometry args={[1.24, 0.05, 0.94]} />
                <meshStandardMaterial color={p.accent} />
              </mesh>
            </group>
          ))}
          <points>
            <bufferGeometry ref={sparkGeo}>
              <bufferAttribute attach="attributes-position" args={[sparks, 3]} />
            </bufferGeometry>
            <pointsMaterial color={p.saffron} size={0.06} toneMapped={false} />
          </points>
          {/* graduation cap */}
          <group ref={cap} position={[0, 1.55, 0]}>
            <mesh><boxGeometry args={[0.8, 0.05, 0.8]} /><meshStandardMaterial color={p.ink} /></mesh>
            <mesh position={[0, -0.13, 0]}><cylinderGeometry args={[0.26, 0.3, 0.22, 20]} /><meshStandardMaterial color={p.ink} /></mesh>
            <mesh position={[0.3, -0.1, 0.3]}><sphereGeometry args={[0.04, 10, 10]} /><meshStandardMaterial color={p.saffron} /></mesh>
          </group>
          {/* the six modules */}
          <group ref={ring} position={[0, 0.35, 0]}>
            {modules.map((m, i) => {
              const a = (i / modules.length) * Math.PI * 2;
              return (
                <group key={m} position={[Math.cos(a) * 2.25, Math.sin(i * 2.1) * 0.25, Math.sin(a) * 2.25]}>
                  <mesh>
                    <boxGeometry args={[0.7, 0.5, 0.1]} />
                    <meshStandardMaterial color={p.solid} roughness={0.5} />
                  </mesh>
                  <ModuleMark kind={m} p={p} />
                </group>
              );
            })}
          </group>
        </group>
      </PointerTilt>
    </>
  );
}
