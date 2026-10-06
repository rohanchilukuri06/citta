// Data Engineering — "Building AI-Ready Data Platforms": source systems (databases, event streams, apps) feed
// real-time pipelines; records flow through a processing ring into a cloud warehouse / lake (the single source of truth).
import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { usePalette, useClock, PointerTilt, Lights } from "@/three/core";

const PER_PIPE = 22;

export default function Pipeline() {
  const p = usePalette();
  const t = useClock();
  const sources = useMemo(() => [new THREE.Vector3(-3.1, 1.3, -0.4), new THREE.Vector3(-3.3, 0, 0.5), new THREE.Vector3(-3.1, -1.3, -0.2)], []);
  const hubPos = useMemo(() => new THREE.Vector3(-0.6, 0, 0), []);
  const sink = useMemo(() => new THREE.Vector3(2.3, -0.1, 0), []);
  const curves = useMemo(() => sources.map((s) => new THREE.CatmullRomCurve3([
    s, new THREE.Vector3(s.x + 1.2, s.y * 0.8, s.z * 0.5), new THREE.Vector3(hubPos.x - 0.4, s.y * 0.25, 0), hubPos.clone(),
    new THREE.Vector3(hubPos.x + 1.1, s.y * 0.18, 0), new THREE.Vector3(sink.x - 0.9, sink.y + s.y * 0.1, 0),
  ])), [sources, hubPos, sink]);
  const tubes = useMemo(() => curves.map((c) => new THREE.TubeGeometry(c, 90, 0.045, 8, false)), [curves]);
  const count = curves.length * PER_PIPE;
  const dots = useRef();
  const ring = useRef();
  const dummy = useMemo(() => new THREE.Object3D(), []);

  useFrame(() => {
    const time = t.current;
    curves.forEach((c, ci) => {
      for (let k = 0; k < PER_PIPE; k += 1) {
        const u = (k / PER_PIPE + time * (0.16 + ci * 0.03)) % 1;
        c.getPointAt(u, dummy.position);
        dummy.scale.setScalar(u > 0.45 && u < 0.6 ? 1.6 : 1); // records are enriched at the processing ring
        dummy.updateMatrix();
        dots.current.setMatrixAt(ci * PER_PIPE + k, dummy.matrix);
      }
    });
    dots.current.instanceMatrix.needsUpdate = true;
    if (ring.current) ring.current.rotation.z = time * 0.9;
  });

  const sourceColours = [p.sky, p.coral, p.saffron];
  return (
    <>
      <Lights />
      <PointerTilt strength={0.28} pitch={0.25} yaw={-0.15}>
        {/* source systems */}
        {sources.map((s, i) => (
          <group key={i} position={s}>
            {[0, 0.16, 0.32].map((y) => (
              <mesh key={y} position={[0, y - 0.16, 0]}>
                <cylinderGeometry args={[0.32, 0.32, 0.12, 24]} />
                <meshStandardMaterial color={sourceColours[i]} roughness={0.4} />
              </mesh>
            ))}
          </group>
        ))}
        {tubes.map((g, i) => (
          <mesh key={i} geometry={g}>
            <meshStandardMaterial color={p.inkMuted} transparent opacity={0.35} />
          </mesh>
        ))}
        <instancedMesh ref={dots} args={[undefined, undefined, count]}>
          <sphereGeometry args={[0.06, 10, 10]} />
          <meshBasicMaterial color={p.accent} toneMapped={false} />
        </instancedMesh>
        {/* stream processing ring */}
        <mesh ref={ring} position={hubPos}>
          <torusGeometry args={[0.42, 0.06, 12, 48]} />
          <meshStandardMaterial color={p.jade} emissive={p.jade} emissiveIntensity={0.4} />
        </mesh>
        {/* warehouse / lake */}
        <group position={sink}>
          <mesh>
            <cylinderGeometry args={[0.95, 0.95, 1.5, 40, 1, true]} />
            <meshStandardMaterial color={p.accent} transparent opacity={0.22} side={THREE.DoubleSide} />
          </mesh>
          {[-0.5, -0.2, 0.1].map((y, k) => (
            <mesh key={y} position={[0, y, 0]}>
              <cylinderGeometry args={[0.9, 0.9, 0.22, 40]} />
              <meshStandardMaterial color={[p.accent, p.jade, p.sky][k]} roughness={0.35} transparent opacity={0.85} />
            </mesh>
          ))}
          <mesh position={[0, 0.75, 0]} rotation={[Math.PI / 2, 0, 0]}>
            <torusGeometry args={[0.95, 0.02, 8, 60]} />
            <meshBasicMaterial color={p.accent} />
          </mesh>
        </group>
      </PointerTilt>
    </>
  );
}
