import {SERVER_URL} from "@/utils/constants";
export const getData = async () => {
    try {
        console.log("SERVER_URL", process.env.NEXT_PUBLIC_BACKEND_URL);
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