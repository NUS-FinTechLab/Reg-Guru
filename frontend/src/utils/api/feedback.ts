import { SERVER_URL } from "@/utils/constants";
import { buildAuthHeaders } from "@/utils/auth-client";
import { FeedbackRequest } from "./types";

/**
 * Log user feedback for a query response
 * @param feedbackData - Object containing feedback information
 * @returns Promise that resolves when feedback is logged
 */
export const logFeedback = async (feedbackData: FeedbackRequest): Promise<void> => {
    try {
        const response = await fetch(`${SERVER_URL}/api/log_feedback`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...buildAuthHeaders(),
            },
            body: JSON.stringify(feedbackData),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
    } catch (error) {
        console.error("Error logging feedback:", error);
        throw error;
    }
};

/**
 * Test the API connection
 * @returns Promise that resolves with test message
 */
export const testApi = async (): Promise<{ message: string }> => {
    try {
        const response = await fetch(`${SERVER_URL}/api/test`, {
            headers: buildAuthHeaders(),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Error testing API:", error);
        throw error;
    }
};
