// 360° AI-Powered Digital Marketing — "AI-driven acquisition, engagement, conversion, and revenue optimization":
// a 360° ring of eight channels (branding, social, content, SEO, PPC, e-commerce, WhatsApp, influencer) rotates
// above a funnel; leads drop from every channel, spiral down, and converge into conversions (revenue) at the bottom.
import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { usePalette, useClock, PointerTilt, Lights, seeded } from "@/three/core";

const CHANNELS = 8;
const LEADS = 70;
const TOP = 1.25;
const BOTTOM = -1.35;

export default function Funnel() {
  const p = usePalette();
  const t = useClock();
  const ring = useRef();
  const leads = useRef();
  const pool = useRef();
  const dummy = useMemo(() => new THREE.Object3D(), []);
  const seeds = useMemo(() => {
    const rnd = seeded(19);
    return Array.from({ length: LEADS }, () => ({ ch: Math.floor(rnd() * CHANNELS), o: rnd(), s: 0.18 + rnd() * 0.1 }));
  }, []);
  const funnelGeo = useMemo(() => {
    const pts = [];
    for (let i = 0; i <= 20; i += 1) {
      const y = TOP - (i / 20) * (TOP - BOTTOM);
      const k = i / 20;
      pts.push(new THREE.Vector2(0.18 + Math.pow(1 - k, 1.6) * 1.75, y));
    }
    return new THREE.LatheGeometry(pts, 48);
  }, []);
  const colours = [p.coral, p.saffron, p.jade, p.sky, p.accent, p.terracotta, p.leaf, p.gold];

  useFrame(() => {
    const time = t.current;
    const spin = time * 0.35;
    if (ring.current) ring.current.rotation.y = spin;
    seeds.forEach((s, i) => {
      const u = (s.o + time * s.s) % 1;
      const startA = (s.ch / CHANNELS) * Math.PI * 2 + spin;
      const y = TOP + 0.35 - u * (TOP + 0.35 - BOTTOM - 0.1);
      const k = Math.min(1, Math.max(0, (TOP - y) / (TOP - BOTTOM)));
      const r = u < 0.08 ? 2.25 - u * 6 : 0.12 + Math.pow(1 - k, 1.6) * 1.55;
      const a = startA + u * 5;
      dummy.position.set(Math.cos(a) * r, y, Math.sin(a) * r);
      dummy.scale.setScalar(u > 0.92 ? (1 - u) / 0.08 : 1);
      dummy.updateMatrix();
      leads.current.setMatrixAt(i, dummy.matrix);
    });
    leads.current.instanceMatrix.needsUpdate = true;
    if (pool.current) pool.current.scale.setScalar(1 + Math.sin(time * 3) * 0.08);
  });

  return (
    <>
      <Lights />
      <PointerTilt strength={0.28} pitch={0.38}>
        <mesh geometry={funnelGeo}>
          <meshStandardMaterial color={p.accent} transparent opacity={p.dark ? 0.18 : 0.14} side={THREE.DoubleSide} />
        </mesh>
        <mesh geometry={funnelGeo}>
          <meshBasicMaterial color={p.accent} wireframe transparent opacity={0.22} />
        </mesh>
        <group ref={ring} position={[0, TOP + 0.45, 0]}>
          <mesh rotation={[Math.PI / 2, 0, 0]}>
            <torusGeometry args={[2.3, 0.02, 8, 120]} />
            <meshBasicMaterial color={p.inkMuted} transparent opacity={0.45} />
          </mesh>
          {colours.map((c, i) => {
            const a = (i / CHANNELS) * Math.PI * 2;
            return (
              <mesh key={i} position={[Math.cos(a) * 2.3, 0, Math.sin(a) * 2.3]} rotation={[0, -a, 0]}>
                <boxGeometry args={[0.36, 0.36, 0.1]} />
                <meshStandardMaterial color={c} emissive={c} emissiveIntensity={0.25} roughness={0.35} />
              </mesh>
            );
          })}
        </group>
        <instancedMesh ref={leads} args={[undefined, undefined, LEADS]}>
          <sphereGeometry args={[0.055, 10, 10]} />
          <meshBasicMaterial color={p.saffron} toneMapped={false} />
        </instancedMesh>
        {/* conversions */}
        <mesh ref={pool} position={[0, BOTTOM - 0.2, 0]}>
          <sphereGeometry args={[0.28, 24, 24]} />
          <meshStandardMaterial color={p.jade} emissive={p.jade} emissiveIntensity={0.55} />
        </mesh>
      </PointerTilt>
    </>
  );
}
