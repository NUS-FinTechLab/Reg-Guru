// Common types for API responses and requests
export interface Source {
    title: string;
    link: string;
}

export interface Message {
    id: number | string;
    text: string;
    role: "user" | "bot";
    timestamp: Date;
    sources?: Source[];
    pending?: boolean;
}

export interface AuthUser {
  id: string;
  username: string;
  email: string;
  createdAt: string;
  updatedAt: string;
}

export interface ChatSession {
    id: string;
    chatId: string;
    region: string;
    userId: string;
    createdAt: string;
    updatedAt: string;
}

export interface ChatMessageDTO {
    id: number;
    role: "user" | "bot";
    text: string;
    sources: Source[];
    timestamp: string;
}

export interface ChatResponse {
    response: string;
    sources: Source[];
    session: ChatSession;
    messages: {
        user: ChatMessageDTO;
        bot: ChatMessageDTO;
    };
}

export interface ChatHistoryResponse {
    session: ChatSession;
    messages: ChatMessageDTO[];
}

export interface ChatRequest {
    chatId: string;
    text: string;
    region?: string;
    userId: string;
}

export interface FeedbackRequest {
    chatId: string;
    rating: 'thumbs_up' | 'thumbs_down';
    comments?: string;
    messageId?: number;
}

export interface ApiResponse<T> {
    data?: T;
    error?: string;
    status: number;
}

export interface ChatHistoryEntry {
    id: number;
    chatId: string | null;
    chatExternalId: string | null;
    queryText: string;
    responseSummary: string | null;
    createdAt: string;
}
