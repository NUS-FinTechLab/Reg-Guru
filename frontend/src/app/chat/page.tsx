import type { Metadata } from "next";

import ChatDashboard from "@/app/chat/components/ChatDashboard";

export default function ChatHomePage() {
  return <ChatDashboard />;
}

export const metadata: Metadata = {
  title: "Chat | Reg-Guru - Document Q&A Chatbot",
};
