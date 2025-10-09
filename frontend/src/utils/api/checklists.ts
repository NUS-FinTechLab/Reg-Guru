import { SERVER_URL } from "@/utils/constants";
import { fetchWithAuth } from "@/utils/auth-client";
import {
  ChecklistDetailDTO,
  ChecklistInput,
  ChecklistItemDTO,
  ChecklistItemPriority,
  ChecklistItemStatus,
  ChecklistSummaryDTO,
} from "./types";

const STATUS_VALUES: ChecklistItemStatus[] = ["not_started", "ongoing", "finished"];
const PRIORITY_VALUES: ChecklistItemPriority[] = ["low", "medium", "high"];

const isStatus = (value: string): value is ChecklistItemStatus =>
  STATUS_VALUES.includes(value as ChecklistItemStatus);

const isPriority = (value: string): value is ChecklistItemPriority =>
  PRIORITY_VALUES.includes(value as ChecklistItemPriority);

const normalizeStatus = (value: unknown): ChecklistItemStatus => {
  const normalized = String(value ?? "not_started").trim().toLowerCase().replace(/-/g, "_");
  return isStatus(normalized) ? normalized : "not_started";
};

const normalizePriority = (value: unknown): ChecklistItemPriority => {
  const normalized = String(value ?? "medium").trim().toLowerCase();
  return isPriority(normalized) ? normalized : "medium";
};

const toNumber = (value: unknown, fallback = 0): number => {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const normalizeItem = (raw: any): ChecklistItemDTO => ({
  id: String(raw?.id ?? ""),
  checklistId: String(raw?.checklistId ?? raw?.checklist_id ?? ""),
  content: String(raw?.content ?? ""),
  status: normalizeStatus(raw?.status),
  priority: normalizePriority(raw?.priority),
  createdAt: String(raw?.createdAt ?? raw?.created_at ?? new Date().toISOString()),
  updatedAt: String(raw?.updatedAt ?? raw?.updated_at ?? new Date().toISOString()),
});

const normalizeSummary = (raw: any): ChecklistSummaryDTO => ({
  id: String(raw?.id ?? ""),
  userId: String(raw?.userId ?? raw?.user_id ?? ""),
  title: String(raw?.title ?? ""),
  description: String(raw?.description ?? ""),
  createdAt: String(raw?.createdAt ?? raw?.created_at ?? new Date().toISOString()),
  updatedAt: String(raw?.updatedAt ?? raw?.updated_at ?? new Date().toISOString()),
  totalItems: Math.max(0, Math.trunc(toNumber(raw?.totalItems ?? raw?.total_items, 0))),
  finishedItems: Math.max(0, Math.trunc(toNumber(raw?.finishedItems ?? raw?.finished_items, 0))),
  progress: Math.max(0, Math.min(1, Number(toNumber(raw?.progress, 0)))),
});

const normalizeDetail = (raw: any): ChecklistDetailDTO => {
  const summary = normalizeSummary(raw);
  const items = Array.isArray(raw?.items) ? raw.items.map(normalizeItem) : [];
  const totalItems = items.length || summary.totalItems;
  const finishedItems = items.filter((item) => item.status === "finished").length || summary.finishedItems;
  const progress = totalItems > 0 ? finishedItems / totalItems : summary.progress;

  return {
    ...summary,
    items,
    totalItems,
    finishedItems,
    progress,
  };
};

export const listChecklists = async (): Promise<ChecklistSummaryDTO[]> => {
  try {
    const response = await fetchWithAuth(`${SERVER_URL}/api/checklists`);
    if (!response.ok) {
      console.error("Failed to fetch checklists", await response.text());
      return [];
    }

    const payload = (await response.json()) as { checklists?: unknown[] };
    const rawList = Array.isArray(payload?.checklists) ? payload?.checklists : [];
    return rawList.map(normalizeSummary);
  } catch (error) {
    console.error("Failed to fetch checklists", error);
    return [];
  }
};

export const getChecklist = async (
  checklistId: string,
): Promise<ChecklistDetailDTO | null> => {
  try {
    const response = await fetchWithAuth(`${SERVER_URL}/api/checklists/${checklistId}`);

    if (response.status === 404) {
      return null;
    }

    if (!response.ok) {
      console.error("Failed to fetch checklist", await response.text());
      return null;
    }

    const payload = (await response.json()) as { checklist?: unknown };
    if (!payload?.checklist) {
      return null;
    }

    return normalizeDetail(payload.checklist);
  } catch (error) {
    console.error("Failed to fetch checklist", error);
    return null;
  }
};

export const createChecklist = async (
  input: ChecklistInput,
): Promise<ChecklistDetailDTO> => {
  const response = await fetchWithAuth(`${SERVER_URL}/api/checklists`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Failed to create checklist");
  }

  const payload = (await response.json()) as { checklist?: unknown };
  if (!payload?.checklist) {
    throw new Error("Invalid response when creating checklist");
  }

  return normalizeDetail(payload.checklist);
};

export const updateChecklist = async (
  checklistId: string,
  input: Partial<ChecklistInput> & { title: string; description: string },
): Promise<ChecklistDetailDTO> => {
  const response = await fetchWithAuth(`${SERVER_URL}/api/checklists/${checklistId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Failed to update checklist");
  }

  const payload = (await response.json()) as { checklist?: unknown };
  if (!payload?.checklist) {
    throw new Error("Invalid response when updating checklist");
  }

  return normalizeDetail(payload.checklist);
};

export const deleteChecklist = async (checklistId: string): Promise<boolean> => {
  try {
    const response = await fetchWithAuth(`${SERVER_URL}/api/checklists/${checklistId}`, {
      method: "DELETE",
    });

    if (response.status === 404) {
      return false;
    }

    if (!response.ok) {
      console.error("Failed to delete checklist", await response.text());
      return false;
    }

    return true;
  } catch (error) {
    console.error("Failed to delete checklist", error);
    return false;
  }
};

export interface ChecklistGenerationPayload {
  mission: string;
  context: string;
  region: "US" | "SG" | "EU";
  prompt: string;
}

export interface ChecklistGenerationResult {
  ok: boolean;
  status: number;
  message: string;
  data?: unknown;
}

export const requestChecklistGeneration = async (
  payload: ChecklistGenerationPayload,
): Promise<ChecklistGenerationResult> => {
  try {
    const response = await fetchWithAuth(`${SERVER_URL}/api/checklists/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mission: payload.mission,
        context: payload.context,
        region: payload.region.toLowerCase(),
        prompt: payload.prompt,
      }),
    });

    const text = await response.text();
    let parsed: any = null;
    if (text) {
      try {
        parsed = JSON.parse(text);
      } catch (error) {
        console.warn("Failed to parse checklist generation response", error);
      }
    }

    const message =
      parsed?.error || parsed?.message || (response.ok ? "Checklist generation request submitted." : "Checklist generation request failed.");

    return {
      ok: response.ok,
      status: response.status,
      message,
      data: parsed?.result,
    };
  } catch (error) {
    console.error("Failed to request checklist generation", error);
    return {
      ok: false,
      status: 500,
      message: "Failed to request checklist generation.",
    };
  }
};
