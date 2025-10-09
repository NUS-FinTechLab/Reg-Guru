import type { LucideIcon } from "lucide-react";
import { ClipboardCheck, MessageSquare } from "lucide-react";

export type WorkspaceModule = {
  name: string;
  description: string;
  href: string;
  icon: LucideIcon;
};

export const WORKSPACE_MODULES: WorkspaceModule[] = [
  {
    name: "Chat",
    description: "Document Q&A assistant",
    href: "/chat",
    icon: MessageSquare,
  },
  {
    name: "Compliance Checklist",
    description: "Track regulatory tasks and progress",
    href: "/modules/compliance-checklist",
    icon: ClipboardCheck,
  },
];
