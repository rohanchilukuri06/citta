// Real Estate OS — "listings → leads → site visits → agreements → post-sale → analytics": a district of towers rises,
// one project tower is lit floor by floor (inventory sold), and lead pins drop onto listed buildings.
import { useLayoutEffect, useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { usePalette, useClock, PointerTilt, Lights, seeded, smooth, clamp01 } from "@/three/core";

const GRID = 6;
const FLOORS = 12;

export default function Skyline() {
  const p = usePalette();
  const t = useClock();
  const towers = useMemo(() => {
    const rnd = seeded(41);
    const out = [];
    for (let x = 0; x < GRID; x += 1) for (let z = 0; z < GRID; z += 1) {
      if ((x === 2 || x === 3) && (z === 2 || z === 3)) continue; // the plaza for the featured project
      out.push({ x: (x - (GRID - 1) / 2) * 0.78, z: (z - (GRID - 1) / 2) * 0.78, h: 0.35 + rnd() * 1.5, d: rnd() * 0.6, lead: rnd() < 0.22 });
    }
    return out;
  }, []);
  const mesh = useRef();
  const pins = useRef();
  const floors = useRef();
  const dummy = useMemo(() => new THREE.Object3D(), []);
  const col = useMemo(() => new THREE.Color(), []);
  const leadTowers = towers.filter((tw) => tw.lead);

  useLayoutEffect(() => {
    towers.forEach((tw, i) => mesh.current.setColorAt(i, col.set(tw.lead ? p.sky : p.solid)));
    if (mesh.current.instanceColor) mesh.current.instanceColor.needsUpdate = true;
  }, [towers, p, col]);

  useFrame(() => {
    const time = t.current;
    towers.forEach((tw, i) => {
      const grow = smooth(clamp01((time - tw.d) / 1.6));
      const h = tw.h * grow + 0.001;
      dummy.position.set(tw.x, h / 2, tw.z);
      dummy.rotation.set(0, 0, 0);
      dummy.scale.set(0.5, h, 0.5);
      dummy.updateMatrix();
      mesh.current.setMatrixAt(i, dummy.matrix);
    });
    mesh.current.instanceMatrix.needsUpdate = true;
    leadTowers.forEach((tw, i) => {
      const bob = Math.sin(time * 2 + i) * 0.08;
      const drop = smooth(clamp01((time - 1.8 - i * 0.15) / 0.8));
      dummy.position.set(tw.x, tw.h + 0.45 + bob + (1 - drop) * 1.5, tw.z);
      dummy.rotation.set(Math.PI, time, 0);
      dummy.scale.setScalar(drop);
      dummy.updateMatrix();
      pins.current.setMatrixAt(i, dummy.matrix);
    });
    pins.current.instanceMatrix.needsUpdate = true;
    // featured project: floors light up in sequence (units sold)
    const sold = Math.floor(((time * 1.2) % (FLOORS + 4)));
    for (let f = 0; f < FLOORS; f += 1) {
      floors.current.setColorAt(f, col.set(f < sold ? p.accent : p.solid));
    }
    if (floors.current.instanceColor) floors.current.instanceColor.needsUpdate = true;
  });

  useLayoutEffect(() => {
    for (let f = 0; f < FLOORS; f += 1) {
      dummy.position.set(0, 0.12 + f * 0.22, 0);
      dummy.rotation.set(0, 0, 0);
      dummy.scale.set(1, 1, 1);
      dummy.updateMatrix();
      floors.current.setMatrixAt(f, dummy.matrix);
    }
    floors.current.instanceMatrix.needsUpdate = true;
  }, [dummy]);

  return (
    <>
      <Lights />
      <PointerTilt strength={0.3} pitch={0.5} yaw={0.7}>
        <group position={[0, -1.1, 0]}>
          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]}>
            <planeGeometry args={[5.4, 5.4]} />
            <meshStandardMaterial color={p.ground} roughness={0.9} />
          </mesh>
          <instancedMesh ref={mesh} args={[undefined, undefined, towers.length]}>
            <boxGeometry args={[1, 1, 1]} />
            <meshStandardMaterial roughness={0.55} />
          </instancedMesh>
          <instancedMesh ref={pins} args={[undefined, undefined, leadTowers.length]}>
            <coneGeometry args={[0.1, 0.28, 12]} />
            <meshStandardMaterial color={p.coral} emissive={p.coral} emissiveIntensity={0.4} />
          </instancedMesh>
          {/* featured project tower, floor by floor */}
          <instancedMesh ref={floors} args={[undefined, undefined, FLOORS]}>
            <boxGeometry args={[0.95, 0.18, 0.95]} />
            <meshStandardMaterial roughness={0.4} emissive={p.accent} emissiveIntensity={0.06} />
          </instancedMesh>
          <mesh position={[0, FLOORS * 0.22 + 0.14, 0]}>
            <boxGeometry args={[0.7, 0.08, 0.7]} />
            <meshStandardMaterial color={p.saffron} />
          </mesh>
        </group>
      </PointerTilt>
    </>
  );
}
