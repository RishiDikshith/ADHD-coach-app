const configuredApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
const configuredWsUrl = process.env.NEXT_PUBLIC_WS_URL?.trim();

// Ensure frontend API calls always reach FastAPI on port 8000 and never accidentally
// fall back to relative URLs on port 3000 (e.g. http://localhost:3000/auth/...)
export const API_URL = (configuredApiUrl || "http://localhost:8000").replace(/\/+$/, "");
export const WS_URL = (configuredWsUrl || "ws://localhost:8000").replace(/\/+$/, "");
