// Scene registry: each topic's 3D scene, loaded on demand (a page only downloads the scenes it shows).
import { lazy } from "react";

export const SCENES = {
  neural:    { C: lazy(() => import("./NeuralCore")),     camera: { position: [0, 0, 8.2], fov: 42 }, label: "A knowledge network with signals travelling between nodes, a reasoning core, and AI agents orbiting it." },
  fragments: { C: lazy(() => import("./Fragments")),      camera: { position: [0, 0, 9], fov: 45 },   label: "Scattered data fragments assemble into one unified platform, then fall apart again." },
  stack:     { C: lazy(() => import("./AgentStack")),     camera: { position: [0, 0.4, 8], fov: 42 }, label: "Four stacked AI layers — RAG, chat, voice and video agents — with data rising through them." },
  broadcast: { C: lazy(() => import("./Broadcast")),      camera: { position: [0, 3.4, 10.5], fov: 45 }, label: "A brand's phone broadcasting WhatsApp messages along arcs to a ring of customers." },
  creators:  { C: lazy(() => import("./CreatorNetwork")), camera: { position: [0, 1.6, 7.4], fov: 45 }, label: "A brand hub with creators orbiting it; briefs go out and affiliate sales come back." },
  commerce:  { C: lazy(() => import("./CommerceFlow")),   camera: { position: [0, 3.6, 7.6], fov: 45 }, label: "Orders travel a loop from storefront to warehouse to delivery to AI support." },
  skyline:   { C: lazy(() => import("./Skyline")),        camera: { position: [0, 2.4, 7.6], fov: 45 }, label: "A district of towers rises; a featured project lights up floor by floor and lead pins drop on listings." },
  helix:     { C: lazy(() => import("./Helix")),          camera: { position: [0, 0.6, 8], fov: 45 }, label: "A molecular double helix with batch vials released as a scanner ring reviews them." },
  city:      { C: lazy(() => import("./CityGrid")),       camera: { position: [0, 4, 7], fov: 45 },    label: "A city grid with live traffic, pulsing IoT sensors and a central data beacon." },
  learning:  { C: lazy(() => import("./Learning")),       camera: { position: [0, 1.4, 6.2], fov: 45 }, label: "An open book with knowledge spiralling up to a graduation cap, circled by six learning modules." },
  modules:   { C: lazy(() => import("./ModuleGrid")),     camera: { position: [0, 2.2, 7], fov: 45 }, label: "Nine AI modules on one platform, promoted one by one from proof-of-concept to production." },
  pipeline:  { C: lazy(() => import("./Pipeline")),       camera: { position: [0, 0.8, 8], fov: 45 }, label: "Data from source systems flows through real-time pipelines into a cloud warehouse." },
  agents:    { C: lazy(() => import("./Agents")),         camera: { position: [0, 1.6, 8], fov: 45 }, label: "An orchestrator agent delegates tasks to specialist agents and receives their results." },
  roadmap:   { C: lazy(() => import("./Roadmap")),        camera: { position: [0, 1.6, 5.6], fov: 45 }, label: "A strategic roadmap as rising steps; a marker climbs and each milestone flag lights up." },
  funnel:    { C: lazy(() => import("./Funnel")),         camera: { position: [0, 1.6, 8], fov: 45 }, label: "Eight marketing channels circle a funnel; leads spiral down into conversions." },
  trophy:    { C: lazy(() => import("./Trophy")),         camera: { position: [0, 0.6, 7], fov: 42 }, label: "A turning award trophy with winner stars orbiting it." },
  globe:     { C: lazy(() => import("./Globe")),          camera: { position: [0, 0, 7], fov: 45 },    label: "A dotted globe with a pin on CittaAI's Hyderabad office and signals arcing to the world." },
  growth:    { C: lazy(() => import("./Growth")),         camera: { position: [0, 1.0, 6.2], fov: 45 }, label: "Bars climbing with a rising ROI line across three case studies." },
};
