"use client";

import { KeyboardEvent, useCallback } from "react";
import { useRouter } from "next/navigation";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ChecklistSummaryDTO } from "@/utils/api";

interface ChecklistCardProps {
  checklist: ChecklistSummaryDTO;
  onSelect?: (checklistId: string) => void;
}

const clampProgress = (value: number) => {
  if (!Number.isFinite(value)) {
    return 0;
  }
  if (value < 0) return 0;
  if (value > 1) return 1;
  return value;
};

export default function ChecklistCard({ checklist, onSelect }: ChecklistCardProps) {
  const router = useRouter();
  const progress = clampProgress(checklist.progress);
  const progressPercent = Math.round(progress * 100);
  const { totalItems, finishedItems } = checklist;

  const handleSelect = useCallback(() => {
    if (onSelect) {
      onSelect(checklist.id);
    } else if (checklist.id) {
      router.push(`/modules/compliance-checklist/${checklist.id}`);
    }
  }, [checklist.id, onSelect, router]);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent<HTMLDivElement>) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        handleSelect();
      }
    },
    [handleSelect],
  );

  return (
    <Card
      role="button"
      tabIndex={0}
      onClick={handleSelect}
      onKeyDown={handleKeyDown}
      className="cursor-pointer transition-colors hover:border-primary/60"
    >
      <CardHeader>
        <CardTitle className="text-2xl font-semibold">{checklist.title}</CardTitle>
        <CardDescription>{checklist.description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-2 text-sm">
          <span className="font-medium text-foreground">
            {finishedItems} of {totalItems} completed
          </span>
          <span className="text-muted-foreground">({progressPercent}% done)</span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
          <div
            className="h-full rounded-full bg-primary transition-all"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </CardContent>
    </Card>
  );
}
