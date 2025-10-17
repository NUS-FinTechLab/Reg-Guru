"use client";

import { memo } from "react";
import { ChevronDown, Loader2, Pencil, Trash2 } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

import type {
  ChecklistItemDTO,
  ChecklistItemPriority,
  ChecklistItemStatus,
  ChecklistStageDTO,
} from "@/utils/api";

interface MetaConfig {
  label: string;
  className: string;
}

interface ChecklistStageListProps {
  stages: ChecklistStageDTO[];
  expandedStages: Record<string, boolean>;
  onToggleStage: (stageId: string) => void;
  statusMeta: Record<ChecklistItemStatus, MetaConfig>;
  priorityMeta: Record<ChecklistItemPriority, MetaConfig>;
  itemDecoration: Record<ChecklistItemStatus, string>;
  getRelativeTime: (dateString: string) => string;
  onEditItem: (item: ChecklistItemDTO) => void;
  onDeleteItem: (item: ChecklistItemDTO) => void;
  updatingItemStatusIds: Set<string>;
  pendingDeleteItemId: string | null;
  isDeletingItem: boolean;
}

function StageListContent({
  stages,
  expandedStages,
  onToggleStage,
  statusMeta,
  priorityMeta,
  itemDecoration,
  getRelativeTime,
  onEditItem,
  onDeleteItem,
  updatingItemStatusIds,
  pendingDeleteItemId,
  isDeletingItem,
}: ChecklistStageListProps) {
  if (stages.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-border/60 bg-muted/30 p-10 text-center text-sm text-muted-foreground">
        No stages yet. Add a stage to structure your compliance tasks.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {stages.map((stage, stageIndex) => {
        const stageItems = stage.items;
        const completedInStage = stageItems.filter((item) => item.status === "finished").length;
        const stageProgress = stageItems.length > 0 ? Math.round((completedInStage / stageItems.length) * 100) : 0;
        const isExpanded = expandedStages[stage.id] ?? true;

        return (
          <motion.div
            key={stage.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: stageIndex * 0.08 }}
            className="overflow-hidden rounded-2xl border border-border/60 bg-card/60 shadow-sm transition-shadow duration-300 hover:shadow-md"
          >
            <button
              type="button"
              onClick={() => onToggleStage(stage.id)}
              aria-expanded={isExpanded}
              className="flex w-full items-start gap-6 p-6 text-left transition-colors hover:bg-muted/30"
            >
              <div className="flex-shrink-0">
                <div className="flex size-14 items-center justify-center rounded-full border-2 border-primary/30 bg-primary/10 text-lg font-semibold text-primary shadow-sm">
                  {stageIndex + 1}
                </div>
              </div>
              <div className="min-w-0 flex-1 space-y-3">
                <div className="space-y-2">
                  <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                    <h3 className="text-2xl font-semibold leading-tight text-foreground">
                      {stage.title}
                    </h3>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{completedInStage} of {stageItems.length} completed</span>
                      <span>• {stageProgress}%</span>
                    </div>
                  </div>
                  {stage.description ? (
                    <p className="text-sm leading-relaxed text-muted-foreground">
                      {stage.description}
                    </p>
                  ) : null}
                  {stage.referenceLinks?.length ? (
                    <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                      <span>Stage references:</span>
                      {stage.referenceLinks.map((reference, index) => {
                        const label = reference.title?.trim() || reference.url?.trim() || `Reference ${index + 1}`;
                        if (!label) {
                          return null;
                        }
                        return reference.url ? (
                          <a
                            key={`${stage.id}-reference-${index}`}
                            href={reference.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="underline-offset-2 transition hover:text-primary hover:underline"
                          >
                            {label}
                          </a>
                        ) : (
                          <span key={`${stage.id}-reference-${index}`}>{label}</span>
                        );
                      })}
                    </div>
                  ) : null}
                </div>
              </div>
              <div className="flex-shrink-0 pt-2">
                <ChevronDown
                  className={`size-5 text-muted-foreground transition-transform duration-300 ${isExpanded ? "rotate-180" : "rotate-0"}`}
                />
              </div>
            </button>

            <AnimatePresence initial={false}>
              {isExpanded && (
                <motion.div
                  key="stage-content"
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3, ease: "easeInOut" }}
                  className="overflow-hidden"
                >
                  <div className="border-t border-border/50 bg-muted/10 px-6 py-5">
                    {stageItems.length === 0 ? (
                      <div className="rounded-xl border border-dashed border-border/50 bg-background/60 p-6 text-center text-sm text-muted-foreground">
                        No items in this stage yet.
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {stageItems.map((item, itemIndex) => {
                          const statusClasses = statusMeta[item.status];
                          const priorityClasses = priorityMeta[item.priority];
                          const decorationClass = itemDecoration[item.status] ?? itemDecoration.not_started;
                          const isItemUpdating = updatingItemStatusIds.has(item.id);
                          const isPendingDeletion = pendingDeleteItemId === item.id && isDeletingItem;
                          const isBusy = isItemUpdating || isPendingDeletion;

                          return (
                            <motion.div
                              key={item.id}
                              initial={{ opacity: 0, x: -12 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: itemIndex * 0.05 }}
                              aria-busy={isBusy}
                              className={`group relative flex gap-4 rounded-xl border p-5 text-sm shadow-sm transition-all duration-200 hover:shadow-md ${decorationClass}`}
                            >
                              {isBusy ? (
                                <div className="pointer-events-none absolute inset-0 z-20 flex items-center justify-center rounded-xl bg-background/80 backdrop-blur-sm">
                                  <span
                                    className={`flex items-center gap-2 text-xs font-medium ${isPendingDeletion ? "text-destructive" : "text-muted-foreground"}`}
                                  >
                                    <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                                    {isPendingDeletion ? "Deleting…" : "Saving…"}
                                  </span>
                                </div>
                              ) : null}
                              <div className="absolute -top-3 right-3 z-10">
                                <div className="pointer-events-none -translate-y-1 rounded-full border border-border bg-background/95 px-1 py-0 opacity-0 shadow-sm backdrop-blur transition-all duration-150 group-hover:pointer-events-auto group-hover:-translate-y-2 group-hover:opacity-100 group-focus-within:pointer-events-auto group-focus-within:-translate-y-2 group-focus-within:opacity-100">
                                  <div className="flex items-center gap-0.5">
                                    <Button
                                      type="button"
                                      size="icon"
                                      variant="ghost"
                                      className="size-6 rounded-full text-muted-foreground hover:text-primary"
                                      disabled={isItemUpdating || isPendingDeletion}
                                      onClick={() => onEditItem(item)}
                                      aria-label="Edit task"
                                    >
                                      <Pencil className="size-3" />
                                    </Button>
                                    <span className="h-3 w-px bg-border/60" aria-hidden="true" />
                                    <Button
                                      type="button"
                                      size="icon"
                                      variant="ghost"
                                      className="size-6 rounded-full text-muted-foreground hover:text-destructive"
                                      disabled={isPendingDeletion}
                                      onClick={() => onDeleteItem(item)}
                                      aria-label="Delete task"
                                    >
                                      <Trash2 className="size-3" />
                                    </Button>
                                  </div>
                                </div>
                              </div>

                              <div className="flex-1 min-w-0 space-y-3">
                                <p className="text-base font-medium leading-relaxed">
                                  {item.content}
                                </p>
                                <div className="flex flex-wrap items-center gap-2">
                                  <Badge variant="outline" className={`${statusClasses.className} text-xs font-medium`}>
                                    {statusClasses.label}
                                  </Badge>
                                  <Badge variant="outline" className={`${priorityClasses.className} text-xs font-medium`}>
                                    {priorityClasses.label} priority
                                  </Badge>
                                  <span className="text-xs text-muted-foreground">
                                    Updated {getRelativeTime(item.updatedAt)}
                                  </span>
                                </div>
                                {item.referenceLinks?.length ? (
                                  <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                                    <span>References:</span>
                                    {item.referenceLinks.map((reference, index) => {
                                      const label = reference.title?.trim() || reference.url?.trim() || `Reference ${index + 1}`;
                                      if (!label) {
                                        return null;
                                      }
                                      return reference.url ? (
                                        <a
                                          key={`${item.id}-reference-${index}`}
                                          href={reference.url}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          className="underline-offset-2 transition hover:text-primary hover:underline"
                                        >
                                          {label}
                                        </a>
                                      ) : (
                                        <span key={`${item.id}-reference-${index}`}>{label}</span>
                                      );
                                    })}
                                  </div>
                                ) : null}
                              </div>
                            </motion.div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        );
      })}
    </div>
  );
}

function ChecklistStageList(props: ChecklistStageListProps) {
  return (
    <div className="space-y-6 pb-10">
      <div className="space-y-2 pt-2">
        <h2 className="text-3xl font-semibold text-foreground">Stages &amp; Tasks</h2>
        <p className="text-sm text-muted-foreground">
          Review each stage and the tasks within to organise delivery of your compliance workstream.
        </p>
      </div>

      <StageListContent {...props} />
    </div>
  );
}

export default memo(ChecklistStageList);
