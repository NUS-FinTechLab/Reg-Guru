import {Metadata} from "next";
import HistoryDashboard from "@/app/chat/components/history";

export default function Home() {

    return (
        <main className={""}>
            <HistoryDashboard/>
        </main>
    );
}
export const metadata :Metadata = {
    title: "History | Reg-Guru - Document Q&A Chatbot",
}