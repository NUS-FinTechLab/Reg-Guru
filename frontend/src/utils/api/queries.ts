import { SERVER_URL } from "@/utils/constants";

export interface SavedQuery {
    id: number;
    session_id: string | null;
    chat_external_id: string | null;
    query_text: string;
    response_summary: string | null;
    created_at: string;
}

export const getSavedQueries = async (): Promise<SavedQuery[]> => {
    const response = await fetch(`${SERVER_URL}/api/saved_queries`);

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.savedQueries ?? [];
};

export const getAllData = async (): Promise<{ savedQueries: SavedQuery[] }> => {
    const savedQueries = await getSavedQueries();
    return { savedQueries };
};

interface CreateSavedQueryPayload {
    chatId?: string;
    query: string;
    responseSummary?: string;
}

export const createSavedQuery = async (payload: CreateSavedQueryPayload): Promise<{ savedQuery: SavedQuery }> => {
    const response = await fetch(`${SERVER_URL}/api/saved_queries`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json() as Promise<{ savedQuery: SavedQuery }>;
};
