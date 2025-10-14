// Common types for API responses and requests
export interface Source {
  title: string;
  link: string;
}

export interface Message {
  id: number | string;
  text: string;
  role: "user" | "ai";
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

export interface ChatSummary {
  id: string;
  userId: string;
  createdAt: string;
  updatedAt: string;
}

export interface ChatMessageDTO {
  id: number;
  role: "user" | "ai";
  text: string;
  sources: Source[];
  createdAt: string;
  updatedAt: string;
  userId?: string | null;
}

export interface ChatResponse {
  response: string;
  sources: Source[];
  chat: ChatSummary;
  messages: {
    user: ChatMessageDTO;
    ai: ChatMessageDTO;
  };
}

export interface ChatDetailResponse {
  chat: ChatSummary | null;
  messages: ChatMessageDTO[];
}

export interface ChatRequest {
  chatId?: string;
  text: string;
  region?: string;
  userId: string;
}

export interface ChatListItem {
  id: string;
  userId: string;
  createdAt: string;
  updatedAt: string;
  lastMessage: {
    text: string;
    role: "user" | "ai";
    createdAt: string | null;
  } | null;
}

export type ChecklistItemStatus = "not_started" | "ongoing" | "finished";
export type ChecklistItemPriority = "low" | "medium" | "high";

export interface ChecklistItemDTO {
  id: string;
  checklistId: string;
  stageId: string;
  content: string;
  status: ChecklistItemStatus;
  priority: ChecklistItemPriority;
  referenceLink: string[] | null;
  position: number;
  createdAt: string;
  updatedAt: string;
}

export interface ChecklistSummaryDTO {
  id: string;
  userId: string;
  title: string;
  description: string;
  createdAt: string;
  updatedAt: string;
  stageCount: number;
  totalItems: number;
  finishedItems: number;
  progress: number;
}

export interface ChecklistStageDTO {
  id: string;
  checklistId: string;
  title: string;
  description: string;
  position: number;
  createdAt: string;
  updatedAt: string;
  items: ChecklistItemDTO[];
}

export interface ChecklistDetailDTO extends ChecklistSummaryDTO {
  stages: ChecklistStageDTO[];
  items: ChecklistItemDTO[];
}

export interface ChecklistItemInput {
  content: string;
  status: ChecklistItemStatus;
  priority: ChecklistItemPriority;
  position?: number;
}

export interface ChecklistStageInput {
  title: string;
  description?: string;
  position?: number;
  items: ChecklistItemInput[];
}

export interface ChecklistInput {
  title: string;
  description: string;
  stages: ChecklistStageInput[];
  /**
   * Fallback for legacy payloads. When provided, the backend will map these items into a default stage.
   */
  items?: ChecklistItemInput[];
}
