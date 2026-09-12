"use client";

import { useRef, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import { Float } from "@react-three/drei";
import * as THREE from "three";

export const NAVY = "#0B1A4D";
export const GOLD = "#D2B589";
export const IVORY = "#FDFFFF";
export const CREAM = "#F5F0E8";

/** @deprecated use NAVY */
export const GREEN = NAVY;

type Vec3 = [number, number, number];

/** Balance de la justice — animation 3D captivante */
export function JusticeScales3D({
  scale = 1,
  position = [0, 0, 0] as Vec3,
}: {
  scale?: number;
  position?: Vec3;
}) {
  const beam = useRef<THREE.Group>(null);
  const leftPan = useRef<THREE.Mesh>(null);
  const rightPan = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    const sway = Math.sin(t * 0.8) * 0.12;
    if (beam.current) {
      beam.current.rotation.z = sway;
    }
    if (leftPan.current) {
      leftPan.current.position.y = -0.55 - Math.abs(sway) * 0.3;
    }
    if (rightPan.current) {
      rightPan.current.position.y = -0.55 + Math.abs(sway) * 0.3;
    }
  });

  return (
    <group position={position} scale={scale}>
      {/* Pilier */}
      <mesh position={[0, -0.8, 0]}>
        <cylinderGeometry args={[0.06, 0.1, 1.6, 16]} />
        <meshStandardMaterial color={GOLD} metalness={0.9} roughness={0.1} emissive={GOLD} emissiveIntensity={0.08} />
      </mesh>
      {/* Base */}
      <mesh position={[0, -1.55, 0]}>
        <cylinderGeometry args={[0.5, 0.55, 0.12, 24]} />
        <meshStandardMaterial color={NAVY} metalness={0.7} roughness={0.2} />
      </mesh>
      {/* Barre oscillante */}
      <group ref={beam} position={[0, 0.1, 0]}>
        <mesh>
          <boxGeometry args={[2.4, 0.06, 0.06]} />
          <meshStandardMaterial color={GOLD} metalness={0.95} roughness={0.05} emissive={GOLD} emissiveIntensity={0.12} />
        </mesh>
        {/* Chaînes + plateaux */}
        <group position={[-1.1, -0.3, 0]}>
          <mesh position={[0, -0.2, 0]}>
            <cylinderGeometry args={[0.015, 0.015, 0.4, 8]} />
            <meshStandardMaterial color={GOLD} metalness={0.8} roughness={0.15} />
          </mesh>
          <mesh ref={leftPan} position={[0, -0.55, 0]}>
            <cylinderGeometry args={[0.35, 0.38, 0.06, 24]} />
            <meshStandardMaterial color={IVORY} metalness={0.5} roughness={0.3} transparent opacity={0.9} />
          </mesh>
        </group>
        <group position={[1.1, -0.3, 0]}>
          <mesh position={[0, -0.2, 0]}>
            <cylinderGeometry args={[0.015, 0.015, 0.4, 8]} />
            <meshStandardMaterial color={GOLD} metalness={0.8} roughness={0.15} />
          </mesh>
          <mesh ref={rightPan} position={[0, -0.55, 0]}>
            <cylinderGeometry args={[0.35, 0.38, 0.06, 24]} />
            <meshStandardMaterial color={IVORY} metalness={0.5} roughness={0.3} transparent opacity={0.9} />
          </mesh>
        </group>
      </group>
    </group>
  );
}

/** Livre de loi 3D */
export function LawBook3D({
  scale = 1,
  position = [0, 0, 0] as Vec3,
}: {
  scale?: number;
  position?: Vec3;
}) {
  const ref = useRef<THREE.Group>(null);
  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.y = state.clock.elapsedTime * 0.25;
      ref.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.4) * 0.08;
    }
  });

  return (
    <group ref={ref} position={position} scale={scale}>
      <mesh position={[0, 0, 0]} rotation={[0, 0.3, 0]}>
        <boxGeometry args={[1.2, 0.15, 0.9]} />
        <meshStandardMaterial color={NAVY} metalness={0.4} roughness={0.35} />
      </mesh>
      <mesh position={[0.02, 0.08, 0.02]} rotation={[0, 0.3, 0]}>
        <boxGeometry args={[1.1, 0.02, 0.82]} />
        <meshStandardMaterial color={GOLD} metalness={0.85} roughness={0.1} emissive={GOLD} emissiveIntensity={0.1} />
      </mesh>
    </group>
  );
}

export function createStarShape(r = 0.55) {
  const s = new THREE.Shape();
  for (let i = 0; i < 10; i++) {
    const angle = (i * Math.PI) / 5 - Math.PI / 2;
    const radius = i % 2 === 0 ? r : r * 0.42;
    const x = Math.cos(angle) * radius;
    const y = Math.sin(angle) * radius;
    if (i === 0) s.moveTo(x, y);
    else s.lineTo(x, y);
  }
  s.closePath();
  return s;
}

export function MoroccanStar3D({ scale = 1, position = [0, 0, 0] as Vec3 }) {
  const ref = useRef<THREE.Group>(null);
  const shape = useMemo(() => createStarShape(), []);
  const gray = "#B0B8C8";

  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.z = state.clock.elapsedTime * 0.06;
      const pulse = 0.35 + Math.sin(state.clock.elapsedTime * 2.2) * 0.25;
      const mat = (ref.current.children[0] as THREE.Mesh | undefined)?.material as
        | THREE.MeshStandardMaterial
        | undefined;
      if (mat) mat.emissiveIntensity = pulse;
    }
  });

  return (
    <group ref={ref} position={position} scale={scale}>
      <mesh>
        <extrudeGeometry args={[shape, { depth: 0.05, bevelEnabled: true, bevelSize: 0.01, bevelThickness: 0.01 }]} />
        <meshStandardMaterial
          color={gray}
          metalness={0.85}
          roughness={0.2}
          emissive={gray}
          emissiveIntensity={0.4}
          transparent
          opacity={0.85}
        />
      </mesh>
    </group>
  );
}

/** Logo mark 3D (balance miniature) */
export function SanadLogoMark3D() {
  return (
    <Float speed={1.2} rotationIntensity={0.1} floatIntensity={0.25}>
      <JusticeScales3D scale={0.55} />
    </Float>
  );
}
