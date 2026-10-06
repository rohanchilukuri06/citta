// Influencer Marketing Platform — "Creator Collaboration OS": a brand hub with creators of different reach on orbits.
// Campaign briefs travel out to creators (coral), sales return to the brand (jade) — native affiliate attribution.
import { useLayoutEffect, useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { usePalette, useClock, PointerTilt, Lights, seeded } from "@/three/core";

const CREATORS = 22;
const PACKETS = 26;

export default function CreatorNetwork() {
  const p = usePalette();
  const t = useClock();
  const creators = useMemo(() => {
    const rnd = seeded(31);
    return Array.from({ length: CREATORS }, (_, i) => ({
      shell: i % 3,
      angle: rnd() * Math.PI * 2,
      tilt: (rnd() - 0.5) * 1.2,
      size: 0.09 + rnd() * 0.16, // audience size
      speed: 0.12 + rnd() * 0.1,
    }));
  }, []);
  const packets = useMemo(() => {
    const rnd = seeded(77);
    return Array.from({ length: PACKETS }, (_, i) => ({ creator: Math.floor(rnd() * CREATORS), phase: rnd(), back: i % 2 === 1 }));
  }, []);
  const mesh = useRef();
  const pk = useRef();
  const lines = useRef();
  const hub = useRef();
  const dummy = useMemo(() => new THREE.Object3D(), []);
  const pos = useMemo(() => creators.map(() => new THREE.Vector3()), [creators]);
  const linePos = useMemo(() => new Float32Array(CREATORS * 6), []);
  const col = useMemo(() => new THREE.Color(), []);

  useLayoutEffect(() => {
    creators.forEach((c, i) => mesh.current.setColorAt(i, col.set([p.coral, p.saffron, p.accent][c.shell])));
    if (mesh.current.instanceColor) mesh.current.instanceColor.needsUpdate = true;
    packets.forEach((k, i) => pk.current.setColorAt(i, col.set(k.back ? p.jade : p.coral)));
    if (pk.current.instanceColor) pk.current.instanceColor.needsUpdate = true;
  }, [creators, packets, p, col]);

  useFrame(() => {
    const time = t.current;
    creators.forEach((c, i) => {
      const r = 1.7 + c.shell * 0.75;
      const a = c.angle + time * c.speed;
      pos[i].set(Math.cos(a) * r, Math.sin(a * 1.3 + c.tilt) * 0.55 + c.tilt * 0.6, Math.sin(a) * r);
      dummy.position.copy(pos[i]);
      dummy.scale.setScalar(c.size / 0.15);
      dummy.updateMatrix();
      mesh.current.setMatrixAt(i, dummy.matrix);
      linePos.set([0, 0, 0, pos[i].x, pos[i].y, pos[i].z], i * 6);
    });
    mesh.current.instanceMatrix.needsUpdate = true;
    if (lines.current) lines.current.geometry.attributes.position.needsUpdate = true;
    packets.forEach((k, i) => {
      const u = (k.phase + time * 0.42) % 1;
      const f = k.back ? 1 - u : u;
      dummy.position.copy(pos[k.creator]).multiplyScalar(f);
      dummy.scale.setScalar(0.55);
      dummy.updateMatrix();
      pk.current.setMatrixAt(i, dummy.matrix);
    });
    pk.current.instanceMatrix.needsUpdate = true;
    if (hub.current) hub.current.scale.setScalar(1 + Math.sin(time * 2.2) * 0.05);
  });

  return (
    <>
      <Lights />
      <PointerTilt strength={0.35} pitch={0.3}>
        <mesh ref={hub}>
          <dodecahedronGeometry args={[0.55, 0]} />
          <meshStandardMaterial color={p.accent} emissive={p.accent} emissiveIntensity={0.35} roughness={0.3} flatShading />
        </mesh>
        <lineSegments ref={lines}>
          <bufferGeometry>
            <bufferAttribute attach="attributes-position" args={[linePos, 3]} />
          </bufferGeometry>
          <lineBasicMaterial color={p.inkMuted} transparent opacity={0.28} />
        </lineSegments>
        <instancedMesh ref={mesh} args={[undefined, undefined, CREATORS]}>
          <sphereGeometry args={[0.15, 18, 18]} />
          <meshStandardMaterial roughness={0.35} />
        </instancedMesh>
        <instancedMesh ref={pk} args={[undefined, undefined, PACKETS]}>
          <octahedronGeometry args={[0.08, 0]} />
          <meshBasicMaterial toneMapped={false} />
        </instancedMesh>
        {[1.7, 2.45, 3.2].map((r) => (
          <mesh key={r} rotation={[Math.PI / 2, 0, 0]}>
            <torusGeometry args={[r, 0.005, 6, 140]} />
            <meshBasicMaterial color={p.inkMuted} transparent opacity={0.3} />
          </mesh>
        ))}
      </PointerTilt>
    </>
  );
}
