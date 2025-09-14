import ChatDashboard from "@/app/chat/components/Chat";
import {Metadata} from "next";

export default function Home() {

    return (
       <main className={""}>
           <ChatDashboard/>
       </main>
    );
}
export const metadata :Metadata = {
    title: "Chat | Reg-Guru - Document Q&A Chatbot",
}