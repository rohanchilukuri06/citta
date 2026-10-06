// Smart Cities OS — "Unified city data across IoT, mobility, and utilities": a city grid with live traffic on the
// roads, IoT sensors pulsing at intersections, and a data beacon gathering it all into one platform.
import { useLayoutEffect, useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { usePalette, useClock, PointerTilt, Lights, seeded } from "@/three/core";

const BLOCKS = 5;          // 5×5 city blocks
const SIZE = 0.82;          // block footprint
const ROAD = 0.3;           // road width
const PITCH = SIZE + ROAD;
const CARS = 34;

export default function CityGrid() {
  const p = usePalette();
  const t = useClock();
  const span = BLOCKS * PITCH;
  const buildings = useMemo(() => {
    const rnd = seeded(9);
    const out = [];
    for (let bx = 0; bx < BLOCKS; bx += 1) for (let bz = 0; bz < BLOCKS; bz += 1) {
      const cx = (bx - (BLOCKS - 1) / 2) * PITCH;
      const cz = (bz - (BLOCKS - 1) / 2) * PITCH;
      if (bx === 2 && bz === 2) continue; // central plaza (the platform beacon)
      for (let k = 0; k < 4; k += 1) {
        out.push({ x: cx + ((k % 2) - 0.5) * 0.38, z: cz + (Math.floor(k / 2) - 0.5) * 0.38, h: 0.15 + rnd() * rnd() * 1.4, park: rnd() < 0.12 });
      }
    }
    return out;
  }, []);
  const lanes = useMemo(() => {
    const out = [];
    for (let i = 0; i <= BLOCKS; i += 1) {
      const c = (i - BLOCKS / 2) * PITCH;
      out.push({ axis: "x", c }, { axis: "z", c });
    }
    return out;
  }, []);
  const cars = useMemo(() => {
    const rnd = seeded(13);
    return Array.from({ length: CARS }, () => ({ lane: Math.floor(rnd() * lanes.length), o: rnd(), dir: rnd() < 0.5 ? 1 : -1, s: 0.08 + rnd() * 0.07 }));
  }, [lanes.length]);
  const sensors = useMemo(() => {
    const out = [];
    for (let i = 1; i < BLOCKS; i += 2) for (let j = 1; j < BLOCKS; j += 2) {
      out.push(new THREE.Vector3((i - BLOCKS / 2) * PITCH, 0.02, (j - BLOCKS / 2) * PITCH));
    }
    return out;
  }, []);

  const bMesh = useRef();
  const cMesh = useRef();
  const rings = useRef([]);
  const beacon = useRef();
  const dummy = useMemo(() => new THREE.Object3D(), []);
  const col = useMemo(() => new THREE.Color(), []);

  useLayoutEffect(() => {
    buildings.forEach((b, i) => {
      dummy.position.set(b.x, b.park ? 0.02 : b.h / 2, b.z);
      dummy.rotation.set(0, 0, 0);
      dummy.scale.set(0.32, b.park ? 0.04 : b.h, 0.32);
      dummy.updateMatrix();
      bMesh.current.setMatrixAt(i, dummy.matrix);
      bMesh.current.setColorAt(i, col.set(b.park ? p.leaf : p.solid));
    });
    bMesh.current.instanceMatrix.needsUpdate = true;
    if (bMesh.current.instanceColor) bMesh.current.instanceColor.needsUpdate = true;
    cars.forEach((c, i) => cMesh.current.setColorAt(i, col.set(i % 4 === 0 ? p.coral : i % 3 === 0 ? p.saffron : p.accent)));
    if (cMesh.current.instanceColor) cMesh.current.instanceColor.needsUpdate = true;
  }, [buildings, cars, p, dummy, col]);

  useFrame(() => {
    const time = t.current;
    cars.forEach((c, i) => {
      const lane = lanes[c.lane];
      const u = ((((c.o + time * c.s * c.dir) % 1) + 1) % 1) * span - span / 2;
      const off = c.dir * 0.07;
      if (lane.axis === "x") { dummy.position.set(u, 0.06, lane.c + off); dummy.rotation.set(0, 0, 0); }
      else { dummy.position.set(lane.c + off, 0.06, u); dummy.rotation.set(0, Math.PI / 2, 0); }
      dummy.scale.setScalar(1);
      dummy.updateMatrix();
      cMesh.current.setMatrixAt(i, dummy.matrix);
    });
    cMesh.current.instanceMatrix.needsUpdate = true;
    rings.current.forEach((r, i) => {
      if (!r) return;
      const k = (time * 0.6 + i * 0.27) % 1;
      r.scale.setScalar(0.2 + k * 1.1);
      r.material.opacity = (1 - k) * 0.7;
    });
    if (beacon.current) beacon.current.rotation.y = time * 0.8;
  });

  return (
    <>
      <Lights />
      <PointerTilt strength={0.28} pitch={0.62} yaw={0.6}>
        <group position={[0, -0.6, 0]}>
          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.005, 0]}>
            <planeGeometry args={[span + 0.4, span + 0.4]} />
            <meshStandardMaterial color={p.ground} roughness={1} />
          </mesh>
          {/* road markings */}
          {lanes.map((l, i) => (
            <mesh key={i} rotation={[-Math.PI / 2, 0, l.axis === "x" ? 0 : Math.PI / 2]} position={l.axis === "x" ? [0, 0.004, l.c] : [l.c, 0.004, 0]}>
              <planeGeometry args={[span, ROAD * 0.75]} />
              <meshStandardMaterial color={p.inkMuted} transparent opacity={0.22} />
            </mesh>
          ))}
          <instancedMesh ref={bMesh} args={[undefined, undefined, buildings.length]}>
            <boxGeometry args={[1, 1, 1]} />
            <meshStandardMaterial roughness={0.6} />
          </instancedMesh>
          <instancedMesh ref={cMesh} args={[undefined, undefined, CARS]}>
            <boxGeometry args={[0.16, 0.07, 0.08]} />
            <meshStandardMaterial emissiveIntensity={0.3} roughness={0.4} />
          </instancedMesh>
          {sensors.map((s, i) => (
            <mesh key={i} ref={(el) => { rings.current[i] = el; }} position={s} rotation={[-Math.PI / 2, 0, 0]}>
              <ringGeometry args={[0.18, 0.22, 32]} />
              <meshBasicMaterial color={p.jade} transparent opacity={0.6} side={THREE.DoubleSide} toneMapped={false} />
            </mesh>
          ))}
          {/* central data beacon: the unified city platform */}
          <group ref={beacon} position={[0, 0, 0]}>
            <mesh position={[0, 0.55, 0]}>
              <cylinderGeometry args={[0.05, 0.12, 1.1, 12]} />
              <meshStandardMaterial color={p.accent} emissive={p.accent} emissiveIntensity={0.4} />
            </mesh>
            <mesh position={[0, 1.2, 0]}>
              <octahedronGeometry args={[0.2, 0]} />
              <meshStandardMaterial color={p.saffron} emissive={p.saffron} emissiveIntensity={0.5} />
            </mesh>
          </group>
        </group>
      </PointerTilt>
    </>
  );
}
