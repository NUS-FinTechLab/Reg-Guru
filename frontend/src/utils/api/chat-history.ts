import { SERVER_URL } from "@/utils/constants";
import { buildAuthHeaders } from "@/utils/auth-client";
import { ChatHistoryEntry } from "./types";

export const getChatHistoryEntries = async (
  limit?: number,
): Promise<ChatHistoryEntry[]> => {
  const params = new URLSearchParams();
  if (typeof limit === "number") {
    params.set("limit", limit.toString());
  }

  try {
    const response = await fetch(
      `${SERVER_URL}/api/chat_history${params.toString() ? `?${params.toString()}` : ""}`,
      {
        headers: buildAuthHeaders(),
      },
    );

    if (!response.ok) {
      return [];
    }

    const data = (await response.json()) as {
      history?: ChatHistoryEntry[];
    };

    return data.history ?? [];
  } catch (error) {
    return [];
  }
};

export const createChatHistoryEntry = async (
  chatExternalId: string,
  payload: { query: string; responseSummary?: string | null },
): Promise<{ historyEntry: ChatHistoryEntry }> => {
  const response = await fetch(
    `${SERVER_URL}/api/chat/${chatExternalId}/history`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...buildAuthHeaders(),
      },
      body: JSON.stringify(payload),
    },
  );

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json() as Promise<{ historyEntry: ChatHistoryEntry }>;
};
