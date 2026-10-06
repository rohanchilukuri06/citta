// Contact — "Come say hello at our office": a dotted globe turned to India, a pulsing pin on the Hyderabad
// headquarters (HITEC City), and signals arcing out to the world — reach the team from anywhere.
import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { usePalette, useClock, PointerTilt, Lights, fibonacciSphere } from "@/three/core";

const R = 2;
const HYD = { lat: 17.44, lon: 78.38 };
const DESTS = [
  { lat: 25.2, lon: 55.27 }, { lat: 51.5, lon: -0.12 }, { lat: 1.35, lon: 103.8 }, { lat: 40.7, lon: -74.0 },
  { lat: -33.9, lon: 151.2 }, { lat: 35.7, lon: 139.7 }, { lat: 28.6, lon: 77.2 }, { lat: 19.07, lon: 72.87 },
];

function toVec(lat, lon, r = R) {
  const phi = (90 - lat) * (Math.PI / 180);
  const th = (lon + 180) * (Math.PI / 180);
  return new THREE.Vector3(-r * Math.sin(phi) * Math.cos(th), r * Math.cos(phi), r * Math.sin(phi) * Math.sin(th));
}

export default function Globe() {
  const p = usePalette();
  const t = useClock();
  const globe = useRef();
  const ring = useRef();
  const pulses = useRef([]);
  const dots = useMemo(() => {
    const pts = fibonacciSphere(1400, R);
    const arr = new Float32Array(pts.length * 3);
    pts.forEach((v, i) => arr.set([v.x, v.y, v.z], i * 3));
    return arr;
  }, []);
  const hq = useMemo(() => toVec(HYD.lat, HYD.lon), []);
  const arcs = useMemo(() => DESTS.map((d) => {
    const end = toVec(d.lat, d.lon);
    const mid = hq.clone().add(end).multiplyScalar(0.5);
    mid.setLength(R + 0.35 + hq.distanceTo(end) * 0.35);
    return new THREE.QuadraticBezierCurve3(hq, mid, end);
  }), [hq]);
  const arcGeos = useMemo(() => arcs.map((c) => new THREE.BufferGeometry().setFromPoints(c.getPoints(48))), [arcs]);
  // rotate so India faces the camera
  const facing = useMemo(() => {
    const q = new THREE.Quaternion().setFromUnitVectors(hq.clone().normalize(), new THREE.Vector3(0.25, 0.32, 1).normalize());
    return new THREE.Euler().setFromQuaternion(q);
  }, [hq]);

  useFrame(() => {
    const time = t.current;
    if (globe.current) globe.current.rotation.y = Math.sin(time * 0.25) * 0.35;
    if (ring.current) {
      const k = (time * 0.7) % 1;
      ring.current.scale.setScalar(0.4 + k * 1.6);
      ring.current.material.opacity = 1 - k;
    }
    pulses.current.forEach((m, i) => {
      if (!m) return;
      const u = (time * 0.3 + i / arcs.length) % 1;
      arcs[i].getPoint(u, m.position);
    });
  });

  return (
    <>
      <Lights />
      <PointerTilt strength={0.3}>
        <group ref={globe}>
          <group rotation={facing}>
            <mesh>
              <sphereGeometry args={[R * 0.985, 48, 48]} />
              <meshStandardMaterial color={p.dark ? p.ground : p.surface} transparent opacity={p.dark ? 0.85 : 0.75} roughness={0.9} />
            </mesh>
            <points>
              <bufferGeometry>
                <bufferAttribute attach="attributes-position" args={[dots, 3]} />
              </bufferGeometry>
              <pointsMaterial color={p.accent} size={0.035} transparent opacity={0.65} />
            </points>
            {arcGeos.map((g, i) => (
              <line key={i} geometry={g}>
                <lineBasicMaterial color={p.jade} transparent opacity={0.55} />
              </line>
            ))}
            {arcs.map((_, i) => (
              <mesh key={i} ref={(el) => { pulses.current[i] = el; }}>
                <sphereGeometry args={[0.045, 10, 10]} />
                <meshBasicMaterial color={p.saffron} toneMapped={false} />
              </mesh>
            ))}
            {/* Hyderabad HQ pin */}
            <group position={hq} quaternion={new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), hq.clone().normalize())}>
              <mesh position={[0, 0.22, 0]}>
                <cylinderGeometry args={[0.018, 0.018, 0.44, 8]} />
                <meshBasicMaterial color={p.coral} />
              </mesh>
              <mesh position={[0, 0.48, 0]}>
                <sphereGeometry args={[0.1, 16, 16]} />
                <meshStandardMaterial color={p.coral} emissive={p.coral} emissiveIntensity={0.6} />
              </mesh>
              <mesh ref={ring} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, 0]}>
                <ringGeometry args={[0.12, 0.16, 32]} />
                <meshBasicMaterial color={p.coral} transparent side={THREE.DoubleSide} toneMapped={false} />
              </mesh>
            </group>
          </group>
        </group>
      </PointerTilt>
    </>
  );
}
