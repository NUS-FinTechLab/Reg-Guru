// Common types for API responses and requests
export interface Message {
    id: number;
    text: string;
    role: "user" | "bot";
    timestamp: Date;
}

export interface ChatRequest {
    message: Message;
}

export interface ChatResponse {
    response: string;
}

export interface FeedbackRequest {
    query: string;
    response: string;
    rating: 'thumbs_up' | 'thumbs_down';
    comments?: string;
}

export interface ApiResponse<T> {
    data?: T;
    error?: string;
    status: number;
}