// Development-only: every topic scene on one page, for visual review (/__scenes?set=1|2). Not linked anywhere.
import { useSearchParams } from "react-router-dom";
import Scene from "@/three/Scene";
import ThemeToggle from "@/components/ThemeToggle";

const SCENE_NAMES = ["neural", "fragments", "stack", "broadcast", "creators", "commerce", "skyline", "helix", "city", "learning", "modules", "pipeline", "agents", "roadmap", "funnel", "trophy", "globe", "growth"];

export default function SceneGallery() {
  const [params] = useSearchParams();
  const names = SCENE_NAMES;
  const half = Math.ceil(names.length / 2);
  const set = params.get("set") === "2" ? names.slice(half) : names.slice(0, half);
  return (
    <div className="container-x pt-6 pb-10">
      <div className="flex justify-end mb-3"><ThemeToggle /></div>
      <div className="grid grid-cols-3 gap-4">
        {set.map((n) => (
          <div key={n} className="card p-3">
            <div className="font-mono text-xs text-ink-muted mb-2">{n}</div>
            <Scene name={n} className="h-[300px] rounded-2xl" />
          </div>
        ))}
      </div>
    </div>
  );
}
