import ky from "ky";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

const TOKEN_STORAGE_KEY = "sr_integration_token";

/**
 * When embedded inside the LMS admin (hiring-manager iframe) or the LMS student
 * portal, the host passes a short-lived bearer token via the `?sr_token=` query
 * param. Capture it once and persist it for the session so every API call is
 * authenticated. Running standalone (no token) keeps the previous behaviour.
 */
function captureIntegrationToken(): void {
  if (typeof window === "undefined") return;
  try {
    const url = new URL(window.location.href);
    const token = url.searchParams.get("sr_token");
    if (token) {
      sessionStorage.setItem(TOKEN_STORAGE_KEY, token);
      // Scrub the token from the visible URL.
      url.searchParams.delete("sr_token");
      window.history.replaceState({}, "", url.toString());
    }
  } catch {
    /* ignore */
  }
}

function getIntegrationToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    // Standalone login token (localStorage) takes precedence; fall back to the
    // embedded-iframe integration token (sessionStorage).
    return (
      localStorage.getItem("sr_auth_token") ||
      sessionStorage.getItem(TOKEN_STORAGE_KEY)
    );
  } catch {
    return null;
  }
}

captureIntegrationToken();

export const api = ky.create({
  prefixUrl: API_BASE_URL,
  timeout: 30_000,
  retry: {
    limit: 2,
    methods: ["get"],
    statusCodes: [408, 502, 503, 504],
  },
  hooks: {
    beforeRequest: [
      (request) => {
        const token = getIntegrationToken();
        if (token) {
          request.headers.set("Authorization", `Bearer ${token}`);
        }
      },
    ],
    afterResponse: [
      (request, _options, response) => {
        // Session expired / invalid token → clear it and bounce to login instead
        // of letting every call silently 401 forever.
        if (response.status !== 401 || typeof window === "undefined") return;
        const isAuthCall = new URL(request.url).pathname.includes("/auth/");
        const hadSession = !!localStorage.getItem("sr_auth_token");
        if (isAuthCall || !hadSession) return; // don't loop on the login page / embedded flow
        localStorage.removeItem("sr_auth_token");
        localStorage.removeItem("sr_auth_user");
        if (!window.location.pathname.startsWith("/login")) {
          window.location.href = "/login?expired=1";
        }
      },
    ],
  },
});
