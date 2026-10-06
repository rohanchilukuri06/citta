// WhatsApp Marketing Platform — "Brand Messaging OS": one brand phone broadcasts message bubbles along arcs to a
// ring of customers (lakhs of messages, segmented); each recipient lights up when its message is delivered.
import { useLayoutEffect, useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { usePalette, useClock, PointerTilt, Lights, seeded } from "@/three/core";

const RECIPIENTS = 30;
const BUBBLES = 36;
const RING = 3.1;

export default function Broadcast() {
  const p = usePalette();
  const t = useClock();
  const people = useRef();
  const bubbles = useRef();
  const dummy = useMemo(() => new THREE.Object3D(), []);
  const col = useMemo(() => new THREE.Color(), []);
  const lit = useMemo(() => new Float32Array(RECIPIENTS), []);
  const accent = useMemo(() => new THREE.Color(p.accent), [p.accent]);

  const targets = useMemo(() => Array.from({ length: RECIPIENTS }, (_, i) => {
    const a = (i / RECIPIENTS) * Math.PI * 2;
    const r = RING + (i % 3) * 0.35;
    return new THREE.Vector3(Math.cos(a) * r, Math.sin(i * 1.7) * 0.35 - 0.35, Math.sin(a) * r);
  }), []);
  const flights = useMemo(() => {
    const rnd = seeded(5);
    return Array.from({ length: BUBBLES }, (_, i) => ({ target: i % RECIPIENTS, phase: rnd(), speed: 0.32 + rnd() * 0.18 }));
  }, []);
  const origin = useMemo(() => new THREE.Vector3(0, 0.75, 0), []);
  const curve = useMemo(() => new THREE.QuadraticBezierCurve3(new THREE.Vector3(), new THREE.Vector3(), new THREE.Vector3()), []);

  useLayoutEffect(() => {
    targets.forEach((v, i) => {
      dummy.position.copy(v);
      dummy.scale.setScalar(1);
      dummy.updateMatrix();
      people.current.setMatrixAt(i, dummy.matrix);
      people.current.setColorAt(i, col.set(p.inkMuted));
    });
    people.current.instanceMatrix.needsUpdate = true;
  }, [targets, dummy, col, p]);

  useFrame((_, delta) => {
    const time = t.current;
    flights.forEach((f, i) => {
      const u = (f.phase + time * f.speed) % 1;
      const end = targets[f.target];
      curve.v0.copy(origin);
      curve.v1.set(end.x * 0.5, 2.4, end.z * 0.5);
      curve.v2.copy(end);
      curve.getPoint(u, dummy.position);
      const s = u < 0.1 ? u / 0.1 : u > 0.92 ? (1 - u) / 0.08 : 1;
      dummy.scale.set(0.26 * s, 0.17 * s, 0.06 * s);
      dummy.lookAt(0, dummy.position.y, 0);
      dummy.updateMatrix();
      bubbles.current.setMatrixAt(i, dummy.matrix);
      if (u > 0.95) lit[f.target] = 1;
    });
    bubbles.current.instanceMatrix.needsUpdate = true;
    const fade = Math.exp(-delta * 1.4);
    targets.forEach((v, i) => {
      lit[i] *= fade;
      dummy.position.copy(v);
      dummy.rotation.set(0, 0, 0);
      dummy.scale.setScalar(1 + lit[i] * 0.6);
      dummy.updateMatrix();
      people.current.setMatrixAt(i, dummy.matrix);
      people.current.setColorAt(i, col.set(p.inkMuted).lerp(accent, Math.min(1, lit[i] * 1.4)));
    });
    people.current.instanceMatrix.needsUpdate = true;
    if (people.current.instanceColor) people.current.instanceColor.needsUpdate = true;
  });

  return (
    <>
      <Lights />
      <PointerTilt strength={0.25} pitch={0.32}>
        {/* the brand's phone */}
        <group position={[0, 0.1, 0]}>
          <mesh>
            <boxGeometry args={[0.9, 1.7, 0.12]} />
            <meshStandardMaterial color={p.dark ? p.solid : p.ink} roughness={0.3} metalness={0.3} />
          </mesh>
          <mesh position={[0, 0, 0.065]}>
            <planeGeometry args={[0.78, 1.52]} />
            <meshStandardMaterial color={p.accent} emissive={p.accent} emissiveIntensity={0.45} />
          </mesh>
          {[0.42, 0.12, -0.18].map((y, k) => (
            <mesh key={k} position={[k % 2 ? 0.1 : -0.1, y, 0.075]}>
              <boxGeometry args={[0.5, 0.16, 0.01]} />
              <meshStandardMaterial color={p.solid} />
            </mesh>
          ))}
        </group>
        {/* customers */}
        <instancedMesh ref={people} args={[undefined, undefined, RECIPIENTS]}>
          <sphereGeometry args={[0.13, 16, 16]} />
          <meshStandardMaterial roughness={0.4} />
        </instancedMesh>
        {/* message bubbles */}
        <instancedMesh ref={bubbles} args={[undefined, undefined, BUBBLES]}>
          <boxGeometry args={[1, 1, 1]} />
          <meshStandardMaterial color={p.accent} emissive={p.accent} emissiveIntensity={0.2} roughness={0.3} />
        </instancedMesh>
        {/* audience ring */}
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.75, 0]}>
          <ringGeometry args={[RING - 0.25, RING + 0.95, 72]} />
          <meshBasicMaterial color={p.accent} transparent opacity={0.07} side={THREE.DoubleSide} />
        </mesh>
      </PointerTilt>
    </>
  );
}
