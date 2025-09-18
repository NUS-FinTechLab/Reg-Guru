import { SERVER_URL } from "@/utils/constants";
import { ChatRequest, ChatResponse } from "./types";

/**
 * Send a chat message to the backend
 * @param message - The message object containing user input
 * @returns Promise with the bot's response
 */
export const sendChatMessage = async (message: ChatRequest): Promise<ChatResponse> => {
    try {
        const response = await fetch(`${SERVER_URL}/api/chat`, {
            method: "POST",
            headers: { 
                "Content-Type": "application/json" 
            },
            body: JSON.stringify(message),
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