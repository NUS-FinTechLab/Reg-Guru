const TOKEN_STORAGE_KEY = "reg-guru.token";
const USER_STORAGE_KEY = "reg-guru.user";

type StoredUser = {
  id: string;
  username: string;
  email: string;
  createdAt: string;
  updatedAt: string;
};

export const getStoredUser = (): StoredUser | null => {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = sessionStorage.getItem(USER_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as StoredUser;
  } catch (error) {
    console.error("Failed to parse stored user", error);
    return null;
  }
};

export const getAuthToken = (): string | null => {
  if (typeof window === "undefined") {
    return null;
  }
  return sessionStorage.getItem(TOKEN_STORAGE_KEY);
};

export const storeAuth = (token: string, user: StoredUser): void => {
  if (typeof window === "undefined") {
    return;
  }
  sessionStorage.setItem(TOKEN_STORAGE_KEY, token);
  sessionStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
  window.dispatchEvent(new Event("auth-change"));
};

export const clearAuth = (): void => {
  if (typeof window === "undefined") {
    return;
  }
  sessionStorage.removeItem(TOKEN_STORAGE_KEY);
  sessionStorage.removeItem(USER_STORAGE_KEY);
  window.dispatchEvent(new Event("auth-change"));
};

export const buildAuthHeaders = (): Record<string, string> => {
  const token = getAuthToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const TOKEN_KEY = TOKEN_STORAGE_KEY;
export const USER_KEY = USER_STORAGE_KEY;
