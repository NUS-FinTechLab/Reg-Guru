import type { Metadata } from "next";

import ChatPage from "@/app/modules/chat/[chatId]/components/ChatPage";

export default function ChatSessionPage() {
  return <ChatPage />;
}

export const metadata: Metadata = {
  title: "Chat | Reg-Guru - Document Q&A Chatbot",
};
