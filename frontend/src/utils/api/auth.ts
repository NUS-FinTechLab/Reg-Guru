import { SERVER_URL } from "@/utils/constants";
import {
  clearAuth,
  fetchWithAuth,
  getRefreshToken,
  storeAuth,
} from "@/utils/auth-client";
import type { AuthUser } from "./types";

interface AuthSuccessResponse {
  token: string;
  refreshToken: string;
  user: AuthUser;
}

interface RegisterPayload {
  username: string;
  email: string;
  password: string;
}

interface LoginPayload {
  identifier: string;
  password: string;
}

async function handleAuthResponse(response: Response): Promise<AuthSuccessResponse> {
  if (!response.ok) {
    const bodyText = await response.text();
    try {
      const data = JSON.parse(bodyText) as { error?: string };
      if (data?.error) {
        throw new Error(data.error);
      }
    } catch (jsonError) {
      throw new Error(bodyText || `HTTP error ${response.status}`);
    }
    throw new Error(`HTTP error ${response.status}`);
  }

  const data = (await response.json()) as Partial<AuthSuccessResponse> & {
    error?: string;
  };

  if (!data.token || !data.user || !data.refreshToken) {
    throw new Error(data.error || "Authentication response missing token information");
  }

  storeAuth({ token: data.token, refreshToken: data.refreshToken, user: data.user });
  return { token: data.token, refreshToken: data.refreshToken, user: data.user };
}

export const registerUser = async (
  payload: RegisterPayload,
): Promise<AuthSuccessResponse> => {
  const response = await fetchWithAuth(
    `${SERVER_URL}/api/auth/register`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
    { skipAuth: true },
  );

  return handleAuthResponse(response);
};

export const loginUser = async (payload: LoginPayload): Promise<AuthSuccessResponse> => {
  const response = await fetchWithAuth(
    `${SERVER_URL}/api/auth/login`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: payload.identifier,
        email: payload.identifier,
        password: payload.password,
      }),
    },
    { skipAuth: true },
  );

  return handleAuthResponse(response);
};

export const logoutUser = async (): Promise<void> => {
  const refreshToken = getRefreshToken();

  if (refreshToken) {
    try {
      await fetch(`${SERVER_URL}/api/auth/logout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refreshToken }),
      });
    } catch (error) {
      console.warn("Failed to notify backend about logout", error);
    }
  }

  clearAuth();
};
