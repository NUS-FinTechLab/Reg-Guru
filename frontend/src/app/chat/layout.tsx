import type { ReactNode } from "react";

import { SidebarProvider } from "@/components/ui/sidebar";

import { AppSidebar } from "@/app/chat/components/AppSidebar";

export default function ChatLayout({ children }: { children: ReactNode }) {
  return (
    <SidebarProvider>
      <AppSidebar />
      <main className="container ml-0 w-full max-w-none px-4 pb-10 pt-6 md:ml-36">
        {children}
      </main>
    </SidebarProvider>
  );
}
