"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ChecklistDetailDTO, ChecklistItemPriority, ChecklistItemStatus, getChecklist } from "@/utils/api";

interface MetaConfig {
  label: string;
  className: string;
}

const STATUS_META: Record<ChecklistItemStatus, MetaConfig> = {
  not_started: {
    label: "Not started",
    className: "border-border/60 bg-muted/40 text-muted-foreground",
  },
  ongoing: {
    label: "Ongoing",
    className: "border-amber-400/40 bg-amber-500/10 text-amber-300",
  },
  finished: {
    label: "Finished",
    className: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
  },
};

const PRIORITY_META: Record<ChecklistItemPriority, MetaConfig> = {
  low: {
    label: "Low",
    className: "border-blue-400/30 bg-blue-500/10 text-blue-300",
  },
  medium: {
    label: "Medium",
    className: "border-indigo-400/40 bg-indigo-500/10 text-indigo-300",
  },
  high: {
    label: "High",
    className: "border-rose-400/40 bg-rose-500/10 text-rose-300",
  },
};

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

  useEffect(() => {
    if (!checklistId) {
      setNotFound(true);
      setIsLoading(false);
      return;
    }

    let isMounted = true;
    setIsLoading(true);
    setNotFound(false);

    getChecklist(checklistId)
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
      })
      .catch((error) => {
        console.error("Failed to fetch checklist", error);
        if (isMounted) {
          setNotFound(true);
          setChecklist(null);
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [checklistId]);

  const progressPercent = useMemo(() => {
    if (!checklist) {
      return 0;
    }
    const progress = checklist.progress ?? 0;
    const bounded = Math.max(0, Math.min(1, progress));
    return Math.round(bounded * 100);
  }, [checklist]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <main className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-6 py-10">
        <div className="flex items-center gap-3">
          <Button variant="ghost" onClick={() => router.push("/modules/compliance-checklist")}
            className="px-2">
            <ArrowLeft className="size-4" />
            Back
          </Button>
        </div>

        {isLoading ? (
          <div className="text-sm text-muted-foreground">Loading checklist…</div>
        ) : notFound || !checklist ? (
          <div className="rounded-xl border border-dashed border-border/60 p-8 text-sm text-muted-foreground">
            Checklist not found. It may have been deleted or you might not have access.
          </div>
        ) : (
          <>
            <Card>
              <CardHeader className="space-y-4">
                <div className="flex flex-col gap-3">
                  <CardTitle className="text-3xl font-semibold">
                    {checklist.title}
                  </CardTitle>
                  <CardDescription>{checklist.description}</CardDescription>
                </div>
                <div className="space-y-3">
                  <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                    <span>
                      Created {new Date(checklist.createdAt).toLocaleString()}
                    </span>
                    <span>• Updated {new Date(checklist.updatedAt).toLocaleString()}</span>
                    <span>
                      • {checklist.finishedItems} of {checklist.totalItems} completed
                    </span>
                    <span>• {progressPercent}% complete</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-primary transition-all"
                      style={{ width: `${progressPercent}%` }}
                    />
                  </div>
                </div>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-2xl font-semibold">Checklist items</CardTitle>
                <CardDescription>
                  Review each task, its current status, and priority.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {checklist.items.length === 0 ? (
                  <div className="rounded-lg border border-dashed border-border/60 p-6 text-sm text-muted-foreground">
                    No items yet. Add tasks to guide your compliance workstream.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {checklist.items.map((item) => {
                      const statusMeta = STATUS_META[item.status];
                      const priorityMeta = PRIORITY_META[item.priority];
                      return (
                        <div
                          key={item.id}
                          className="flex flex-col gap-3 rounded-xl border border-border/60 bg-muted/10 p-4"
                        >
                          <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                            <p className="text-base font-medium text-foreground">
                              {item.content}
                            </p>
                            <div className="flex flex-wrap items-center gap-2">
                              <Badge variant="outline" className={statusMeta.className}>
                                {statusMeta.label}
                              </Badge>
                              <Badge variant="outline" className={priorityMeta.className}>
                                Priority: {priorityMeta.label}
                              </Badge>
                            </div>
                          </div>
                          <div className="text-xs text-muted-foreground">
                            Updated {new Date(item.updatedAt).toLocaleString()}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </main>
    </div>
  );
}

