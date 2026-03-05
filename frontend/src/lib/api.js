// In dev, VITE_API_BASE is unset and Vite proxies /api -> localhost:8000.
// In production, set VITE_API_BASE to your backend Render URL,
// e.g. https://matchadaddy-api.onrender.com
export const API_BASE = import.meta.env.VITE_API_BASE ?? ''
