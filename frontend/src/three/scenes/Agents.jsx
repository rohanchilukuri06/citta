// Enterprise & Agentic AI — "Intelligent & Agentic Systems Built for the Enterprise" (multi-agent systems, RAG,
// conversational AI, custom LLMs): an orchestrator plans and delegates tasks to specialist agents on their orbits;
// tasks go out (saffron), results come back (jade), and a knowledge base feeds retrieval.
import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { usePalette, useClock, PointerTilt, Lights } from "@/three/core";

const AGENTS = 5;

export default function Agents() {
  const p = usePalette();
  const t = useClock();
  const core = useRef();
  const agentRefs = useRef([]);
  const tasks = useRef([]);
  const results = useRef([]);
  const lines = useRef();
  const linePos = useMemo(() => new Float32Array(AGENTS * 6), []);
  const pos = useMemo(() => Array.from({ length: AGENTS }, () => new THREE.Vector3()), []);
  const shapes = ["sphere", "box", "octa", "cone", "torus"];
  const colours = [p.sky, p.coral, p.saffron, p.jade, p.accent];

  useFrame(() => {
    const time = t.current;
    if (core.current) { core.current.rotation.y = time * 0.6; core.current.rotation.x = time * 0.3; }
    for (let i = 0; i < AGENTS; i += 1) {
      const a = (i / AGENTS) * Math.PI * 2 + time * 0.18;
      pos[i].set(Math.cos(a) * 2.5, Math.sin(a * 2 + i) * 0.6, Math.sin(a) * 2.5);
      const ag = agentRefs.current[i];
      if (ag) { ag.position.copy(pos[i]); ag.rotation.y = time; }
      linePos.set([0, 0, 0, pos[i].x, pos[i].y, pos[i].z], i * 6);
      const u = (time * 0.35 + i / AGENTS) % 1;
      const out = Math.min(1, u * 2);           // first half: task travels out
      const back = Math.max(0, (u - 0.5) * 2);  // second half: result returns
      if (tasks.current[i]) { tasks.current[i].position.copy(pos[i]).multiplyScalar(out); tasks.current[i].visible = u < 0.5; }
      if (results.current[i]) { results.current[i].position.copy(pos[i]).multiplyScalar(1 - back); results.current[i].visible = u >= 0.5; }
    }
    if (lines.current) lines.current.geometry.attributes.position.needsUpdate = true;
  });

  return (
    <>
      <Lights />
      <PointerTilt strength={0.32} pitch={0.3}>
        {/* orchestrator / planner */}
        <mesh ref={core}>
          <icosahedronGeometry args={[0.55, 0]} />
          <meshStandardMaterial color={p.accent} emissive={p.accent} emissiveIntensity={0.35} flatShading />
        </mesh>
        <mesh>
          <sphereGeometry args={[0.85, 24, 24]} />
          <meshBasicMaterial color={p.accent} wireframe transparent opacity={0.15} />
        </mesh>
        <lineSegments ref={lines}>
          <bufferGeometry>
            <bufferAttribute attach="attributes-position" args={[linePos, 3]} />
          </bufferGeometry>
          <lineBasicMaterial color={p.inkMuted} transparent opacity={0.4} />
        </lineSegments>
        {shapes.map((s, i) => (
          <group key={s} ref={(el) => { agentRefs.current[i] = el; }}>
            <mesh>
              {s === "sphere" && <sphereGeometry args={[0.26, 20, 20]} />}
              {s === "box" && <boxGeometry args={[0.42, 0.42, 0.42]} />}
              {s === "octa" && <octahedronGeometry args={[0.3, 0]} />}
              {s === "cone" && <coneGeometry args={[0.26, 0.48, 18]} />}
              {s === "torus" && <torusGeometry args={[0.22, 0.08, 10, 28]} />}
              <meshStandardMaterial color={colours[i]} roughness={0.35} />
            </mesh>
          </group>
        ))}
        {Array.from({ length: AGENTS }).map((_, i) => (
          <group key={i}>
            <mesh ref={(el) => { tasks.current[i] = el; }}>
              <boxGeometry args={[0.1, 0.1, 0.1]} />
              <meshBasicMaterial color={p.saffron} toneMapped={false} />
            </mesh>
            <mesh ref={(el) => { results.current[i] = el; }}>
              <sphereGeometry args={[0.07, 10, 10]} />
              <meshBasicMaterial color={p.jade} toneMapped={false} />
            </mesh>
          </group>
        ))}
        {/* knowledge base the agents retrieve from */}
        <group position={[0, -1.7, 0]}>
          {[0, 0.12, 0.24].map((y) => (
            <mesh key={y} position={[0, y, 0]}>
              <boxGeometry args={[1.6, 0.08, 1.1]} />
              <meshStandardMaterial color={p.solid} />
            </mesh>
          ))}
        </group>
      </PointerTilt>
    </>
  );
}
