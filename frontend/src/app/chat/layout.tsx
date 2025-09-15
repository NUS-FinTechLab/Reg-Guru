import {SidebarProvider} from "@/components/ui/sidebar"
import {AppSidebar} from "./components/AppSidebar"
import React from "react";

export default function Layout({ children }: { children: React.ReactNode }) {
    return (
        <SidebarProvider>
            <AppSidebar />
            <main className={"container ml-0 md:ml-36"}>
                {children}
            </main>
        </SidebarProvider>
    )
}
