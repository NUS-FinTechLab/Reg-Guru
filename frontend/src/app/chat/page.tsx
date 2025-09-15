import ChatDashboard from "@/app/chat/components/Chat";
import { Metadata } from "next";

export default function Home() {
    return (
        <ChatDashboard />
    );
}
export const metadata: Metadata = {
    title: "Chat | Reg-Guru - Document Q&A Chatbot",
}