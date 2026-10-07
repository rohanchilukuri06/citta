// Backend address for the chat widget, contact form and admin console.
// Production (Vercel): set REACT_APP_BACKEND_URL in the project's Environment Variables, e.g. your Railway domain.
// The other names are accepted for compatibility with older deployments.
const configured =
  process.env.REACT_APP_API_URL ||
  process.env.REACT_APP_BACKEND_URL ||
  process.env.VITE_API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.API_BASE_URL ||
  "";

if (!configured && process.env.NODE_ENV === "production") {
  // eslint-disable-next-line no-console
  console.error("CittaAI: REACT_APP_BACKEND_URL is not set for this build — the chat and contact form cannot reach the backend.");
}

export const API_BASE_URL = (configured || "http://localhost:8000").replace(/\/$/, "");
