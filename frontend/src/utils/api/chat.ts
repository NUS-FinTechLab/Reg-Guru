import { SERVER_URL } from "@/utils/constants";
import { ChatHistoryResponse, ChatRequest, ChatResponse } from "./types";

/**
 * Send a chat message to the backend
 * @param request - The chat request containing message and region
 * @returns Promise with the bot's response and sources
 */
export const sendChatMessage = async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await fetch(`${SERVER_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            chatId: request.chatId,
            message: { text: request.text },
            region: request.region?.toLowerCase() || "us"
        }),
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
};

export const fetchChatHistory = async (chatId: string): Promise<ChatHistoryResponse> => {
    const response = await fetch(`${SERVER_URL}/api/chat/${chatId}`);

    if (response.status === 404) {
        throw new Error("not_found");
    }

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
};
