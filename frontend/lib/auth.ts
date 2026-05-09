export type User = {
  id: number;
  full_name: string;
  phone: string;
  email?: string | null;
  avatar_path?: string | null;
  role: string;
};

function hasStorage() {
  return typeof window !== "undefined";
}

export function saveAuth(access: string, refresh: string, user: User) {
  if (!hasStorage()) return;
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
  localStorage.setItem("user", JSON.stringify(user));
}

export function getAccessToken(): string | null {
  if (!hasStorage()) return null;
  return localStorage.getItem("access_token");
}

export function getRefreshToken(): string | null {
  if (!hasStorage()) return null;
  return localStorage.getItem("refresh_token");
}

export function getUser(): User | null {
  if (!hasStorage()) return null;
  const raw = localStorage.getItem("user");
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function setLastPath(path: string) {
  if (!hasStorage()) return;
  localStorage.setItem("last_path", path);
}

export function getLastPath(): string | null {
  if (!hasStorage()) return null;
  return localStorage.getItem("last_path");
}

export function logout() {
  if (!hasStorage()) return;
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user");
  localStorage.removeItem("last_path");
}
