// "Inside CittaAI's Agentic AI Stack" — four layers (RAG intelligence → chat agents → voice agents → video agents).
// Knowledge particles rise from the base through every layer: "from manual workflows to autonomous execution".
// The layer for the step the visitor is hovering lifts and glows.
import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { usePalette, useClock, PointerTilt, Lights, seeded } from "@/three/core";

const LAYERS = 4;
const SPACING = 0.95;
const PARTICLES = 140;

function Layer({ index, active, colour }) {
  const g = useRef();
  const p = usePalette();
  const baseY = (index - (LAYERS - 1) / 2) * SPACING;
  useFrame((_, delta) => {
    if (!g.current) return;
    const target = baseY + (active ? 0.28 : 0);
    const k = 1 - Math.exp(-delta * 6);
    g.current.position.y += (target - g.current.position.y) * k;
    const s = active ? 1.06 : 1;
    g.current.scale.x += (s - g.current.scale.x) * k;
    g.current.scale.z += (s - g.current.scale.z) * k;
  });
  return (
    <group ref={g} position={[0, baseY, 0]}>
      <mesh>
        <boxGeometry args={[3.2, 0.14, 2.2]} />
        <meshStandardMaterial color={colour} transparent opacity={active ? 0.92 : p.dark ? 0.55 : 0.5}
          emissive={colour} emissiveIntensity={active ? 0.45 : 0.08} roughness={0.35} />
      </mesh>
      <lineSegments>
        <edgesGeometry args={[new THREE.BoxGeometry(3.2, 0.14, 2.2)]} />
        <lineBasicMaterial color={colour} transparent opacity={0.9} />
      </lineSegments>
      {/* small "agent" nodes sitting on each layer */}
      {[-1.1, -0.35, 0.4, 1.15].map((x, k) => (
        <mesh key={k} position={[x, 0.16, ((k % 2) - 0.5) * 0.9]}>
          <sphereGeometry args={[0.07, 14, 14]} />
          <meshStandardMaterial color={p.solid} emissive={colour} emissiveIntensity={active ? 0.9 : 0.25} />
        </mesh>
      ))}
    </group>
  );
}

export default function AgentStack({ active = -1 }) {
  const p = usePalette();
  const t = useClock();
  const colours = [p.sky, p.accent, p.saffron, p.jade];
  const seeds = useMemo(() => {
    const rnd = seeded(11);
    return Array.from({ length: PARTICLES }, () => ({ x: (rnd() - 0.5) * 2.8, z: (rnd() - 0.5) * 1.8, o: rnd(), s: 0.25 + rnd() * 0.35 }));
  }, []);
  const positions = useMemo(() => new Float32Array(PARTICLES * 3), []);
  const geo = useRef();
  const height = LAYERS * SPACING + 0.6;

  useFrame(() => {
    const time = t.current;
    seeds.forEach((s, i) => {
      const y = ((s.o + time * s.s * 0.35) % 1) * height - height / 2;
      positions.set([s.x + Math.sin(time + i) * 0.05, y, s.z], i * 3);
    });
    if (geo.current) geo.current.attributes.position.needsUpdate = true;
  });

  return (
    <>
      <Lights />
      <PointerTilt strength={0.3} yaw={-0.55} pitch={0.42}>
        {colours.map((c, i) => <Layer key={i} index={i} active={active === i} colour={c} />)}
        <points>
          <bufferGeometry ref={geo}>
            <bufferAttribute attach="attributes-position" args={[positions, 3]} />
          </bufferGeometry>
          <pointsMaterial color={p.saffron} size={0.055} transparent opacity={0.9} toneMapped={false} />
        </points>
        {/* vertical spine connecting the layers */}
        <mesh>
          <cylinderGeometry args={[0.03, 0.03, height, 8]} />
          <meshBasicMaterial color={p.inkMuted} transparent opacity={0.5} />
        </mesh>
      </PointerTilt>
    </>
  );
}
