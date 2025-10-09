"use client";

import { useEffect, useMemo, useState, type SyntheticEvent } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { Cog, LayoutGrid, Plus, Search } from "lucide-react";

import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarHeader,
} from "@/components/ui/sidebar";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { listChats, ChatListItem } from "@/utils/api";
import { getStoredUser } from "@/utils/auth-client";

export function AppSidebar() {
    const router = useRouter();
    const [chats, setChats] = useState<ChatListItem[]>([]);
    const [searchTerm, setSearchTerm] = useState("");
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const handleImageError = (event: SyntheticEvent<HTMLImageElement>) => {
        event.currentTarget.style.visibility = "hidden";
    };

    useEffect(() => {
        let isMounted = true;
        const user = getStoredUser();

        if (!user) {
            if (isMounted) {
                setError("Log in to view your chats");
                setIsLoading(false);
            }
            return () => {
                isMounted = false;
            };
        }

        setIsLoading(true);

        listChats()
            .then((data) => {
                if (isMounted) {
                    const sorted = [...data].sort(
                        (a, b) =>
                            new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime(),
                    );
                    setChats(sorted);
                }
            })
            .catch((err: unknown) => {
                console.error("Failed to load chats:", err);
                if (isMounted) {
                    setError("Unable to load chats");
                }
            })
            .finally(() => {
                if (isMounted) {
                    setIsLoading(false);
                }
            });

        return () => {
            isMounted = false;
        };
    }, []);

    useEffect(() => {
        const handleUpdated = (event: Event) => {
            const customEvent = event as CustomEvent<ChatListItem>;
            const updatedChat = customEvent.detail;
            if (!updatedChat) {
                return;
            }
            setChats((prev) => {
                const without = prev.filter((item) => item.id !== updatedChat.id);
                const next = [updatedChat, ...without];
                return next.sort(
                    (a, b) =>
                        new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime(),
                );
            });
        };

        window.addEventListener("chat-updated", handleUpdated as EventListener);
        return () => {
            window.removeEventListener("chat-updated", handleUpdated as EventListener);
        };
    }, []);

    const filteredEntries = useMemo(() => {
        const term = searchTerm.toLowerCase();
        return chats.filter((chat) => {
            const preview = chat.lastMessage?.text?.toLowerCase() ?? "";
            return preview.includes(term) || chat.id.toLowerCase().includes(term);
        });
    }, [chats, searchTerm]);

    const handleChatSelect = (chat: ChatListItem) => {
        if (chat.id) {
            router.push(`/chat/${chat.id}`);
        }
    };

    return (
        <Sidebar variant="sidebar" className="w-full max-w-sm">
            <SidebarHeader>
                <div className="my-2 px-2 flex justify-between items-center">
                    <div className="flex items-center gap-2">
                        <div className="relative">
                            <Image
                                src="/logo.png"
                                alt="Bot avatar"
                                width={40}
                                height={40}
                                className="rounded-full border-2 border-blue-200"
                                onError={handleImageError}
                            />
                            <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-white"></span>
                        </div>
                        <div>
                            <h1 className="font-bold font-mono uppercase text-sm">reg-guru</h1>
                            <p className="text-xs text-gray-500">Online</p>
                        </div>
                    </div>
                    <TooltipProvider>
                        <Tooltip>
                            <TooltipTrigger asChild>
                                <Button
                                    asChild
                                    className="cursor-pointer w-10 h-10 rounded-full text-gray-400"
                                    variant="outline"
                                >
                                    <Link href="/chat">
                                        <Plus />
                                    </Link>
                                </Button>
                            </TooltipTrigger>
                            <TooltipContent>
                                <p>New Chat</p>
                            </TooltipContent>
                        </Tooltip>
                    </TooltipProvider>
                </div>
            </SidebarHeader>
            <SidebarContent>
                <div className="flex flex-col h-full">
                    <div className="flex items-center gap-2 my-4 mx-4">
                        <div className="relative flex-1 focus:ring-0">
                            <Input
                                placeholder="Search chats"
                                value={searchTerm}
                                onChange={(event) => setSearchTerm(event.target.value)}
                                className="pl-4 pr-12 py-5 max-w-lg w-full rounded-full"
                            />
                            <div className="absolute right-1 top-1/2 transform -translate-y-1/2">
                                <Button size="icon" className="h-8 w-8 rounded-full" variant="outline">
                                    <Search className="h-4 w-4" />
                                </Button>
                            </div>
                        </div>
                    </div>
                    <div className="px-4 pb-6 overflow-y-auto">
                        {isLoading && (
                            <p className="text-sm text-gray-500">Loading chats...</p>
                        )}
                        {!isLoading && error && (
                            <p className="text-sm text-red-500">{error}</p>
                        )}
                        {!isLoading && !error && filteredEntries.length === 0 && (
                            <p className="text-sm text-gray-500">No conversations yet.</p>
                        )}
                        {!isLoading && !error && filteredEntries.length > 0 && (
                            <ul className="space-y-3">
                                {filteredEntries.map((chat) => {
                                    const preview = chat.lastMessage?.text ?? "Start a conversation";
                                    const timestamp = chat.lastMessage?.createdAt ?? chat.updatedAt;
                                    return (
                                        <li key={chat.id}>
                                            <button
                                                type="button"
                                                onClick={() => handleChatSelect(chat)}
                                                className="w-full text-left p-3 rounded-xl border hover:border-blue-300 transition"
                                            >
                                                <p className="text-sm font-medium truncate">
                                                    {preview}
                                                </p>
                                                <p className="text-xs text-gray-500 mt-1">
                                                    {new Date(timestamp).toLocaleString()}
                                                </p>
                                            </button>
                                        </li>
                                    );
                                })}
                            </ul>
                        )}
                    </div>
                </div>
            </SidebarContent>
            <SidebarFooter className="mt-auto px-4 pb-4">
                <div className="flex items-center justify-between gap-2">
                    <Button
                        onClick={() => router.push("/modules")}
                        size="sm"
                        variant="ghost"
                        className="rounded-full"
                    >
                        <LayoutGrid className="mr-1 h-3.5 w-3.5" />
                        Workspace
                    </Button>
                    <Button asChild className="cursor-pointer w-10 h-10 rounded-full text-gray-400" variant="outline">
                        <Link href="#">
                            <Cog />
                        </Link>
                    </Button>
                </div>
            </SidebarFooter>
        </Sidebar>
    );
}
