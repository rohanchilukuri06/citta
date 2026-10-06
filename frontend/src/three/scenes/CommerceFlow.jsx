// E-Commerce OS — "Run everything, from storefront to supply chain to support": orders travel a loop through four
// stations (storefront → warehouse → delivery → AI support) on one platform base.
import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { usePalette, useClock, PointerTilt, Lights } from "@/three/core";

const PACKAGES = 18;

function Storefront({ p }) {
  return (
    <group>
      <mesh position={[0, 0.35, 0]}><boxGeometry args={[0.9, 0.7, 0.7]} /><meshStandardMaterial color={p.solid} roughness={0.5} /></mesh>
      <mesh position={[0, 0.78, 0.18]} rotation={[0.35, 0, 0]}><boxGeometry args={[1.0, 0.06, 0.55]} /><meshStandardMaterial color={p.coral} /></mesh>
      <mesh position={[0, 0.3, 0.36]}><planeGeometry args={[0.5, 0.42]} /><meshStandardMaterial color={p.accent} emissive={p.accent} emissiveIntensity={0.35} /></mesh>
    </group>
  );
}
function Warehouse({ p }) {
  return (
    <group>
      <mesh position={[0, 0.32, 0]}><boxGeometry args={[1.1, 0.64, 0.8]} /><meshStandardMaterial color={p.solid} /></mesh>
      <mesh position={[0, 0.64, 0]} rotation={[0, 0, Math.PI / 4]}><boxGeometry args={[0.78, 0.78, 0.82]} /><meshStandardMaterial color={p.sky} /></mesh>
      {[-0.25, 0.05, 0.35].map((x) => <mesh key={x} position={[x - 0.05, 0.12, 0.42]}><boxGeometry args={[0.2, 0.2, 0.05]} /><meshStandardMaterial color={p.saffron} /></mesh>)}
    </group>
  );
}
function Truck({ p }) {
  return (
    <group>
      <mesh position={[-0.12, 0.32, 0]}><boxGeometry args={[0.75, 0.5, 0.5]} /><meshStandardMaterial color={p.solid} /></mesh>
      <mesh position={[0.4, 0.24, 0]}><boxGeometry args={[0.32, 0.34, 0.48]} /><meshStandardMaterial color={p.jade} /></mesh>
      {[-0.35, 0.15, 0.42].map((x) => <mesh key={x} position={[x, 0.06, 0.26]} rotation={[Math.PI / 2, 0, 0]}><cylinderGeometry args={[0.09, 0.09, 0.06, 16]} /><meshStandardMaterial color={p.ink} /></mesh>)}
    </group>
  );
}
function Support({ p }) {
  return (
    <group>
      <mesh position={[0, 0.42, 0]}><sphereGeometry args={[0.32, 24, 24]} /><meshStandardMaterial color={p.accent} emissive={p.accent} emissiveIntensity={0.35} /></mesh>
      <mesh position={[0, 0.42, 0]} rotation={[Math.PI / 2, 0, 0]}><torusGeometry args={[0.46, 0.035, 10, 40]} /><meshStandardMaterial color={p.saffron} /></mesh>
    </group>
  );
}

export default function CommerceFlow() {
  const p = usePalette();
  const t = useClock();
  const curve = useMemo(() => new THREE.CatmullRomCurve3([
    new THREE.Vector3(-2.4, 0, -1.3), new THREE.Vector3(0, 0, -1.9), new THREE.Vector3(2.4, 0, -1.3),
    new THREE.Vector3(2.7, 0, 0.6), new THREE.Vector3(0, 0, 1.6), new THREE.Vector3(-2.7, 0, 0.6),
  ], true, "catmullrom", 0.5), []);
  const track = useMemo(() => new THREE.TubeGeometry(curve, 160, 0.07, 8, true), [curve]);
  const boxes = useRef();
  const dummy = useMemo(() => new THREE.Object3D(), []);
  const tangent = useMemo(() => new THREE.Vector3(), []);
  const stations = [
    { u: 0.0, C: Storefront }, { u: 0.33, C: Warehouse }, { u: 0.55, C: Truck }, { u: 0.8, C: Support },
  ].map((s) => ({ ...s, pos: curve.getPointAt(s.u) }));

  useFrame(() => {
    const time = t.current;
    for (let i = 0; i < PACKAGES; i += 1) {
      const u = (i / PACKAGES + time * 0.045) % 1;
      curve.getPointAt(u, dummy.position);
      curve.getTangentAt(u, tangent);
      dummy.position.y = 0.17;
      dummy.rotation.set(0, Math.atan2(tangent.x, tangent.z), 0);
      dummy.scale.setScalar(1);
      dummy.updateMatrix();
      boxes.current.setMatrixAt(i, dummy.matrix);
    }
    boxes.current.instanceMatrix.needsUpdate = true;
  });

  return (
    <>
      <Lights />
      <PointerTilt strength={0.25} pitch={0.55} yaw={0.25}>
        <group position={[0, -0.5, 0]}>
          {/* the one platform everything runs on */}
          <mesh position={[0, -0.08, 0]}>
            <boxGeometry args={[6.6, 0.12, 4.6]} />
            <meshStandardMaterial color={p.ground} roughness={0.8} />
          </mesh>
          <mesh geometry={track}>
            <meshStandardMaterial color={p.inkMuted} roughness={0.6} />
          </mesh>
          <instancedMesh ref={boxes} args={[undefined, undefined, PACKAGES]}>
            <boxGeometry args={[0.22, 0.2, 0.22]} />
            <meshStandardMaterial color={p.saffron} roughness={0.5} />
          </instancedMesh>
          {stations.map(({ C, pos, u }) => (
            <group key={u} position={[pos.x * 1.32, 0, pos.z * 1.32]}>
              <C p={p} />
            </group>
          ))}
        </group>
      </PointerTilt>
    </>
  );
}
