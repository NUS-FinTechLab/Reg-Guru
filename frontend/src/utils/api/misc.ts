import { SERVER_URL } from "@/utils/constants";
import { fetchWithAuth } from "@/utils/auth-client";

export const testApi = async (): Promise<{ message: string }> => {
  try {
    const response = await fetchWithAuth(`${SERVER_URL}/api/test`);

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
