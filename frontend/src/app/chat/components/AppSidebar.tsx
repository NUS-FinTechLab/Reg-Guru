"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { Cog, Plus, Search } from "lucide-react";

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
import { getChatHistoryEntries, ChatHistoryEntry } from "@/utils/api";
import { getStoredUser } from "@/utils/auth-client";

export function AppSidebar() {
    const router = useRouter();
    const [historyEntries, setHistoryEntries] = useState<ChatHistoryEntry[]>([]);
    const [searchTerm, setSearchTerm] = useState("");
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let isMounted = true;
        const user = getStoredUser();

        if (!user) {
            if (isMounted) {
                setError("Log in to view your chat history");
                setIsLoading(false);
            }
            return () => {
                isMounted = false;
            };
        }

        setIsLoading(true);

        getChatHistoryEntries()
            .then((data) => {
                if (isMounted) {
                    setHistoryEntries(data);
                }
            })
            .catch((err: unknown) => {
                console.error("Failed to load chat history:", err);
                if (isMounted) {
                    setError("Unable to load chat history");
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
        const handleCreated = (event: Event) => {
            const customEvent = event as CustomEvent<ChatHistoryEntry>;
            const newEntry = customEvent.detail;
            if (!newEntry) {
                return;
            }
            setHistoryEntries((prev) => {
                if (prev.some((item) => item.id === newEntry.id)) {
                    return prev;
                }
                return [newEntry, ...prev];
            });
        };

        window.addEventListener("chat-history-created", handleCreated as EventListener);
        return () => {
            window.removeEventListener("chat-history-created", handleCreated as EventListener);
        };
    }, []);

    const filteredEntries = useMemo(() => {
        const term = searchTerm.toLowerCase();
        return historyEntries.filter((entry) =>
            entry.queryText.toLowerCase().includes(term)
        );
    }, [historyEntries, searchTerm]);

    const handleHistorySelect = (entry: ChatHistoryEntry) => {
        if (entry.chatExternalId) {
            router.push(`/chat/${entry.chatExternalId}`);
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
                            <p className="text-sm text-gray-500">Loading chat history...</p>
                        )}
                        {!isLoading && error && (
                            <p className="text-sm text-red-500">{error}</p>
                        )}
                        {!isLoading && !error && filteredEntries.length === 0 && (
                            <p className="text-sm text-gray-500">No chat history yet.</p>
                        )}
                        {!isLoading && !error && filteredEntries.length > 0 && (
                            <ul className="space-y-3">
                                {filteredEntries.map((entry) => (
                                    <li key={entry.id}>
                                        <button
                                            type="button"
                                            onClick={() => handleHistorySelect(entry)}
                                            className="w-full text-left p-3 rounded-xl border hover:border-blue-300 transition"
                                        >
                                            <p className="text-sm font-medium truncate">{entry.queryText}</p>
                                            <p className="text-xs text-gray-500 mt-1">
                                                {new Date(entry.createdAt).toLocaleString()}
                                            </p>
                                        </button>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                </div>
            </SidebarContent>
            <SidebarFooter className="absolute bottom-4">
                <div className="px-2">
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
