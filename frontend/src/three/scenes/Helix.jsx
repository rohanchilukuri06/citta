// Pharma & Healthcare OS — "AI-Powered Quality, Compliance & Release Intelligence": a molecular double helix, with
// batch vials orbiting it. A scanner ring sweeps the batch; each vial turns from pending (saffron) to released (jade)
// as it passes review — faster, reliable batch decisions.
import { useLayoutEffect, useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { usePalette, useClock, PointerTilt, Lights } from "@/three/core";

const STEPS = 34;
const VIALS = 12;
const HEIGHT = 4.2;

export default function Helix() {
  const p = usePalette();
  const t = useClock();
  const group = useRef();
  const atoms = useRef();
  const rungs = useRef();
  const vials = useRef();
  const scanner = useRef();
  const dummy = useMemo(() => new THREE.Object3D(), []);
  const col = useMemo(() => new THREE.Color(), []);
  const up = useMemo(() => new THREE.Vector3(0, 1, 0), []);

  useLayoutEffect(() => {
    for (let i = 0; i < STEPS; i += 1) {
      const y = (i / (STEPS - 1) - 0.5) * HEIGHT;
      const a = i * 0.42;
      const A = new THREE.Vector3(Math.cos(a) * 0.85, y, Math.sin(a) * 0.85);
      const B = new THREE.Vector3(Math.cos(a + Math.PI) * 0.85, y, Math.sin(a + Math.PI) * 0.85);
      [A, B].forEach((v, k) => {
        dummy.position.copy(v);
        dummy.scale.setScalar(1);
        dummy.quaternion.identity();
        dummy.updateMatrix();
        atoms.current.setMatrixAt(i * 2 + k, dummy.matrix);
        atoms.current.setColorAt(i * 2 + k, col.set(k ? p.accent : p.sky));
      });
      const mid = A.clone().add(B).multiplyScalar(0.5);
      const dir = B.clone().sub(A);
      dummy.position.copy(mid);
      dummy.quaternion.setFromUnitVectors(up, dir.clone().normalize());
      dummy.scale.set(1, dir.length(), 1);
      dummy.updateMatrix();
      rungs.current.setMatrixAt(i, dummy.matrix);
    }
    atoms.current.instanceMatrix.needsUpdate = true;
    if (atoms.current.instanceColor) atoms.current.instanceColor.needsUpdate = true;
    rungs.current.instanceMatrix.needsUpdate = true;
  }, [p, dummy, col, up]);

  useFrame(() => {
    const time = t.current;
    if (group.current) group.current.rotation.y = time * 0.35;
    const scanY = Math.sin(time * 0.8) * (HEIGHT / 2 - 0.3);
    if (scanner.current) scanner.current.position.y = scanY;
    for (let i = 0; i < VIALS; i += 1) {
      const a = (i / VIALS) * Math.PI * 2 - time * 0.25;
      const y = ((i % 4) - 1.5) * 0.95;
      dummy.position.set(Math.cos(a) * 2.2, y, Math.sin(a) * 2.2);
      dummy.quaternion.identity();
      dummy.rotation.set(0, 0, 0.25);
      dummy.scale.setScalar(1);
      dummy.updateMatrix();
      vials.current.setMatrixAt(i, dummy.matrix);
      // released once the scanner has passed this vial's level on its current sweep
      const released = Math.cos(time * 0.8) > 0 ? scanY > y : scanY < y;
      vials.current.setColorAt(i, col.set(released ? p.jade : p.saffron));
    }
    vials.current.instanceMatrix.needsUpdate = true;
    if (vials.current.instanceColor) vials.current.instanceColor.needsUpdate = true;
  });

  return (
    <>
      <Lights />
      <PointerTilt strength={0.3} pitch={0.12}>
        <group ref={group}>
          <instancedMesh ref={atoms} args={[undefined, undefined, STEPS * 2]}>
            <sphereGeometry args={[0.13, 16, 16]} />
            <meshStandardMaterial roughness={0.3} />
          </instancedMesh>
          <instancedMesh ref={rungs} args={[undefined, undefined, STEPS]}>
            <cylinderGeometry args={[0.025, 0.025, 1, 8]} />
            <meshStandardMaterial color={p.inkMuted} transparent opacity={0.7} />
          </instancedMesh>
        </group>
        <instancedMesh ref={vials} args={[undefined, undefined, VIALS]}>
          <capsuleGeometry args={[0.12, 0.34, 6, 14]} />
          <meshStandardMaterial roughness={0.25} />
        </instancedMesh>
        <mesh ref={scanner} rotation={[Math.PI / 2, 0, 0]}>
          <torusGeometry args={[2.2, 0.02, 8, 120]} />
          <meshBasicMaterial color={p.jade} toneMapped={false} />
        </mesh>
      </PointerTilt>
    </>
  );
}
