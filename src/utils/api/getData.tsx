import {SERVER_URL} from "@/utils/constants";
import { string } from "zod";
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

export class fileNames {
    filenames! : string[];
    constructor(filenames : string[]) {
        this.filenames = filenames;
    }
}

export const getFileNames = async (): Promise<fileNames> => {
    try {
        const res = await fetch(SERVER_URL + "/api/get_documents", {next : {revalidate : 3600}});
        const data = await res.json();
        return new fileNames(data.map((x: any) => x.filename));
    } catch (error) {
        console.log("Error loading data: ", error);
    }
    const some : fileNames = {
        filenames: [],
    }
    return some;
}