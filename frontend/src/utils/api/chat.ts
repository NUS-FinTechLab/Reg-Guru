import { SERVER_URL } from "@/utils/constants";
import { ChatRequest, ChatResponse } from "./types";

/**
 * Send a chat message to the backend
 * @param request - The chat request containing message and region
 * @returns Promise with the bot's response and sources
 */
export const sendChatMessage = async (request: ChatRequest): Promise<ChatResponse> => {
    try {
        const requestBody = {
            message: {
                text: request.message.text
            },
            region: request.region?.toLowerCase() || "us"
        };

        const response = await fetch(`${SERVER_URL}/api/chat`, {
            method: "POST",
            headers: { 
                "Content-Type": "application/json" 
            },
            body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Error sending chat message:", error);
        throw error;
    }
};

/**
 * @deprecated Save query functionality has been removed per user request
 */
export const saveQuery = async (queryData: any): Promise<void> => {
    console.warn("saveQuery: Save query functionality has been removed");
    // No-op function for backward compatibility
};