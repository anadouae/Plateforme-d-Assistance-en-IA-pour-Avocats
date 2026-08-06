"use client";

import { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Float, Stars, Sparkles } from "@react-three/drei";
import * as THREE from "three";
import { MoroccanStar3D, NAVY, GOLD, IVORY } from "@/components/three/shapes";

function ParticleField() {
  return (
    <>
      <Sparkles count={160} scale={14} size={1.1} speed={0.4} color="#A8B0C0" opacity={0.55} />
      <Sparkles count={100} scale={11} size={0.8} speed={0.28} color="#C5CCD8" opacity={0.35} />
    </>
  );
}

function CursorStarField({ cursor }: { cursor: { x: number; y: number } }) {
  const group = useRef<THREE.Group>(null);
  useFrame(() => {
    if (group.current) {
      group.current.position.x = THREE.MathUtils.lerp(
        group.current.position.x,
        (cursor.x - 0.5) * 3.5,
        0.06,
      );
      group.current.position.y = THREE.MathUtils.lerp(
        group.current.position.y,
        -(cursor.y - 0.5) * 2.2,
        0.06,
      );
    }
  });

  const positions: [number, number, number][] = [
    [-2.5, 1.8, -1],
    [2.8, 1.2, -0.5],
    [-1.2, -1.5, 0.3],
    [3.2, -0.8, -1.2],
    [0.5, 2.2, -2],
    [-3, 0.2, 0.8],
    [1.5, -2, -0.8],
    [-0.8, 0.8, -1.5],
  ];

  return (
    <group ref={group}>
      {positions.map((pos, i) => (
        <Float key={i} speed={1.2 + i * 0.15} floatIntensity={0.6} rotationIntensity={0.3}>
          <MoroccanStar3D position={pos} scale={0.1 + (i % 3) * 0.04} />
        </Float>
      ))}
    </group>
  );
}

function SceneContent({ cursor }: { cursor: { x: number; y: number } }) {
  const starsRef = useRef<THREE.Group>(null);

  useFrame(() => {
    if (starsRef.current) {
      starsRef.current.rotation.y = THREE.MathUtils.lerp(
        starsRef.current.rotation.y,
        (cursor.x - 0.5) * 0.8,
        0.03,
      );
      starsRef.current.rotation.x = THREE.MathUtils.lerp(
        starsRef.current.rotation.x,
        -(cursor.y - 0.5) * 0.4,
        0.03,
      );
    }
  });

  return (
    <>
      <ambientLight intensity={0.4} />
      <directionalLight position={[5, 8, 5]} intensity={1.2} color={IVORY} />
      <pointLight position={[-5, 3, 2]} intensity={0.6} color={GOLD} />
      <pointLight position={[5, -2, 4]} intensity={0.4} color={NAVY} />

      <ParticleField />

      <group ref={starsRef}>
        <Stars radius={90} depth={50} count={1800} factor={3.5} saturation={0.2} fade speed={0.35} />
      </group>

      <CursorStarField cursor={cursor} />
    </>
  );
}

export function HeroScene({ cursor = { x: 0.5, y: 0.5 } }: { cursor?: { x: number; y: number } }) {
  return (
    <div className="absolute inset-0 z-0">
      <Canvas
        camera={{ position: [0, 0.5, 7], fov: 42 }}
        dpr={[1, 1.5]}
        gl={{ antialias: true, alpha: true }}
        style={{ background: `linear-gradient(180deg, ${NAVY} 0%, #1a223d 100%)` }}
      >
        <fog attach="fog" args={[NAVY, 10, 24]} />
        <SceneContent cursor={cursor} />
      </Canvas>
    </div>
  );
}
