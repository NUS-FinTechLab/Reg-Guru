import { SERVER_URL } from "@/utils/constants";
import { buildAuthHeaders, clearAuth, storeAuth } from "@/utils/auth-client";
import type { AuthUser } from "./types";

interface AuthSuccessResponse {
  token: string;
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

  if (!data.token || !data.user) {
    throw new Error(data.error || "Authentication response missing token");
  }

  storeAuth(data.token, data.user);
  return { token: data.token, user: data.user };
}

export const registerUser = async (
  payload: RegisterPayload,
): Promise<AuthSuccessResponse> => {
  const response = await fetch(`${SERVER_URL}/api/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...buildAuthHeaders(),
    },
    body: JSON.stringify(payload),
  });

  return handleAuthResponse(response);
};

export const loginUser = async (payload: LoginPayload): Promise<AuthSuccessResponse> => {
  const response = await fetch(`${SERVER_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: payload.identifier,
      email: payload.identifier,
      password: payload.password,
    }),
  });

  return handleAuthResponse(response);
};

export const logoutUser = (): void => {
  clearAuth();
};
