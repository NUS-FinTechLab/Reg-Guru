import { SERVER_URL } from "@/utils/constants";
import { buildAuthHeaders } from "@/utils/auth-client";

export const testApi = async (): Promise<{ message: string }> => {
  const response = await fetch(`${SERVER_URL}/api/test`, {
    headers: buildAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json() as Promise<{ message: string }>;
};
