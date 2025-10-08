import type { ReactNode } from "react";

import ModuleNav, { ModuleNavMobile } from "./module-nav";

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <ModuleNav />
      <div className="flex-1 overflow-y-auto">
        <ModuleNavMobile />
        <div className="pb-6">
          {children}
        </div>
      </div>
    </div>
  );
}
