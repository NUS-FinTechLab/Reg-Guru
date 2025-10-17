"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import ChecklistCard from "@/components/modules/compliance-checklist/ChecklistCard";
import ChecklistGeneratePopover from "@/components/modules/compliance-checklist/ChecklistGeneratePopover";
import { Badge } from "@/components/ui/badge";
import { getStoredUser } from "@/utils/auth-client";
import { ChecklistSummaryDTO, listChecklists, type AuthUser } from "@/utils/api";

export default function ComplianceChecklistPage() {
  const router = useRouter();
  const [checklists, setChecklists] = useState<ChecklistSummaryDTO[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isGeneratorOpen, setIsGeneratorOpen] = useState(false);
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    const updateUser = () => {
      const stored = getStoredUser();
      if (!stored) {
        setAuthUser(null);
        setIsLoading(false);
        router.replace("/login");
        return;
      }

      setAuthUser(stored);
    };

    updateUser();
    window.addEventListener("auth-change", updateUser);
    return () => window.removeEventListener("auth-change", updateUser);
  }, [router]);

  useEffect(() => {
    if (!authUser) {
      setChecklists([]);
      return;
    }

    let isMounted = true;

    const loadChecklists = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await listChecklists();
        if (isMounted) {
          setChecklists(data);
        }
      } catch (err) {
        console.error(err);
        if (isMounted) {
          setError("Unable to load checklists");
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    loadChecklists();

    return () => {
      isMounted = false;
    };
  }, [authUser]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6 py-10 transition duration-200">
        <header className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-3">
            <h1 className="text-4xl font-semibold tracking-tight">
              Compliance Checklists
            </h1>
            <p className="max-w-2xl text-muted-foreground">
              Browse every checklist generated for your organisation. Track
              progress at a glance and open a checklist to review each task.
            </p>
          </div>

          <ChecklistGeneratePopover
            open={isGeneratorOpen}
            onOpenChange={setIsGeneratorOpen}
          />
        </header>

        {error && (
          <Badge variant="destructive" className="w-fit">
            {error}
          </Badge>
        )}

        {isLoading ? (
          <div className="text-sm text-muted-foreground">Loading checklists…</div>
        ) : checklists.length === 0 ? (
          <div className="rounded-xl border border-dashed border-border/60 p-8 text-sm text-muted-foreground">
            No checklists yet. Generate your first one to get started.
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2">
            {checklists.map((checklist) => (
              <ChecklistCard key={checklist.id} checklist={checklist} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
