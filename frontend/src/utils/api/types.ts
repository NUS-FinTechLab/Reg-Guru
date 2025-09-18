// Common types for API responses and requests
export interface Message {
    id: number;
    text: string;
    role: "user" | "bot";
    timestamp: Date;
    sources?: Source[]; // Add sources to message for bot responses
}

export interface Source {
    title: string;
    link: string;
}

export interface ChatRequest {
    message: Message;
    region?: string;
}

export interface ChatResponse {
    response: string;
    sources?: Source[];
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