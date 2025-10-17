"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChevronDown } from "lucide-react";
import { motion } from "framer-motion";
import { fetchChat, sendChatMessage } from "@/utils/api";
import { AuthUser, ChatListItem, ChatMessageDTO, ChatSummary, Message } from "@/utils/api/types";
import { getStoredUser } from "@/utils/auth-client";
import ChatHeader from "./ChatHeader";
import ChatMessages from "./ChatMessages";
import ChatInput from "./ChatInput";

const mapDtoToMessage = (dto: ChatMessageDTO): Message => ({
    id: dto.id,
    text: dto.text,
    role: dto.role,
    timestamp: new Date(dto.createdAt),
    sources: dto.sources ?? [],
});

export default function ChatPage() {
    const router = useRouter();
    const params = useParams();
    const chatParam = Array.isArray(params?.chatId) ? params.chatId[0] : params?.chatId;
    const chatId = chatParam?.toString() ?? "";
    const searchParams = useSearchParams();

    const [authUser, setAuthUser] = useState<AuthUser | null>(null);
    const [, setChat] = useState<ChatSummary | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [region, setRegion] = useState("US");
    const [isTyping, setIsTyping] = useState(false);
    const [autoScroll, setAutoScroll] = useState(true);
    const [showScrollButton, setShowScrollButton] = useState(false);
    const [isLoadingHistory, setIsLoadingHistory] = useState(true);

    const scrollAreaRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const bootstrapInitialQuestion = useRef(false);

    useEffect(() => {
        const user = getStoredUser();
        if (!user) {
            router.replace("/login");
            return;
        }

        setAuthUser(user);

        const handleAuthChange = () => {
            const updated = getStoredUser();
            setAuthUser(updated);
            if (!updated) {
                router.replace("/login");
            }
        };

        window.addEventListener("auth-change", handleAuthChange);
        return () => {
            window.removeEventListener("auth-change", handleAuthChange);
        };
    }, [router]);

    useEffect(() => {
        if (inputRef.current) {
            inputRef.current.focus();
        }
    }, []);

    useEffect(() => {
        if (!chatId) {
            setIsLoadingHistory(false);
            return;
        }

        if (!authUser) {
            setIsLoadingHistory(false);
            return;
        }

        let isMounted = true;
        setIsLoadingHistory(true);

        fetchChat(chatId)
            .then((data) => {
                if (!isMounted) {
                    return;
                }
                if (!data.chat) {
                    setChat(null);
                    setMessages([]);
                    return;
                }

                setChat(data.chat);
                const mappedMessages = data.messages.map(mapDtoToMessage);
                setMessages(mappedMessages);

                const lastDto = data.messages.length > 0
                    ? data.messages[data.messages.length - 1]
                    : null;
                const chatListItem: ChatListItem = {
                    id: data.chat.id,
                    userId: data.chat.userId,
                    createdAt: data.chat.createdAt,
                    updatedAt: data.chat.updatedAt,
                    lastMessage: lastDto
                        ? {
                            text: lastDto.text,
                            role: lastDto.role,
                            createdAt: lastDto.createdAt,
                        }
                        : null,
                };

                window.dispatchEvent(
                    new CustomEvent<ChatListItem>("chat-updated", { detail: chatListItem }),
                );
            })
            .catch((error: unknown) => {
                if (!isMounted) {
                    return;
                }
                const err = error as Error;
                if (err.message !== "not_found") {
                    console.error("Failed to load chat history:", err);
                } else {
                    setChat(null);
                    setMessages([]);
                }
            })
            .finally(() => {
                if (isMounted) {
                    setIsLoadingHistory(false);
                }
            });

        return () => {
            isMounted = false;
        };
    }, [authUser, chatId]);

    useEffect(() => {
        if (autoScroll && messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [messages, autoScroll]);

    useEffect(() => {
        const scrollArea = scrollAreaRef.current;
        const handleScroll = () => {
            if (!scrollArea) {
                return;
            }
            const { scrollTop, scrollHeight, clientHeight } = scrollArea;
            const isAtBottom = scrollHeight - scrollTop - clientHeight < 20;
            setAutoScroll(isAtBottom);
            setShowScrollButton(!isAtBottom && messages.length > 0);
        };

        if (!scrollArea) {
            return;
        }

        scrollArea.addEventListener("scroll", handleScroll);
        return () => scrollArea.removeEventListener("scroll", handleScroll);
    }, [messages.length]);

    const scrollToBottom = () => {
        setAutoScroll(true);
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
        }
    };

    const formatTime = (date: Date) => {
        return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    };

    const formatDate = (date: Date) => {
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);

        const isToday = date.toDateString() === today.toDateString();
        const isYesterday = date.toDateString() === yesterday.toDateString();

        if (isToday) return "Today";
        if (isYesterday) return "Yesterday";
        return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
    };

    const handleSend = useCallback(async (text: string) => {
        if (!text.trim() || !chatId) {
            return;
        }

        if (!authUser) {
            router.replace("/login");
            return;
        }

        const placeholderId = `pending-${Date.now()}`;
        const userMessage: Message = {
            id: placeholderId,
            text,
            role: "user",
            timestamp: new Date(),
            pending: true,
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setAutoScroll(true);
        setIsTyping(true);

        try {
            const data = await sendChatMessage({
                chatId,
                text,
                region,
                userId: authUser.id,
            });

            setChat(data.chat);

            const resolvedChatId = data.chat.id;
            if (resolvedChatId !== chatId) {
                router.replace(`/modules/chat/${resolvedChatId}`);
            }

            const savedUser = mapDtoToMessage(data.messages.user);
            const botMessage = mapDtoToMessage(data.messages.ai);

            setMessages((prev) => {
                const withoutPlaceholder = prev.filter((msg) => msg.id !== placeholderId);
                return [...withoutPlaceholder, savedUser, botMessage];
            });

            if (data.chat) {
                const chatListItem: ChatListItem = {
                    id: resolvedChatId,
                    userId: data.chat.userId,
                    createdAt: data.chat.createdAt,
                    updatedAt: data.chat.updatedAt,
                    lastMessage: {
                        text: botMessage.text,
                        role: botMessage.role,
                        createdAt: botMessage.timestamp.toISOString(),
                    },
                };

                window.dispatchEvent(
                    new CustomEvent<ChatListItem>("chat-updated", { detail: chatListItem }),
                );
            }
        } catch (error) {
            console.error("Error sending message:", error);
            setMessages((prev) => {
                const updated = prev.map((msg) =>
                    msg.id === placeholderId ? { ...msg, pending: false } : msg
                );
                return [
                    ...updated,
                    {
                        id: `error-${Date.now()}`,
                        text: "Sorry, something went wrong. Please try again.",
                        role: "ai",
                        timestamp: new Date(),
                    },
                ];
            });
        } finally {
            setIsTyping(false);
        }
    }, [authUser, chatId, region, router]);

    useEffect(() => {
        if (!authUser || !chatId || isLoadingHistory) {
            return;
        }
        if (bootstrapInitialQuestion.current) {
            return;
        }

        if (messages.length > 0) {
            bootstrapInitialQuestion.current = true;
            return;
        }

        const initialQuestionText = searchParams.get("initialQuestion") ?? "";
        if (initialQuestionText.trim()) {
            bootstrapInitialQuestion.current = true;
            setInput(initialQuestionText);
            handleSend(initialQuestionText);
        } else {
            bootstrapInitialQuestion.current = true;
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [authUser, chatId, isLoadingHistory, messages.length, searchParams]);

    const messageGroups = useMemo(() => {
        const groups: { [key: string]: Message[] } = {};
        messages.forEach((message) => {
            const dateKey = message.timestamp.toDateString();
            if (!groups[dateKey]) {
                groups[dateKey] = [];
            }
            groups[dateKey].push(message);
        });

        return Object.entries(groups).map(([date, msgs]) => ({
            date: new Date(date),
            messages: msgs,
        }));
    }, [messages]);

    return (
        <div className="flex flex-col rounded-2xl container px-2 w-full h-screen">
            <ChatHeader isTyping={isTyping} region={region} onRegionChange={setRegion} />
            <ScrollArea className="flex-1 px-0 py-2 overflow-y-auto" ref={scrollAreaRef}>
                <ChatMessages
                    messageGroups={messageGroups}
                    isTyping={isTyping}
                    formatDate={formatDate}
                    formatTime={formatTime}
                    messagesEndRef={messagesEndRef}
                />
            </ScrollArea>

            {showScrollButton && (
                <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.8 }}
                    className="fixed bottom-24 right-8 z-10"
                >
                    <Button
                        onClick={scrollToBottom}
                        size="icon"
                        className="h-10 w-10 rounded-full bg-blue-500 hover:bg-blue-600 text-white shadow-lg"
                    >
                        <ChevronDown className="h-5 w-5" />
                    </Button>
                </motion.div>
            )}

            <ChatInput value={input} onChange={setInput} onSend={handleSend} inputRef={inputRef} />
        </div>
    );
}
