import { SERVER_URL } from "@/utils/constants";
import { buildAuthHeaders } from "@/utils/auth-client";
import { ChatListItem } from "./types";

const normalizeChat = (raw: any): ChatListItem => ({
  id: String(raw.id),
  userId: String(raw.userId ?? raw.user_id ?? ""),
  createdAt: String(raw.createdAt ?? raw.created_at ?? ""),
  updatedAt: String(raw.updatedAt ?? raw.updated_at ?? ""),
  lastMessage: raw.lastMessage
    ? {
        text: String(raw.lastMessage.text ?? ""),
        role: raw.lastMessage.role === "user" ? "user" : "ai",
        createdAt: raw.lastMessage.createdAt ?? null,
      }
    : null,
});

export const listChats = async (): Promise<ChatListItem[]> => {
  const response = await fetch(`${SERVER_URL}/api/chats`, {
    headers: buildAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const payload = (await response.json()) as { chats?: unknown[] };
  const rawChats = Array.isArray(payload.chats) ? payload.chats : [];
  return rawChats.map(normalizeChat);
};
