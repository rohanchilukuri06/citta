// Enterprise AI OS — "Nine powerful modules covering every aspect of modern enterprise AI. Built to move from
// PoC → Production": a 3×3 grid of modules on one platform. Modules are promoted one after another — each rises
// out of the PoC plane, turns jade (in production), and links up with its neighbours.
import { useLayoutEffect, useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { usePalette, useClock, PointerTilt, Lights, smooth, clamp01 } from "@/three/core";

const ORDER = [4, 1, 3, 5, 7, 0, 2, 6, 8]; // promote the centre first, then outward

export default function ModuleGrid() {
  const p = usePalette();
  const t = useClock();
  const mesh = useRef();
  const links = useRef();
  const dummy = useMemo(() => new THREE.Object3D(), []);
  const col = useMemo(() => new THREE.Color(), []);
  const jade = useMemo(() => new THREE.Color(), []);
  const cells = useMemo(() => Array.from({ length: 9 }, (_, i) => ({ x: (i % 3 - 1) * 1.05, z: (Math.floor(i / 3) - 1) * 1.05 })), []);
  const edges = useMemo(() => {
    const out = [];
    cells.forEach((_, i) => {
      if (i % 3 < 2) out.push([i, i + 1]);
      if (i < 6) out.push([i, i + 3]);
    });
    return out;
  }, [cells]);
  const linePos = useMemo(() => new Float32Array(edges.length * 6), [edges]);

  useLayoutEffect(() => { jade.set(p.jade); }, [p, jade]);

  useFrame(() => {
    const time = t.current;
    const cycle = (time % 11) / 11; // ~11 s: promote all nine, hold, reset
    const promoted = [];
    cells.forEach((c, i) => {
      const rank = ORDER.indexOf(i);
      const k = smooth(clamp01(cycle * 13 - rank - 0.5)) * (cycle > 0.93 ? 1 - (cycle - 0.93) / 0.07 : 1);
      promoted[i] = k;
      const wave = Math.sin(time * 2 + i) * 0.03;
      dummy.position.set(c.x, 0.2 + k * 0.45 + wave, c.z);
      dummy.rotation.set(0, k * Math.PI * 0.5, 0);
      dummy.scale.set(0.8, 0.4 + k * 0.25, 0.8);
      dummy.updateMatrix();
      mesh.current.setMatrixAt(i, dummy.matrix);
      mesh.current.setColorAt(i, col.set(p.solid).lerp(jade, k));
    });
    mesh.current.instanceMatrix.needsUpdate = true;
    if (mesh.current.instanceColor) mesh.current.instanceColor.needsUpdate = true;
    edges.forEach(([a, b], k) => {
      const on = Math.min(promoted[a], promoted[b]);
      const ya = 0.2 + promoted[a] * 0.45 + 0.35;
      const yb = 0.2 + promoted[b] * 0.45 + 0.35;
      linePos.set([cells[a].x, ya * on - 5 * (1 - on), cells[a].z, cells[b].x, yb * on - 5 * (1 - on), cells[b].z], k * 6);
    });
    if (links.current) links.current.geometry.attributes.position.needsUpdate = true;
  });

  return (
    <>
      <Lights />
      <PointerTilt strength={0.3} pitch={0.6} yaw={0.7}>
        <group position={[0, -0.7, 0]}>
          <mesh position={[0, -0.05, 0]}>
            <boxGeometry args={[3.8, 0.1, 3.8]} />
            <meshStandardMaterial color={p.ground} roughness={0.8} />
          </mesh>
          <mesh position={[0, 0.02, 0]} rotation={[-Math.PI / 2, 0, 0]}>
            <planeGeometry args={[3.6, 3.6, 6, 6]} />
            <meshBasicMaterial color={p.accent} wireframe transparent opacity={0.25} />
          </mesh>
          <instancedMesh ref={mesh} args={[undefined, undefined, 9]}>
            <boxGeometry args={[1, 1, 1]} />
            <meshStandardMaterial roughness={0.4} emissive={p.jade} emissiveIntensity={0.08} />
          </instancedMesh>
          <lineSegments ref={links}>
            <bufferGeometry>
              <bufferAttribute attach="attributes-position" args={[linePos, 3]} />
            </bufferGeometry>
            <lineBasicMaterial color={p.saffron} toneMapped={false} />
          </lineSegments>
        </group>
      </PointerTilt>
    </>
  );
}
