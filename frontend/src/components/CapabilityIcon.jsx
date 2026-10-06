import {
  MessageSquare, Send, Layers, Users, Zap, Inbox, LibraryBig, LineChart, Plug, Shield, HeartHandshake,
  Search, Radio, Wallet, ShoppingBag, Boxes, ClipboardList, UserRound, Bot, Mic, Truck, Home,
  UserPlus, GitBranch, Handshake, Activity, FolderLock, Bell, PiggyBank,
  ClipboardCheck, FileText, Beaker, ShieldCheck, Building, Route, Sun, Layers3, GraduationCap,
  Code2, Video, BookOpen, Database, BrainCircuit, PhoneCall, Network, FileSearch, Waypoints, Cpu, Sparkles
} from "lucide-react";

const map = new Map([
  ["Brand Onboarding", HeartHandshake],
  ["Message Types", MessageSquare],
  ["Mass Scale Broadcasting", Radio],
  ["Segmentation & Targeting", Layers],
  ["Automation & Journeys", Zap],
  ["Two-Way Inbox", Inbox],
  ["Templates Management", LibraryBig],
  ["Analytics & Reporting", LineChart],
  ["Integrations", Plug],
  ["Compliance & Safety", Shield],
  ["Managed Services", Users],

  ["Influencer Discovery", Search],
  ["Communication & Hub", MessageSquare],
  ["Campaign Management", ClipboardList],
  ["Live Tracking", Activity],
  ["Analytics & ROI", LineChart],
  ["Affiliate Marketing", Send],
  ["Payments & Compliance", Wallet],

  ["Product & Inventory", Boxes],
  ["Order Lifecycle", ShoppingBag],
  ["CRM & Retention", UserRound],
  ["Marketing Workflows", Zap],
  ["Conversational AI", Bot],
  ["Voice Agents", Mic],
  ["Data Analytics", LineChart],
  ["Supply Chain Intel", Truck],

  ["Property Listings Management", Home],
  ["Lead Management", UserPlus],
  ["Customer Journey Tracking", GitBranch],
  ["Partner Ecosystem", Handshake],
  ["Project Analytics", Activity],
  ["Document Vault", FolderLock],
  ["Automated Communication", Bell],
  ["Finance Tracking", PiggyBank],

  ["Quality Dashboards", ClipboardCheck],
  ["Batch Records Review Tool", FileText],
  ["Protocol Preparation Tools", Beaker],
  ["CPV Tool", Activity],
  ["APQR Reporting Tool", LineChart],
  ["Assessment Tool", ShieldCheck],

  ["Unified City Data Platform", Building],
  ["Smart Mobility Intelligence", Route],
  ["Utility & Resource Management", Sun],

  ["College LMS", GraduationCap],
  ["Groups & Cohort Management", Users],
  ["Course Learning Experience", BookOpen],
  ["Test Series Platform", ClipboardList],
  ["Coding LMS", Code2],
  ["Video LMS", Video],

  ["RAG & Agentic Applications", BrainCircuit],
  ["Conversational AI ", Bot],
  ["Voice Agents ", PhoneCall],
  ["Multi-Agent Systems", Network],
  ["Document AI", FileSearch],
  ["Data Engineering & Analytics", Database],
  ["Agentic Knowledge Graph", Waypoints],
  ["Database Agents", Database],
  ["Fine-Tuning & RL", Cpu],
]);

export function iconFor(label) {
  return map.get(label) || map.get(`${label} `) || Sparkles;
}

export default function CapabilityIcon({ label, className = "" }) {
  const Icon = iconFor(label);
  return (
    <div className={`icon-tile ${className}`}>
      <Icon className="h-[18px] w-[18px]" />
    </div>
  );
}
