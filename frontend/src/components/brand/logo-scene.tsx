"use client";

import { Canvas } from "@react-three/fiber";
import { SanadLogoMark3D, NAVY, GOLD } from "@/components/three/shapes";

interface LogoSceneProps {
  variant?: "full" | "knot" | "sphere";
}

function LogoLights() {
  return (
    <>
      <ambientLight intensity={0.6} />
      <directionalLight position={[2, 2, 3]} intensity={1} color="#f5f0e8" />
      <pointLight position={[-2, 1, 2]} intensity={0.5} color={NAVY} />
      <pointLight position={[2, -1, 2]} intensity={0.4} color={GOLD} />
    </>
  );
}

export function LogoScene() {
  return (
    <Canvas
      camera={{ position: [0, 0, 3.2], fov: 48 }}
      dpr={[1, 1.5]}
      gl={{ antialias: true, alpha: true }}
      style={{ background: "transparent" }}
    >
      <LogoLights />
      <SanadLogoMark3D />
    </Canvas>
  );
}
