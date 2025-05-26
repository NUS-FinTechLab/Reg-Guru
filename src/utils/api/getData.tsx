import {SERVER_URL} from "@/utils/constants";
export const getData = async () => {
    try {
        const [queriesRes, docsRes] = await Promise.all([
            fetch(`${SERVER_URL}/api/get_queries`),
            fetch(`${SERVER_URL}/api/get_documents`)
        ]);
        const savedQueries = await queriesRes.json();
        const uploadedDocuments = await docsRes.json();

        return {savedQueries, uploadedDocuments}
    } catch (error) {
        console.error("Error loading data:", error);
    }
};