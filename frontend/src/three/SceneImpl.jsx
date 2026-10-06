import { SceneCanvas, CameraRig } from "@/three/core";
import { SCENES } from "@/three/scenes";

/**
 * <Scene name="helix" accent="sky" className="h-[420px]" />
 * A registered topic scene in its frame. Changing `name` swaps the scene inside the same canvas.
 */
export default function Scene({ name, accent, className = "", overlay = null, props = {}, label }) {
  const s = SCENES[name];
  if (!s) return null;
  const { C } = s;
  return (
    <SceneCanvas className={className} camera={s.camera} label={label || s.label} overlay={overlay} accent={accent}>
      <CameraRig position={s.camera.position} fov={s.camera.fov} />
      <C key={name} {...props} />
    </SceneCanvas>
  );
}
