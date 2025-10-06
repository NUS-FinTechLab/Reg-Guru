import ChatDashboard from "@/app/chat/components/ChatDashboard";
import { Metadata } from "next";

export default function Home() {
    return (
        <ChatDashboard />
    );
}
export const metadata: Metadata = {
    title: "Chat | Reg-Guru - Document Q&A Chatbot",
}