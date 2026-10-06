// Awards & Recognition — "Excellence & Innovation" (AP MSME Digital Empowerment Challenge 2025 double victory,
// Best AI Startup 2025): a turning trophy on a plinth, two winner stars orbiting it, sparkles rising.
import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { usePalette, useClock, PointerTilt, Lights, seeded } from "@/three/core";

const SPARKS = 60;

function starShape() {
  const s = new THREE.Shape();
  for (let i = 0; i < 10; i += 1) {
    const r = i % 2 ? 0.11 : 0.26;
    const a = (i / 10) * Math.PI * 2 + Math.PI / 2;
    const x = Math.cos(a) * r;
    const y = Math.sin(a) * r;
    if (i === 0) s.moveTo(x, y); else s.lineTo(x, y);
  }
  s.closePath();
  return s;
}

export default function Trophy() {
  const p = usePalette();
  const t = useClock();
  const cup = useRef();
  const stars = useRef();
  const sparkGeo = useRef();
  const cupGeo = useMemo(() => {
    const pts = [[0, 0], [0.12, 0], [0.12, 0.08], [0.06, 0.12], [0.06, 0.5], [0.12, 0.56], [0.42, 0.72], [0.62, 1.05], [0.68, 1.45], [0.62, 1.47], [0.56, 1.1], [0.38, 0.8], [0, 0.72]]
      .map(([x, y]) => new THREE.Vector2(x, y));
    return new THREE.LatheGeometry(pts, 64);
  }, []);
  const starGeo = useMemo(() => new THREE.ExtrudeGeometry(starShape(), { depth: 0.06, bevelEnabled: true, bevelSize: 0.015, bevelThickness: 0.015, bevelSegments: 2 }), []);
  const seeds = useMemo(() => {
    const rnd = seeded(3);
    return Array.from({ length: SPARKS }, () => ({ a: rnd() * Math.PI * 2, r: 0.9 + rnd() * 1.3, o: rnd(), s: 0.15 + rnd() * 0.2 }));
  }, []);
  const sparks = useMemo(() => new Float32Array(SPARKS * 3), []);

  useFrame(() => {
    const time = t.current;
    if (cup.current) cup.current.rotation.y = time * 0.5;
    if (stars.current) stars.current.rotation.y = -time * 0.7;
    seeds.forEach((s, i) => {
      const u = (s.o + time * s.s) % 1;
      sparks.set([Math.cos(s.a + time * 0.2) * s.r, -1.3 + u * 3.4, Math.sin(s.a + time * 0.2) * s.r], i * 3);
    });
    if (sparkGeo.current) sparkGeo.current.attributes.position.needsUpdate = true;
  });

  return (
    <>
      <Lights intensity={1.1} />
      <pointLight position={[0, 1.5, 2.5]} intensity={6} distance={8} color={p.saffron} />
      <PointerTilt strength={0.3} pitch={0.15}>
        <group position={[0, -1.15, 0]}>
          <mesh position={[0, 0.12, 0]}>
            <boxGeometry args={[1.25, 0.24, 1.25]} />
            <meshStandardMaterial color={p.dark ? p.solid : p.ink} roughness={0.5} />
          </mesh>
          <mesh position={[0, 0.25, 0.63]}>
            <planeGeometry args={[0.8, 0.1]} />
            <meshStandardMaterial color={p.gold} emissive={p.gold} emissiveIntensity={0.3} />
          </mesh>
          <group ref={cup} position={[0, 0.24, 0]}>
            <mesh geometry={cupGeo}>
              <meshStandardMaterial color={p.gold} metalness={0.35} roughness={0.3} emissive={p.gold} emissiveIntensity={0.12} side={THREE.DoubleSide} />
            </mesh>
            {[-1, 1].map((s) => (
              <mesh key={s} position={[s * 0.68, 1.12, 0]} rotation={[0, 0, s * 0.2]}>
                <torusGeometry args={[0.17, 0.035, 10, 24, Math.PI]} />
                <meshStandardMaterial color={p.gold} metalness={0.35} roughness={0.3} emissive={p.gold} emissiveIntensity={0.12} />
              </mesh>
            ))}
          </group>
        </group>
        <group ref={stars}>
          {[0, Math.PI].map((a, k) => (
            <mesh key={k} geometry={starGeo} position={[Math.cos(a) * 1.75, 0.55 + k * 0.4, Math.sin(a) * 1.75]}>
              <meshStandardMaterial color={k ? p.jade : p.accent} emissive={k ? p.jade : p.accent} emissiveIntensity={0.4} />
            </mesh>
          ))}
        </group>
        <points>
          <bufferGeometry ref={sparkGeo}>
            <bufferAttribute attach="attributes-position" args={[sparks, 3]} />
          </bufferGeometry>
          <pointsMaterial color={p.saffron} size={0.05} toneMapped={false} transparent opacity={0.9} />
        </points>
      </PointerTilt>
    </>
  );
}
