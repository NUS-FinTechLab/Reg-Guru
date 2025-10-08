import { SERVER_URL } from "@/utils/constants";
import { buildAuthHeaders } from "@/utils/auth-client";

export const testApi = async (): Promise<{ message: string }> => {
  try {
    const response = await fetch(`${SERVER_URL}/api/test`, {
      headers: buildAuthHeaders(),
    });

    if (!response.ok) {
      console.error("API health check failed", await response.text());
      return { message: "unreachable" };
    }

    return response.json() as Promise<{ message: string }>;
  } catch (error) {
    console.error("API health check failed", error);
    return { message: "unreachable" };
  }
};
