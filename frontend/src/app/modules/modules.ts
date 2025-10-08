import type { LucideIcon } from "lucide-react";
import { MessageSquare } from "lucide-react";

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
];
