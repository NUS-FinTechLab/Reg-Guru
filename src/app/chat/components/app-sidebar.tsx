import {ArrowRight, ArrowUp, Cog, CogIcon, FileText, Paperclip, Plus, Search} from "lucide-react"

import {
    Sidebar,
    SidebarContent, SidebarFooter,
    SidebarGroup,
    SidebarGroupContent,
    SidebarGroupLabel, SidebarHeader,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
} from "@/components/ui/sidebar"
import {Tooltip, TooltipContent, TooltipProvider, TooltipTrigger,} from "@/components/ui/tooltip"
import Image from "next/image";
import {Button} from "@/components/ui/button";
import Link from "next/link";
import {Input} from "@/components/ui/input";
import {AnimatePresence, motion} from "framer-motion";

// Menu items.
const items = [
    {
        title: "Dummy Chat Message 1",
        url: "",
        icon: FileText,
    },
    {
        title: "Dummy Chat Message 2",
        url: "#",
        icon: Paperclip,
        time: "10 mins ago"
    },
    {
        title: "Dummy Chat Message 3",
        url: "#",
        icon: Paperclip,
    },
    {
        title: "Dummy Chat Message 4",
        url: "#",
        icon: Paperclip,
    },
]

export function AppSidebar() {
    return (
        <Sidebar variant={"floating"} className={""}>
            <SidebarHeader>
                <div className={"my-2 px-2 flex justify-between items-center"} >
                    <div className="flex items-center gap-2">
                        <div className="relative">
                            <Image
                                src="/logo.png"
                                alt="Bot avatar"
                                width={40}
                                height={40}
                                className="rounded-full border-2 border-blue-200"
                            />
                            <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-white"></span>
                        </div>
                        <div>
                            <h1 className="font-bold font-mono uppercase text-sm">reg-guru</h1>
                            <p className="text-xs text-gray-500">Online</p>
                        </div>
                    </div>
                    <div>
                        <TooltipProvider>
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <Button asChild className={"cursor-pointer w-10 h-10 rounded-full  text-gray-400"} variant={"outline"}>
                                        <Link href={"/chat"}>
                                            <Plus className={""}/>
                                        </Link>
                                    </Button>
                                </TooltipTrigger>
                                <TooltipContent>
                                    <p>New Chat</p>
                                </TooltipContent>
                            </Tooltip>
                        </TooltipProvider>
                    </div>
                </div>
            </SidebarHeader>
            <SidebarContent className={""}>
                <div>
                    <div className="flex items-center gap-2 my-4 mx-4">
                        <div className="relative flex-1 focus:ring-0">
                            <Input
                                placeholder="Search chats"
                                className="pl-4 pr-12 py-5 max-w-lg w-full rounded-full"
                            />
                                    <div
                                        className="absolute right-1 top-1/2 transform -translate-y-1/2"
                                    >
                                        <Button
                                            // onClick={handleSend}
                                            size="icon"
                                            className="h-8 w-8 rounded-full cursor-pointer "
                                        >
                                            <Search className="h-4 w-4"/>
                                        </Button>
                                    </div>
                        </div>
                    </div>
                </div>
                <SidebarGroup>
                    <SidebarGroupLabel>
                        <div className={"w-full flex justify-between items-center"}>
                            <p className={"font-mono uppercase "}>UPLOADED DOCUMENTS</p>
                            <Link href={"/chat/history"}>
                                <p className={" text-xs"}>See all</p>
                            </Link>
                        </div>
                    </SidebarGroupLabel>
                    <SidebarGroupContent className={""}>
                        <SidebarMenu>
                            
                        </SidebarMenu>
                    </SidebarGroupContent>
                </SidebarGroup>
            </SidebarContent>
            <SidebarFooter className={"absolute bottom-4"}>
                <div className={"px-2"}>
                    <Button asChild className={"cursor-pointer w-10 h-10 rounded-full  text-gray-400"} variant={"outline"}>
                        <Link href={"#"}>
                            <Cog className={""}/>
                        </Link>
                    </Button>
                </div>
            </SidebarFooter>
        </Sidebar>
    )
}
