"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  ChecklistDetailDTO,
  ChecklistItemDTO,
  ChecklistItemPriority,
  ChecklistItemStatus,
  ChecklistStageDTO,
  deleteChecklistItem,
  getChecklist,
  updateChecklistItem,
} from "@/utils/api";

import ChecklistDetailHeader from "./components/ChecklistDetailHeader";
import ChecklistStageList from "./components/ChecklistStageList";
import ChecklistItemEditDialog from "./components/ChecklistItemEditDialog";
import ChecklistItemDeleteDialog from "./components/ChecklistItemDeleteDialog";

interface MetaConfig {
  label: string;
  className: string;
}

const STATUS_META: Record<ChecklistItemStatus, MetaConfig> = {
  not_started: {
    label: "Not started",
    className: "border-border/70 bg-muted/40 text-muted-foreground",
  },
  ongoing: {
    label: "In progress",
    className: "border-amber-400/70 bg-amber-500/20 text-amber-900 dark:text-white",
  },
  finished: {
    label: "Finished",
    className: "border-emerald-500/70 bg-emerald-500/20 text-emerald-900 dark:text-white",
  },
};

const STATUS_OPTIONS: ChecklistItemStatus[] = ["not_started", "ongoing", "finished"];

const PRIORITY_META: Record<ChecklistItemPriority, MetaConfig> = {
  low: {
    label: "Low",
    className: "border-blue-300/70 bg-blue-500/20 text-blue-900 dark:text-white",
  },
  medium: {
    label: "Medium",
    className: "border-amber-400/70 bg-amber-500/20 text-amber-900 dark:text-white",
  },
  high: {
    label: "High",
    className: "border-rose-500/70 bg-rose-500/20 text-rose-900 dark:text-white",
  },
};

const PRIORITY_OPTIONS: ChecklistItemPriority[] = ["low", "medium", "high"];

const ITEM_DECORATION: Record<ChecklistItemStatus, string> = {
  not_started: "border-border/60 bg-background/95 text-foreground",
  ongoing: "border-amber-400/70 bg-amber-500/10 text-amber-900 dark:text-white",
  finished: "border-emerald-400/70 bg-emerald-500/10 text-emerald-900 dark:text-white",
};

function getRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMinutes = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  const diffMonths = Math.floor(diffDays / 30);
  const diffYears = Math.floor(diffDays / 365);

  if (diffMinutes < 1) {
    return "just now";
  }
  if (diffMinutes < 60) {
    return `${diffMinutes} ${diffMinutes === 1 ? "minute" : "minutes"} ago`;
  }
  if (diffHours < 24) {
    return `${diffHours} ${diffHours === 1 ? "hour" : "hours"} ago`;
  }
  if (diffDays < 30) {
    return `${diffDays} ${diffDays === 1 ? "day" : "days"} ago`;
  }
  if (diffMonths < 12) {
    return `${diffMonths} ${diffMonths === 1 ? "month" : "months"} ago`;
  }
  return `${diffYears} ${diffYears === 1 ? "year" : "years"} ago`;
}

export default function ChecklistDetailPage() {
  const params = useParams();
  const router = useRouter();
  const checklistIdParam = Array.isArray(params?.checklistId)
    ? params.checklistId[0]
    : params?.checklistId;
  const checklistId = checklistIdParam?.toString() ?? "";

  const [checklist, setChecklist] = useState<ChecklistDetailDTO | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [expandedStages, setExpandedStages] = useState<Record<string, boolean>>({});
  const [updatingItemStatusIds, setUpdatingItemStatusIds] = useState<Set<string>>(() => new Set());
  const [editingItem, setEditingItem] = useState<ChecklistItemDTO | null>(null);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [itemForm, setItemForm] = useState<{
    content: string;
    status: ChecklistItemStatus;
    priority: ChecklistItemPriority;
  }>(() => ({
    content: "",
    status: "not_started",
    priority: "medium",
  }));
  const [itemFormError, setItemFormError] = useState<string | null>(null);
  const [isSavingItem, setIsSavingItem] = useState(false);
  const [pendingDeleteItem, setPendingDeleteItem] = useState<ChecklistItemDTO | null>(null);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [isDeletingItem, setIsDeletingItem] = useState(false);

  const fetchChecklistData = useCallback(async (): Promise<ChecklistDetailDTO | null> => {
    if (!checklistId) {
      return null;
    }

    try {
      const data = await getChecklist(checklistId);
      return data;
    } catch (error) {
      console.error("Failed to fetch checklist", error);
      return null;
    }
  }, [checklistId]);

  const refreshChecklist = useCallback(async () => {
    const data = await fetchChecklistData();
    if (!data) {
      setChecklist(null);
      setNotFound(true);
    } else {
      setChecklist(data);
      setNotFound(false);
    }
  }, [fetchChecklistData]);

  useEffect(() => {
    let isMounted = true;

    if (!checklistId) {
      setChecklist(null);
      setNotFound(true);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setNotFound(false);

    fetchChecklistData()
      .then((data) => {
        if (!isMounted) {
          return;
        }

        if (!data) {
          setChecklist(null);
          setNotFound(true);
          return;
        }

        setChecklist(data);
        setNotFound(false);
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [checklistId, fetchChecklistData]);

  const progressPercent = useMemo(() => {
    if (!checklist) {
      return 0;
    }
    const progress = checklist.progress ?? 0;
    const bounded = Math.max(0, Math.min(1, progress));
    return Math.round(bounded * 100);
  }, [checklist]);

  const sortedStages = useMemo<ChecklistStageDTO[]>(() => {
    if (!checklist) {
      return [];
    }

    if (checklist.stages.length > 0) {
      return [...checklist.stages]
        .map((stage) => ({
          ...stage,
          items: [...stage.items].sort((a, b) => a.position - b.position),
        }))
        .sort((a, b) => a.position - b.position);
    }

    if (checklist.items.length > 0) {
      return [
        {
          id: `legacy-${checklist.id}`,
          checklistId: checklist.id,
          title: "Checklist items",
          description: "",
          position: 0,
          createdAt: checklist.createdAt,
          updatedAt: checklist.updatedAt,
          items: [...checklist.items].sort((a, b) => a.position - b.position),
        },
      ];
    }

    return [];
  }, [checklist]);

  useEffect(() => {
    setExpandedStages((previous) => {
      const next: Record<string, boolean> = {};
      for (const stage of sortedStages) {
        next[stage.id] = previous[stage.id] ?? true;
      }

      const previousKeys = Object.keys(previous);
      const nextKeys = Object.keys(next);
      const hasChanged =
        previousKeys.length !== nextKeys.length ||
        nextKeys.some((key) => previous[key] !== next[key]);

      return hasChanged ? next : previous;
    });
  }, [sortedStages]);

  const editingStage = useMemo(() => {
    if (!editingItem || !checklist) {
      return null;
    }
    return checklist.stages.find((stage) => stage.id === editingItem.stageId) ?? null;
  }, [checklist, editingItem]);

  const deletingStage = useMemo(() => {
    if (!pendingDeleteItem || !checklist) {
      return null;
    }
    return checklist.stages.find((stage) => stage.id === pendingDeleteItem.stageId) ?? null;
  }, [checklist, pendingDeleteItem]);

  const applyUpdatedItem = useCallback((updatedItem: ChecklistItemDTO) => {
    setChecklist((previous) => {
      if (!previous) {
        return previous;
      }

      const nextStages = previous.stages.map((stage) => {
        if (stage.id !== updatedItem.stageId) {
          return stage;
        }

        return {
          ...stage,
          items: stage.items.map((existing) =>
            existing.id === updatedItem.id ? updatedItem : existing,
          ),
          updatedAt: updatedItem.updatedAt,
        };
      });

      const nextItems = previous.items.map((existing) =>
        existing.id === updatedItem.id ? updatedItem : existing,
      );

      const finishedItems = nextItems.filter((entry) => entry.status === "finished").length;
      const totalItems = nextItems.length;
      const progress = totalItems > 0 ? finishedItems / totalItems : 0;

      return {
        ...previous,
        stages: nextStages,
        items: nextItems,
        finishedItems,
        totalItems,
        progress,
        updatedAt: updatedItem.updatedAt,
      };
    });
  }, []);

  const handleToggleStage = useCallback((stageId: string) => {
    setExpandedStages((previous) => ({
      ...previous,
      [stageId]: !(previous[stageId] ?? true),
    }));
  }, []);

  const handleEditItem = useCallback((item: ChecklistItemDTO) => {
    setEditingItem(item);
    setItemForm({
      content: item.content,
      status: item.status,
      priority: item.priority,
    });
    setItemFormError(null);
    setIsEditDialogOpen(true);
  }, []);

  const handleDeleteItem = useCallback((item: ChecklistItemDTO) => {
    setPendingDeleteItem(item);
    setDeleteError(null);
    setIsDeleteDialogOpen(true);
  }, []);

  const closeEditDialog = useCallback(() => {
    setIsEditDialogOpen(false);
    setItemFormError(null);
    setEditingItem(null);
  }, []);

  const closeDeleteDialog = useCallback(() => {
    setIsDeleteDialogOpen(false);
    setDeleteError(null);
    setPendingDeleteItem(null);
  }, []);

  const handleEditDialogOpenChange = useCallback(
    (open: boolean) => {
      if (!open) {
        closeEditDialog();
      } else if (editingItem) {
        setIsEditDialogOpen(true);
      }
    },
    [closeEditDialog, editingItem],
  );

  const handleDeleteDialogOpenChange = useCallback(
    (open: boolean) => {
      if (!open) {
        closeDeleteDialog();
      } else if (pendingDeleteItem) {
        setIsDeleteDialogOpen(true);
      }
    },
    [closeDeleteDialog, pendingDeleteItem],
  );

  const handleEditFieldChange = useCallback(
    (field: "content" | "status" | "priority", value: string) => {
      setItemForm((previous) => {
        if (field === "content") {
          return { ...previous, content: value };
        }
        if (field === "status") {
          return { ...previous, status: value as ChecklistItemStatus };
        }
        return { ...previous, priority: value as ChecklistItemPriority };
      });
    },
  []);

  const handleSubmitItem = useCallback(async () => {
    if (!checklistId || !editingItem) {
      return;
    }

    const trimmedContent = itemForm.content.trim();
    if (!trimmedContent) {
      setItemFormError("Task content cannot be empty");
      return;
    }

    setIsSavingItem(true);
    setItemFormError(null);
    setUpdatingItemStatusIds((previous) => {
      const next = new Set(previous);
      next.add(editingItem.id);
      return next;
    });

    try {
      const updatedItem = await updateChecklistItem(checklistId, editingItem.id, {
        content: trimmedContent,
        status: itemForm.status,
        priority: itemForm.priority,
      });
      applyUpdatedItem(updatedItem);
      closeEditDialog();
    } catch (error) {
      console.error("Failed to update checklist item", error);
      setItemFormError("Failed to update the task. Please try again.");
    } finally {
      setIsSavingItem(false);
      setUpdatingItemStatusIds((previous) => {
        const next = new Set(previous);
        if (editingItem) {
          next.delete(editingItem.id);
        }
        return next;
      });
    }
  }, [applyUpdatedItem, checklistId, closeEditDialog, editingItem, itemForm.content, itemForm.priority, itemForm.status]);

  const handleConfirmDelete = useCallback(async () => {
    if (!checklistId || !pendingDeleteItem) {
      return;
    }

    setIsDeletingItem(true);
    setDeleteError(null);

    try {
      const success = await deleteChecklistItem(checklistId, pendingDeleteItem.id);
      if (!success) {
        setDeleteError("Unable to delete the task. Please try again.");
        setIsDeletingItem(false);
        return;
      }

      await refreshChecklist();
      closeDeleteDialog();
    } catch (error) {
      console.error("Failed to delete checklist item", error);
      setDeleteError("Failed to delete the task. Please try again.");
    } finally {
      setIsDeletingItem(false);
    }
  }, [checklistId, closeDeleteDialog, pendingDeleteItem, refreshChecklist]);

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-background via-background to-muted/20 text-foreground">
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6 py-10">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            onClick={() => router.push("/modules/compliance-checklist")}
            className="px-2 hover:bg-muted/40"
          >
            <ArrowLeft className="size-4" />
            Back
          </Button>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-16 text-sm text-muted-foreground">
            Loading checklist…
          </div>
        ) : notFound || !checklist ? (
          <div className="rounded-2xl border border-dashed border-border/60 bg-muted/30 p-10 text-center text-sm text-muted-foreground">
            Checklist not found. It may have been deleted or you might not have access.
          </div>
        ) : (
          <>
            <ChecklistDetailHeader
              checklist={checklist}
              progressPercent={progressPercent}
              getRelativeTime={getRelativeTime}
            />

            <ChecklistStageList
              stages={sortedStages}
              expandedStages={expandedStages}
              onToggleStage={handleToggleStage}
              statusMeta={STATUS_META}
              priorityMeta={PRIORITY_META}
              itemDecoration={ITEM_DECORATION}
              getRelativeTime={getRelativeTime}
              onEditItem={handleEditItem}
              onDeleteItem={handleDeleteItem}
              updatingItemStatusIds={updatingItemStatusIds}
              pendingDeleteItemId={pendingDeleteItem?.id ?? null}
              isDeletingItem={isDeletingItem}
            />
          </>
        )}
      </main>

      <ChecklistItemEditDialog
        open={isEditDialogOpen}
        onOpenChange={handleEditDialogOpenChange}
        stageTitle={editingStage?.title ?? null}
        form={itemForm}
        onFieldChange={handleEditFieldChange}
        onSubmit={handleSubmitItem}
        onCancel={closeEditDialog}
        isSaving={isSavingItem}
        error={itemFormError}
        statusOptions={STATUS_OPTIONS}
        priorityOptions={PRIORITY_OPTIONS}
        statusMeta={STATUS_META}
        priorityMeta={PRIORITY_META}
      />

      <ChecklistItemDeleteDialog
        open={isDeleteDialogOpen}
        onOpenChange={handleDeleteDialogOpenChange}
        item={pendingDeleteItem}
        stageTitle={deletingStage?.title ?? null}
        onConfirm={handleConfirmDelete}
        onCancel={closeDeleteDialog}
        isDeleting={isDeletingItem}
        error={deleteError}
      />
    </div>
  );
}
