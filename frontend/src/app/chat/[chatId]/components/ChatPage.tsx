"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChevronDown } from "lucide-react";
import { motion } from "framer-motion";
import { createSavedQuery, fetchChatHistory, sendChatMessage } from "@/utils/api";
import { ChatMessageDTO, ChatSession, Message } from "@/utils/api/types";
import ChatHeader from "./ChatHeader";
import ChatMessages from "./ChatMessages";
import ChatInput from "./ChatInput";

const mapDtoToMessage = (dto: ChatMessageDTO): Message => ({
    id: dto.id,
    text: dto.text,
    role: dto.role,
    timestamp: new Date(dto.timestamp),
    sources: dto.sources ?? [],
});

export default function ChatPage() {
    const params = useParams();
    const chatParam = Array.isArray(params?.chatId) ? params.chatId[0] : params?.chatId;
    const chatId = chatParam?.toString() ?? "";
    const searchParams = useSearchParams();

    const [, setSession] = useState<ChatSession | null>(null);
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
        if (inputRef.current) {
            inputRef.current.focus();
        }
    }, []);

    useEffect(() => {
        if (!chatId) {
            setIsLoadingHistory(false);
            return;
        }

        let isMounted = true;
        setIsLoadingHistory(true);

        fetchChatHistory(chatId)
            .then((data) => {
                if (!isMounted) {
                    return;
                }
                setSession(data.session);
                setRegion(data.session.region.toUpperCase());
                setMessages(data.messages.map(mapDtoToMessage));
            })
            .catch((error: unknown) => {
                if (!isMounted) {
                    return;
                }
                const err = error as Error;
                if (err.message !== "not_found") {
                    console.error("Failed to load chat history:", err);
                } else {
                    setSession(null);
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
    }, [chatId]);

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
            });

            setSession(data.session);
            setRegion(data.session.region.toUpperCase());

            const savedUser = mapDtoToMessage(data.messages.user);
            const botMessage = mapDtoToMessage(data.messages.bot);

            setMessages((prev) => {
                const withoutPlaceholder = prev.filter((msg) => msg.id !== placeholderId);
                return [...withoutPlaceholder, savedUser, botMessage];
            });

            const summaryText = botMessage.text.length > 600
                ? `${botMessage.text.slice(0, 600)}…`
                : botMessage.text;

            void createSavedQuery({
                chatId,
                query: text,
                responseSummary: summaryText,
            })
                .then((result) => {
                    if (result?.savedQuery) {
                        window.dispatchEvent(
                            new CustomEvent("saved-query-created", { detail: result.savedQuery })
                        );
                    }
                })
                .catch((err: unknown) => {
                    console.error("Failed to cache saved query:", err);
                });
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
                        role: "bot",
                        timestamp: new Date(),
                    },
                ];
            });
        } finally {
            setIsTyping(false);
        }
    }, [chatId, region]);

    useEffect(() => {
        if (!chatId || isLoadingHistory) {
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
    }, [chatId, isLoadingHistory, messages.length, searchParams]);

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
