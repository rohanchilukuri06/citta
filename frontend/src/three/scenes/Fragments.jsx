// "Why Enterprise AI Fails to Scale" — fragmented data and isolated pilots (scattered coral shards) assemble into
// one unified, AI-ready platform (an ordered jade lattice), then fall apart again: the problem CittaAI solves.
import { useLayoutEffect, useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { usePalette, useClock, PointerTilt, Lights, seeded, smooth, clamp01 } from "@/three/core";

const N = 4; // 4×4×4 lattice
const COUNT = N * N * N;
const GAP = 0.62;

export default function Fragments() {
  const p = usePalette();
  const t = useClock();
  const mesh = useRef();
  const frame = useRef();
  const dummy = useMemo(() => new THREE.Object3D(), []);
  const cubes = useMemo(() => {
    const rnd = seeded(23);
    const out = [];
    for (let x = 0; x < N; x += 1) for (let y = 0; y < N; y += 1) for (let z = 0; z < N; z += 1) {
      const target = new THREE.Vector3((x - 1.5) * GAP, (y - 1.5) * GAP, (z - 1.5) * GAP);
      // four silos (the four challenges) scattered around the frame
      const silo = (x + y * 2 + z) % 4;
      const centre = [new THREE.Vector3(-2.6, 1.4, 0), new THREE.Vector3(2.5, 1.5, -0.6), new THREE.Vector3(-2.3, -1.5, 0.4), new THREE.Vector3(2.4, -1.4, 0.3)][silo];
      const scattered = centre.clone().add(new THREE.Vector3((rnd() - 0.5) * 1.6, (rnd() - 0.5) * 1.3, (rnd() - 0.5) * 1.4));
      out.push({ target, scattered, spin: new THREE.Euler(rnd() * 6, rnd() * 6, rnd() * 6), delay: rnd() * 0.25 });
    }
    return out;
  }, []);
  const c1 = useMemo(() => new THREE.Color(), []);
  const c2 = useMemo(() => new THREE.Color(), []);
  const boundary = useMemo(() => new THREE.EdgesGeometry(new THREE.BoxGeometry(2.95, 2.95, 2.95)), []);

  useLayoutEffect(() => {
    cubes.forEach((_, i) => mesh.current.setColorAt(i, c1.set(p.coral)));
    if (mesh.current.instanceColor) mesh.current.instanceColor.needsUpdate = true;
  }, [cubes, p, c1]);

  useFrame(() => {
    const time = t.current;
    // 7 s cycle: hold scattered → assemble → hold unified → scatter
    const cyc = (time % 7) / 7;
    const base = cyc < 0.2 ? 0 : cyc < 0.45 ? (cyc - 0.2) / 0.25 : cyc < 0.85 ? 1 : 1 - (cyc - 0.85) / 0.15;
    c2.set(p.jade);
    cubes.forEach((cb, i) => {
      const k = smooth(clamp01((base - cb.delay * (1 - base)) * 1.15));
      dummy.position.lerpVectors(cb.scattered, cb.target, k);
      dummy.rotation.set(cb.spin.x * (1 - k) + time * 0.4 * (1 - k), cb.spin.y * (1 - k), cb.spin.z * (1 - k));
      dummy.scale.setScalar(0.42 + 0.08 * k);
      dummy.updateMatrix();
      mesh.current.setMatrixAt(i, dummy.matrix);
      mesh.current.setColorAt(i, c1.set(p.coral).lerp(c2, k));
    });
    mesh.current.instanceMatrix.needsUpdate = true;
    if (mesh.current.instanceColor) mesh.current.instanceColor.needsUpdate = true;
    if (frame.current) {
      frame.current.material.opacity = 0.5 * smooth(clamp01((base - 0.6) / 0.4));
    }
  });

  return (
    <>
      <Lights />
      <PointerTilt strength={0.3} yaw={0.6} pitch={0.35}>
        <instancedMesh ref={mesh} args={[undefined, undefined, COUNT]}>
          <boxGeometry args={[1, 1, 1]} />
          <meshStandardMaterial roughness={0.45} metalness={0.1} />
        </instancedMesh>
        {/* the platform boundary that appears once everything is unified */}
        <lineSegments ref={frame}>
          <primitive object={boundary} attach="geometry" />
          <lineBasicMaterial color={p.jade} transparent opacity={0} />
        </lineSegments>
      </PointerTilt>
    </>
  );
}
