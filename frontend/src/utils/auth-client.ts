import { SERVER_URL } from "@/utils/constants";
import type { AuthUser } from "@/utils/api/types";

const ACCESS_TOKEN_STORAGE_KEY = "reg-guru.token";
const REFRESH_TOKEN_STORAGE_KEY = "reg-guru.refresh";
const USER_STORAGE_KEY = "reg-guru.user";

type StoredAuthPayload = {
  token: string;
  refreshToken: string;
  user: AuthUser;
};

const isBrowser = (): boolean => typeof window !== "undefined";

const readStorage = (key: string): string | null => {
  if (!isBrowser()) {
    return null;
  }
  try {
    return localStorage.getItem(key);
  } catch (error) {
    console.error(`Failed to read localStorage key "${key}"`, error);
    return null;
  }
};

export const getStoredUser = (): AuthUser | null => {
  const raw = readStorage(USER_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as AuthUser;
  } catch (error) {
    console.error("Failed to parse stored user", error);
    return null;
  }
};

export const getAuthToken = (): string | null => readStorage(ACCESS_TOKEN_STORAGE_KEY);

export const getRefreshToken = (): string | null => readStorage(REFRESH_TOKEN_STORAGE_KEY);

export const storeAuth = (payload: StoredAuthPayload): void => {
  if (!isBrowser()) {
    return;
  }

  localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, payload.token);
  localStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, payload.refreshToken);
  localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(payload.user));
  window.dispatchEvent(new Event("auth-change"));
};

export const clearAuth = (): void => {
  if (!isBrowser()) {
    return;
  }

  localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
  localStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY);
  localStorage.removeItem(USER_STORAGE_KEY);
  window.dispatchEvent(new Event("auth-change"));
};

export const buildAuthHeaders = (): Record<string, string> => {
  const headers: Record<string, string> = {};
  const token = getAuthToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const user = getStoredUser();
  if (user?.id) {
    headers["X-User-Id"] = user.id;
  }

  return headers;
};

const shouldRetryWithRefresh = async (response: Response): Promise<boolean> => {
  try {
    const payload = (await response.json()) as { error?: string } | null;
    return payload?.error === "token_expired";
  } catch (error) {
    console.warn("Failed to parse auth error payload", error);
    return false;
  }
};

export const refreshAccessToken = async (): Promise<boolean> => {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    return false;
  }

  try {
    const response = await fetch(`${SERVER_URL}/api/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refreshToken }),
    });

    if (!response.ok) {
      if (response.status === 401) {
        clearAuth();
      }
      return false;
    }

    const data = (await response.json()) as Partial<StoredAuthPayload> & { error?: string };
    if (!data?.token || !data?.refreshToken || !data?.user) {
      console.error("Refresh response missing fields");
      return false;
    }

    storeAuth({
      token: data.token,
      refreshToken: data.refreshToken,
      user: data.user,
    });
    return true;
  } catch (error) {
    console.error("Failed to refresh access token", error);
    return false;
  }
};

const mergeHeaders = (init: RequestInit, authHeaders: Record<string, string>): Headers => {
  const baseHeaders = init.headers instanceof Headers
    ? new Headers(init.headers)
    : new Headers(init.headers ?? {});

  Object.entries(authHeaders).forEach(([key, value]) => {
    baseHeaders.set(key, value);
  });

  return baseHeaders;
};

export const fetchWithAuth = async (
  input: RequestInfo | URL,
  init: RequestInit = {},
  options: { skipAuth?: boolean; retryOnAuthFailure?: boolean } = {},
): Promise<Response> => {
  const { skipAuth = false, retryOnAuthFailure = true } = options;
  const initialHeaders = skipAuth ? init.headers : mergeHeaders(init, buildAuthHeaders());

  const response = await fetch(input, { ...init, headers: initialHeaders });

  if (!skipAuth && response.status === 401) {
    if (retryOnAuthFailure) {
      const shouldRetry = await shouldRetryWithRefresh(response.clone());
      if (shouldRetry) {
        const refreshed = await refreshAccessToken();
        if (refreshed) {
          const retryHeaders = mergeHeaders(init, buildAuthHeaders());
          return fetch(input, { ...init, headers: retryHeaders });
        }
      }
    }

    clearAuth();
  } else if (!skipAuth && response.status === 403) {
    clearAuth();
  }

  return response;
};

export const TOKEN_KEY = ACCESS_TOKEN_STORAGE_KEY;
export const USER_KEY = USER_STORAGE_KEY;
export const REFRESH_TOKEN_KEY = REFRESH_TOKEN_STORAGE_KEY;
