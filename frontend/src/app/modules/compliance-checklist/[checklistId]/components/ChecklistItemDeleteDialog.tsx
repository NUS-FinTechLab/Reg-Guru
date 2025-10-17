"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";

import type { ChecklistItemDTO } from "@/utils/api";

interface ChecklistItemDeleteDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  item: ChecklistItemDTO | null;
  stageTitle: string | null;
  onConfirm: () => void;
  onCancel: () => void;
  isDeleting: boolean;
  error: string | null;
}

export default function ChecklistItemDeleteDialog({
  open,
  onOpenChange,
  item,
  stageTitle,
  onConfirm,
  onCancel,
  isDeleting,
  error,
}: ChecklistItemDeleteDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md space-y-4">
        <DialogHeader className="space-y-2 text-left">
          <DialogTitle>Delete task</DialogTitle>
          <DialogDescription>
            {stageTitle ? `Stage: ${stageTitle}` : "Delete the selected checklist task."}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 text-sm">
          <p className="text-muted-foreground">Are you sure you want to delete this task?</p>
          {item ? (
            <div className="rounded-lg border border-border/60 bg-muted/20 px-3 py-3 text-foreground">
              <p className="text-sm font-medium">{item.content}</p>
            </div>
          ) : null}
          {error && (
            <div className="rounded-lg border border-destructive/40 bg-destructive/5 px-3 py-2 text-sm text-destructive">
              {error}
            </div>
          )}
        </div>

        <DialogFooter className="justify-end gap-2 sm:flex-row">
          <Button type="button" variant="ghost" onClick={onCancel} disabled={isDeleting}>
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            onClick={onConfirm}
            disabled={isDeleting}
            aria-busy={isDeleting}
          >
            {isDeleting ? (
              <span className="flex items-center gap-2">
                <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                Deleting…
              </span>
            ) : (
              "Delete"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
