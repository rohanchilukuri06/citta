// Home hero — "Living Intelligence": a knowledge network with signals travelling between nodes, an inner reasoning
// core, and autonomous agents orbiting it (CittaAI's agentic-AI positioning).
import { useLayoutEffect, useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { usePalette, useClock, PointerTilt, Lights, fibonacciSphere, seeded } from "@/three/core";

const NODES = 180;
const RADIUS = 2.25;
const PULSES = 46;

export default function NeuralCore({ calm = false }) {
  const p = usePalette();
  const t = useClock();
  const nodes = useMemo(() => fibonacciSphere(NODES, RADIUS), []);
  const edges = useMemo(() => {
    const out = [];
    for (let i = 0; i < nodes.length; i += 1) {
      for (let j = i + 1; j < nodes.length; j += 1) {
        if (nodes[i].distanceTo(nodes[j]) < 0.62) out.push([i, j]);
      }
    }
    return out;
  }, [nodes]);
  const linePositions = useMemo(() => {
    const arr = new Float32Array(edges.length * 6);
    edges.forEach(([a, b], k) => {
      arr.set([nodes[a].x, nodes[a].y, nodes[a].z, nodes[b].x, nodes[b].y, nodes[b].z], k * 6);
    });
    return arr;
  }, [edges, nodes]);

  // Pulses: each travels along one edge, then hops to a neighbouring edge
  const pulses = useMemo(() => {
    const rnd = seeded(7);
    return Array.from({ length: PULSES }, () => ({ edge: Math.floor(rnd() * edges.length), t: rnd(), speed: 0.35 + rnd() * 0.6 }));
  }, [edges.length]);
  const pulsePos = useMemo(() => new Float32Array(PULSES * 3), []);

  const nodeMesh = useRef();
  const pulseGeo = useRef();
  const core = useRef();
  const halo = useRef();
  const agents = useRef();
  const dummy = useMemo(() => new THREE.Object3D(), []);

  useLayoutEffect(() => {
    const c = new THREE.Color();
    nodes.forEach((v, i) => {
      dummy.position.copy(v);
      dummy.scale.setScalar(i % 9 === 0 ? 1.8 : 1);
      dummy.updateMatrix();
      nodeMesh.current.setMatrixAt(i, dummy.matrix);
      nodeMesh.current.setColorAt(i, c.set(i % 9 === 0 ? p.saffron : i % 3 === 0 ? p.jade : p.accent));
    });
    nodeMesh.current.instanceMatrix.needsUpdate = true;
    if (nodeMesh.current.instanceColor) nodeMesh.current.instanceColor.needsUpdate = true;
  }, [nodes, dummy, p]);

  useFrame((_, delta) => {
    const time = t.current;
    const speed = calm ? 0.4 : 1;
    const d = Math.min(delta, 0.05) * speed;
    pulses.forEach((pl, k) => {
      pl.t += d * pl.speed;
      if (pl.t >= 1) {
        // hop to an edge that starts where this one ended
        const end = edges[pl.edge][1];
        const next = edges.findIndex(([a], idx) => a === end && idx !== pl.edge);
        pl.edge = next >= 0 ? next : (pl.edge * 31 + 7) % edges.length;
        pl.t = 0;
      }
      const [a, b] = edges[pl.edge];
      const v = nodes[a].clone().lerp(nodes[b], pl.t);
      pulsePos.set([v.x, v.y, v.z], k * 3);
    });
    if (pulseGeo.current) pulseGeo.current.attributes.position.needsUpdate = true;
    if (core.current) {
      core.current.rotation.x = time * 0.25 * speed;
      core.current.rotation.y = time * 0.35 * speed;
    }
    if (halo.current) halo.current.scale.setScalar(1 + Math.sin(time * 1.6) * 0.06);
    if (agents.current) agents.current.rotation.y = time * 0.22 * speed;
  });

  return (
    <>
      <Lights />
      <PointerTilt strength={0.45}>
        <group rotation={[0.25, 0, 0]}>
          <instancedMesh ref={nodeMesh} args={[undefined, undefined, NODES]}>
            <sphereGeometry args={[0.035, 10, 10]} />
            <meshBasicMaterial toneMapped={false} />
          </instancedMesh>
          <lineSegments>
            <bufferGeometry>
              <bufferAttribute attach="attributes-position" args={[linePositions, 3]} />
            </bufferGeometry>
            <lineBasicMaterial color={p.accent} transparent opacity={p.dark ? 0.28 : 0.22} />
          </lineSegments>
          <points>
            <bufferGeometry ref={pulseGeo}>
              <bufferAttribute attach="attributes-position" args={[pulsePos, 3]} />
            </bufferGeometry>
            <pointsMaterial color={p.saffron} size={0.09} sizeAttenuation transparent opacity={0.95} toneMapped={false} />
          </points>

          {/* reasoning core */}
          <mesh ref={core}>
            <icosahedronGeometry args={[0.85, 1]} />
            <meshStandardMaterial color={p.accent} wireframe transparent opacity={0.55} />
          </mesh>
          <mesh ref={halo}>
            <sphereGeometry args={[0.62, 32, 32]} />
            <meshStandardMaterial color={p.jade} emissive={p.jade} emissiveIntensity={p.dark ? 0.6 : 0.3} transparent opacity={0.35} />
          </mesh>

          {/* autonomous agents on tilted orbits */}
          <group ref={agents}>
            {[0, 1, 2].map((k) => (
              <group key={k} rotation={[0.9 + k * 0.7, k * 1.2, k * 0.4]}>
                <mesh rotation={[Math.PI / 2, 0, 0]}>
                  <torusGeometry args={[3.0 + k * 0.25, 0.006, 6, 160]} />
                  <meshBasicMaterial color={p.inkMuted} transparent opacity={0.35} />
                </mesh>
                <mesh position={[3.0 + k * 0.25, 0, 0]}>
                  <octahedronGeometry args={[0.13, 0]} />
                  <meshStandardMaterial color={[p.coral, p.saffron, p.jade][k]} emissive={[p.coral, p.saffron, p.jade][k]} emissiveIntensity={0.5} />
                </mesh>
              </group>
            ))}
          </group>
        </group>
      </PointerTilt>
    </>
  );
}
