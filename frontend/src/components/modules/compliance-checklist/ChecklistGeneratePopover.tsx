"use client";

import { Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

interface ChecklistGeneratePopoverProps {
  label?: string;
}

export default function ChecklistGeneratePopover({ label = "Generate checklist" }: ChecklistGeneratePopoverProps) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button>
          <Sparkles className="size-4" />
          {label}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-96" />
    </Popover>
  );
}

