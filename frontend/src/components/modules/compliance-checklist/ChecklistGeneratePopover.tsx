"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { requestChecklistGeneration } from "@/utils/api";

interface ChecklistGeneratePopoverProps {
  label?: string;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

type RegionValue = "US" | "SG" | "EU";

const regionOptions: RegionValue[] = ["US", "SG", "EU"];

export default function ChecklistGeneratePopover({
  label = "Generate checklist",
  open: controlledOpen,
  onOpenChange,
}: ChecklistGeneratePopoverProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const actualOpen = controlledOpen ?? internalOpen;

  const setOpen = useCallback(
    (value: boolean) => {
      if (controlledOpen === undefined) {
        setInternalOpen(value);
      }
      onOpenChange?.(value);
    },
    [controlledOpen, onOpenChange],
  );

  const [mission, setMission] = useState("");
  const [context, setContext] = useState("");
  const [region, setRegion] = useState<RegionValue>("US");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  useEffect(() => {
    if (!actualOpen) {
      setMission("");
      setContext("");
      setRegion("US");
      setFeedback(null);
      return;
    }

    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = originalOverflow;
    };
  }, [actualOpen]);

  const handleClose = useCallback(() => {
    setOpen(false);
  }, [setOpen]);

  const handleSubmit = useCallback(async () => {
    const trimmedMission = mission.trim();
    if (!trimmedMission) {
      setFeedback("Please provide a high-level business mission before generating a checklist.");
      return;
    }

    setIsSubmitting(true);
    setFeedback(null);

    try {
      const result = await requestChecklistGeneration({
        mission: trimmedMission,
        context: context.trim(),
        region,
      });

      if (!result.ok) {
        setFeedback(result.message || "Checklist generation is not available yet.");
        return;
      }

      handleClose();
      window.location.reload();
    } catch (error) {
      console.error("Failed to request checklist generation", error);
      setFeedback("Failed to request checklist generation. Please try again later.");
    } finally {
      setIsSubmitting(false);
    }
  }, [context, region, mission, handleClose]);

  return (
    <Dialog open={actualOpen} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Sparkles className="size-4" />
          {label}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-3xl space-y-6">
        <DialogHeader className="space-y-3 text-left">
          <DialogTitle className="text-2xl">Generate checklist with assistant</DialogTitle>
          <DialogDescription>
            Provide a short mission statement, choose the region for embeddings, and add any supporting
            context. We&apos;ll use this to craft an AI-assisted checklist.
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4">
          <div className="space-y-2">
            <Label htmlFor="checklist-region">Region</Label>
            <Select value={region} onValueChange={(value) => setRegion(value as RegionValue)}>
              <SelectTrigger id="checklist-region" className="w-32">
                <SelectValue placeholder="Select region" />
              </SelectTrigger>
              <SelectContent>
                {regionOptions.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="business-mission">High-level business mission</Label>
            <Textarea
              id="business-mission"
              placeholder="Launch a digital payment token exchange serving accredited investors in Singapore."
              value={mission}
              onChange={(event) => setMission(event.target.value)}
              rows={4}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="additional-context">Additional context</Label>
            <Textarea
              id="additional-context"
              placeholder="Mention known partners, timelines, risk areas, or other constraints."
              value={context}
              onChange={(event) => setContext(event.target.value)}
              rows={4}
            />
          </div>
        </div>

        {feedback && (
          <div className="rounded-lg border border-border/60 bg-muted/20 p-3 text-sm text-muted-foreground">
            {feedback}
          </div>
        )}

        <DialogFooter className="justify-end gap-2 sm:flex-row">
          <Button variant="ghost" onClick={handleClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting}
            aria-busy={isSubmitting}
          >
            {isSubmitting ? (
              <span className="flex items-center gap-2">
                <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                Submitting…
              </span>
            ) : (
              "Generate"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
