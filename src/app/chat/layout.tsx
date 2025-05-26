import {SidebarProvider} from "@/components/ui/sidebar"
import {AppSidebar} from "./components/app-sidebar"
import React from "react";

export default function Layout({ children }: { children: React.ReactNode }) {
    return (
        <SidebarProvider>
            <AppSidebar />
            <main className={"container"}>
                {children}
            </main>
        </SidebarProvider>
    )
}
