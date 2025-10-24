import type { ReactNode } from "react";

import { SidebarProvider } from "@/components/ui/sidebar";
import Sidebar from "@/components/layout/Sidebar";

export default function ModulesLayout({ children }: { children: ReactNode }) {
  return (
    <SidebarProvider>
      <Sidebar />
      <main className="container ml-0 w-full max-w-none px-4 pb-10 pt-6 md:ml-36">
        {children}
      </main>
    </SidebarProvider>
  );
}
