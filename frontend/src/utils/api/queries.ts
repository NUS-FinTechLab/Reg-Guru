import { SERVER_URL } from "@/utils/constants";

// Note: All saved queries functionality has been removed per user request
// This file is kept for backward compatibility but functions are disabled

/**
 * @deprecated Saved queries functionality has been removed
 */
export const getSavedQueries = async (): Promise<any[]> => {
    console.warn("getSavedQueries: Saved queries functionality has been removed");
    return [];
};

/**
 * @deprecated Saved queries functionality has been removed  
 */
export const getAllData = async (): Promise<{ savedQueries: any[] }> => {
    console.warn("getAllData: Saved queries functionality has been removed");
    return { savedQueries: [] };
};