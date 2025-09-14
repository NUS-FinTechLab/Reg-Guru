import {Metadata} from "next";
import ChatPage from "@/app/chat/[chatId]/components/ChatPage";

export default function Home() {
    return (
        <main>
            <ChatPage/>
        </main>
    );
}
export const metadata :Metadata = {
    title: "Chat | Reg-Guru - Document Q&A Chatbot",
}