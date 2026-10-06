import { lazy, Suspense } from "react";

// three.js + react-three-fiber load in their own chunk, so pages render their text first and the 3D streams in.
const SceneImpl = lazy(() => import("@/three/SceneImpl"));

/**
 * <Scene name="helix" accent="sky" className="h-[420px]" />
 * A registered topic scene (see three/scenes/index.js). Changing `name` swaps the scene inside the same canvas.
 */
export default function Scene(props) {
  const { className = "", overlay = null } = props;
  return (
    <Suspense fallback={<div className={`scene-frame ${className}`}><div className="scene-fallback" />{overlay}</div>}>
      <SceneImpl {...props} />
    </Suspense>
  );
}
