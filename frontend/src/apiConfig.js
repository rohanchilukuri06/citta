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

// "citta-production.up.railway.app" without https:// would be fetched as a path on this site (→ 405 from Vercel)
const withScheme = (url) => (/^https?:\/\//i.test(url) ? url : `https://${url}`);

// Trailing slashes, and a /docs (Swagger page) or /api suffix copied along with the address, are removed
export const API_BASE_URL = withScheme((configured || "http://localhost:8000").trim())
  .replace(/\/+$/, "")
  .replace(/\/(docs|api)$/i, "");
