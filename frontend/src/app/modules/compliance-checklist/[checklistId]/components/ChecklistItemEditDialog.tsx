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
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import type {
  ChecklistItemPriority,
  ChecklistItemStatus,
} from "@/utils/api";

interface MetaConfig {
  label: string;
  className: string;
}

interface ChecklistItemEditDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  stageTitle: string | null;
  form: {
    content: string;
    status: ChecklistItemStatus;
    priority: ChecklistItemPriority;
  };
  onFieldChange: (field: "content" | "status" | "priority", value: string) => void;
  onSubmit: () => void;
  onCancel: () => void;
  isSaving: boolean;
  error: string | null;
  statusOptions: ChecklistItemStatus[];
  priorityOptions: ChecklistItemPriority[];
  statusMeta: Record<ChecklistItemStatus, MetaConfig>;
  priorityMeta: Record<ChecklistItemPriority, MetaConfig>;
}

export default function ChecklistItemEditDialog({
  open,
  onOpenChange,
  stageTitle,
  form,
  onFieldChange,
  onSubmit,
  onCancel,
  isSaving,
  error,
  statusOptions,
  priorityOptions,
  statusMeta,
  priorityMeta,
}: ChecklistItemEditDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl space-y-6">
        <DialogHeader className="space-y-2 text-left">
          <DialogTitle>Edit task</DialogTitle>
          <DialogDescription>
            {stageTitle ? `Stage: ${stageTitle}` : "Update the checklist task details."}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="checklist-item-content">Task description</Label>
            <Textarea
              id="checklist-item-content"
              value={form.content}
              onChange={(event) => onFieldChange("content", event.target.value)}
              rows={4}
            />
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="checklist-item-status">Status</Label>
              <Select
                value={form.status}
                onValueChange={(value) => onFieldChange("status", value)}
              >
                <SelectTrigger id="checklist-item-status">
                  <SelectValue placeholder="Select status" />
                </SelectTrigger>
                <SelectContent>
                  {statusOptions.map((option) => (
                    <SelectItem key={option} value={option}>
                      {statusMeta[option].label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="checklist-item-priority">Priority</Label>
              <Select
                value={form.priority}
                onValueChange={(value) => onFieldChange("priority", value)}
              >
                <SelectTrigger id="checklist-item-priority">
                  <SelectValue placeholder="Select priority" />
                </SelectTrigger>
                <SelectContent>
                  {priorityOptions.map((option) => (
                    <SelectItem key={option} value={option}>
                      {priorityMeta[option].label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {error && (
            <div className="rounded-lg border border-destructive/40 bg-destructive/5 px-4 py-3 text-sm text-destructive">
              {error}
            </div>
          )}
        </div>

        <DialogFooter className="justify-end gap-2 sm:flex-row">
          <Button type="button" variant="ghost" onClick={onCancel} disabled={isSaving}>
            Cancel
          </Button>
          <Button type="button" onClick={onSubmit} disabled={isSaving}>
            {isSaving ? "Saving…" : "Save changes"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
