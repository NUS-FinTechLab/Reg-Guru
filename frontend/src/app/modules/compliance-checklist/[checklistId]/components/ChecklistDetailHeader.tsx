"use client";

import { motion } from "framer-motion";

import type { ChecklistDetailDTO } from "@/utils/api";

interface ChecklistDetailHeaderProps {
  checklist: ChecklistDetailDTO;
  progressPercent: number;
  getRelativeTime: (dateString: string) => string;
}

export default function ChecklistDetailHeader({
  checklist,
  progressPercent,
  getRelativeTime,
}: ChecklistDetailHeaderProps) {
  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-4">
        <h1 className="text-5xl font-semibold leading-tight tracking-tight text-foreground">
          {checklist.title}
        </h1>
        <p className="max-w text-base leading-relaxed text-muted-foreground">
          {checklist.description}
        </p>
      </div>

      <div className="overflow-hidden rounded-2xl border border-border/60 bg-card/60 p-6 shadow-sm backdrop-blur">
        <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
          <span>Last updated {getRelativeTime(checklist.updatedAt)}</span>
          <span>• {checklist.stageCount} {checklist.stageCount === 1 ? "stage" : "stages"}</span>
          <span>• {checklist.finishedItems} of {checklist.totalItems} completed</span>
          <span>•
            <span className="ml-1 font-semibold text-primary">{progressPercent}% complete</span>
          </span>
        </div>
        <div className="mt-4 h-3 w-full overflow-hidden rounded-full bg-muted">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progressPercent}%` }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className="h-full rounded-full bg-gradient-to-r from-primary to-primary/70"
          />
        </div>
      </div>
    </div>
  );
}
