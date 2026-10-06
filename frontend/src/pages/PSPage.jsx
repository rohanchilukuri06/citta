import { useParams, Navigate } from "react-router-dom";
import { PAGE_CONFIGS } from "@/data/content";
import {
  PSHero, PSStakeholders, PSCapabilities, PSBestOutcomes, PSWhyGrid, PSClosing,
} from "@/components/PSSections";

export default function PSPage({ kind }) {
  const { slug } = useParams();
  const cfg = PAGE_CONFIGS[slug];

  if (!cfg) return <Navigate to="/" replace />;
  if (kind && cfg.kind !== kind) return <Navigate to={`/${cfg.kind}s/${cfg.slug}`} replace />;

  const backTo = cfg.kind === "product" ? "/#products" : "/#solutions";
  const backLabel = cfg.kind === "product" ? "Back to products" : "Back to solutions";

  return (
    // data-accent recolours the whole page (and its 3D scene) with this product's accent, in both themes
    <div data-testid={`${cfg.kind}-page`} data-slug={cfg.slug} data-accent={cfg.accent}>
      <PSHero cfg={cfg} backTo={backTo} backLabel={backLabel} />
      {cfg.stakeholders && <PSStakeholders stakeholders={cfg.stakeholders} />}
      <PSCapabilities cfg={cfg} />
      {cfg.bestFor && <PSBestOutcomes bestFor={cfg.bestFor} outcomes={cfg.outcomes} />}
      {cfg.whyGrid && <PSWhyGrid cfg={cfg} />}
      <PSClosing cfg={cfg} />
    </div>
  );
}
