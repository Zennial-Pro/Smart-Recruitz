import { api } from "./api-client";

const TOKEN_KEY = "sr_auth_token";
const USER_KEY = "sr_auth_user";

export interface AuthUser {
  id: string;
  email: string;
  full_name?: string | null;
  role: string;
}

interface TokenResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

function persist(res: TokenResponse): void {
  localStorage.setItem(TOKEN_KEY, res.access_token);
  localStorage.setItem(USER_KEY, JSON.stringify(res.user));
}

export async function login(email: string, password: string): Promise<AuthUser> {
  const res = await api
    .post("auth/login", { json: { email, password } })
    .json<TokenResponse>();
  persist(res);
  return res.user;
}

export async function signup(
  email: string,
  password: string,
  fullName?: string,
): Promise<AuthUser> {
  const res = await api
    .post("auth/signup", { json: { email, password, full_name: fullName } })
    .json<TokenResponse>();
  persist(res);
  return res.user;
}

/** Store a token handed back from the Google OAuth callback and load the user. */
export async function applyToken(token: string): Promise<AuthUser | null> {
  try {
    localStorage.setItem(TOKEN_KEY, token);
    const user = await api.get("auth/me").json<AuthUser>();
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    return user;
  } catch {
    localStorage.removeItem(TOKEN_KEY);
    return null;
  }
}

export function logout(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  } catch {
    /* ignore */
  }
}
