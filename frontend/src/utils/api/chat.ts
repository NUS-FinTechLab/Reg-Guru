import { SERVER_URL } from "@/utils/constants";
import { buildAuthHeaders } from "@/utils/auth-client";
import { ChatHistoryResponse, ChatRequest, ChatResponse } from "./types";

/**
 * Send a chat message to the backend
 * @param request - The chat request containing message and region
 * @returns Promise with the bot's response and sources
 */
export const sendChatMessage = async (
  request: ChatRequest,
): Promise<ChatResponse> => {
  try {
    const response = await fetch(`${SERVER_URL}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...buildAuthHeaders(),
      },
      body: JSON.stringify({
        chatId: request.chatId,
        message: { text: request.text },
        region: request.region?.toLowerCase() || "us",
        userId: request.userId,
      }),
    });

    if (!response.ok) {
      const body = await response.text();
      let message = `HTTP error! status: ${response.status}`;
      try {
        const parsed = JSON.parse(body) as { error?: string };
        if (parsed?.error) {
          message = parsed.error;
        }
      } catch (error) {
        if (body) {
          message = body;
        }
      }
      throw new Error(message);
    }

    return response.json();
  } catch (error) {
    console.error("Failed to send chat message", error);
    throw new Error("network_error");
  }
};

export const fetchChatHistory = async (
  chatId: string,
): Promise<ChatHistoryResponse> => {
  try {
    const response = await fetch(`${SERVER_URL}/api/chat/${chatId}`, {
      headers: buildAuthHeaders(),
    });

    if (response.status === 404) {
      throw new Error("not_found");
    }

    if (!response.ok) {
      const body = await response.text();
      let message = `HTTP error! status: ${response.status}`;
      try {
        const parsed = JSON.parse(body) as { error?: string };
        if (parsed?.error) {
          message = parsed.error;
        }
      } catch (error) {
        if (body) {
          message = body;
        }
      }
      throw new Error(message);
    }

    return response.json();
  } catch (error) {
    console.error("Failed to fetch chat history", error);
    throw new Error("network_error");
  }
};
