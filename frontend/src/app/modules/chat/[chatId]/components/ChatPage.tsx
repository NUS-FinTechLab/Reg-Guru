"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChevronDown, Loader2 } from "lucide-react";
import { motion } from "framer-motion";
import { fetchChat, requestChecklistGeneration, sendChatMessage } from "@/utils/api";
import { AuthUser, ChatListItem, ChatMessageDTO, ChatSummary, Message } from "@/utils/api/types";
import { getStoredUser } from "@/utils/auth-client";
import ChatHeader from "./ChatHeader";
import ChatMessages from "./ChatMessages";
import ChatInput from "./ChatInput";

const REGION_VALUES = ["US", "SG", "EU"] as const;
type RegionValue = (typeof REGION_VALUES)[number];

const REGION_VALUE_SET = new Set<RegionValue>(REGION_VALUES);

const toRegionValue = (input: string): RegionValue => {
    const upper = (input || "US").toUpperCase() as RegionValue;
    return REGION_VALUE_SET.has(upper) ? upper : "US";
};

const decodeHtmlEntities = (value: string): string =>
    value
        .replace(/&lt;/g, "<")
        .replace(/&gt;/g, ">")
        .replace(/&amp;/g, "&")
        .replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'");

const stripHtml = (value: string): string => {
    if (!value) {
        return "";
    }

    const withoutTags = value.replace(/<[^>]+>/g, " ");
    const collapsedWhitespace = withoutTags.replace(/\s+/g, " ").trim();
    return decodeHtmlEntities(collapsedWhitespace);
};

const unwrapCodeFence = (value: string): string => {
    const trimmed = value.trim();
    const fenceMatch = trimmed.match(/^```(?:json)?\s*([\s\S]*?)```$/i);
    if (fenceMatch) {
        return fenceMatch[1].trim();
    }
    return trimmed;
};

const escapeHtml = (value: string): string =>
    value
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

const toHtmlFromPlainText = (value: string): string => {
    if (!value) {
        return "";
    }
    const escaped = escapeHtml(value);
    return escaped
        .replace(/\r\n/g, "\n")
        .replace(/\n{2,}/g, "<br /><br />")
        .replace(/\n/g, "<br />");
};

const parseStructuredAssistantMessage = (
    rawText: string,
): { answerHtml: string; shouldCreateChecklist?: boolean } | null => {
    const cleaned = (rawText ?? "").trim();
    if (!cleaned) {
        return null;
    }

    let candidate = unwrapCodeFence(cleaned);
    if (candidate.toLowerCase().startsWith("json ")) {
        candidate = candidate.slice(5).trim();
    }

    try {
        const parsed = JSON.parse(candidate);
        if (!parsed || typeof parsed !== "object") {
            return null;
        }

        const answer = typeof parsed.answer === "string" ? parsed.answer.trim() : "";
        const shouldCreateRaw = (parsed as Record<string, unknown>)["shouldCreateChecklist"];

        let shouldCreate: boolean | undefined;
        if (typeof shouldCreateRaw === "boolean") {
            shouldCreate = shouldCreateRaw;
        } else if (typeof shouldCreateRaw === "string") {
            const normalized = shouldCreateRaw.trim().toLowerCase();
            shouldCreate = ["1", "true", "yes"].includes(normalized);
        }

        if (!answer) {
            return null;
        }

        return {
            answerHtml: toHtmlFromPlainText(answer),
            shouldCreateChecklist: shouldCreate,
        };
    } catch {
        return null;
    }
};

const mapDtoToMessage = (dto: ChatMessageDTO): Message => {
    const base: Message = {
        id: dto.id,
        text: dto.text,
        role: dto.role,
        timestamp: new Date(dto.createdAt),
        sources: dto.sources ?? [],
        shouldCreateChecklist: dto.shouldCreateChecklist,
    };

    if (dto.role !== "ai") {
        return base;
    }

    const structured = parseStructuredAssistantMessage(dto.text);
    if (!structured) {
        return base;
    }

    return {
        ...base,
        text: structured.answerHtml,
        shouldCreateChecklist:
            dto.shouldCreateChecklist !== undefined
                ? dto.shouldCreateChecklist
                : structured.shouldCreateChecklist,
    };
};

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
    const [region, setRegion] = useState<RegionValue>("US");
    const [dismissedChecklistIds, setDismissedChecklistIds] = useState<string[]>([]);
    const [checklistSubmittingId, setChecklistSubmittingId] = useState<string | null>(null);
    const [checklistErrors, setChecklistErrors] = useState<Record<string, string>>({});
    const [isTyping, setIsTyping] = useState(false);
    const [autoScroll, setAutoScroll] = useState(true);
    const [showScrollButton, setShowScrollButton] = useState(false);
    const [isLoadingHistory, setIsLoadingHistory] = useState(true);
    const [activeChatId, setActiveChatId] = useState<string>(chatId);

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
            setChat(null);
            setMessages([]);
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
        setActiveChatId(chatId);
    }, [chatId]);

    useEffect(() => {
        setDismissedChecklistIds([]);
        setChecklistSubmittingId(null);
        setChecklistErrors({});
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
        if (!text.trim()) {
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
                chatId: activeChatId || undefined,
                text,
                region,
                userId: authUser.id,
            });

            setChat(data.chat);

            const resolvedChatId = data.chat.id;
            setActiveChatId(resolvedChatId);
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
    }, [activeChatId, authUser, chatId, region, router]);

    const handleRegionChange = useCallback((value: string) => {
        setRegion(toRegionValue(value));
    }, []);

    const shouldShowChecklistPrompt = useCallback(
        (message: Message) => {
            if (message.role !== "ai" || !message.shouldCreateChecklist || message.pending) {
                return false;
            }
            const messageKey = String(message.id);
            return !dismissedChecklistIds.includes(messageKey);
        },
        [dismissedChecklistIds],
    );

    const handleChecklistCancel = useCallback((message: Message) => {
        const messageKey = String(message.id);
        setDismissedChecklistIds((prev) => (prev.includes(messageKey) ? prev : [...prev, messageKey]));
        setChecklistErrors((prev) => {
            if (!(messageKey in prev)) {
                return prev;
            }
            const { [messageKey]: _removed, ...rest } = prev;
            return rest;
        });
        setChecklistSubmittingId((prev) => (prev === messageKey ? null : prev));
    }, []);

    const handleChecklistConfirm = useCallback(
        async (message: Message) => {
            const messageKey = String(message.id);
            if (checklistSubmittingId && checklistSubmittingId !== messageKey) {
                return;
            }

            setChecklistErrors((prev) => {
                if (!(messageKey in prev)) {
                    return prev;
                }
                const { [messageKey]: _ignored, ...rest } = prev;
                return rest;
            });

            const messageIndex = messages.findIndex((item) => String(item.id) === messageKey);
            if (messageIndex === -1) {
                return;
            }

            let previousUserMessage: Message | null = null;
            for (let idx = messageIndex - 1; idx >= 0; idx -= 1) {
                const candidate = messages[idx];
                if (candidate.role === "user") {
                    previousUserMessage = candidate;
                    break;
                }
            }

            const missionText = stripHtml(previousUserMessage?.text ?? "");
            const answerPlain = stripHtml(message.text);

            const contextSegments: string[] = [];
            if (previousUserMessage) {
                const questionPlain = stripHtml(previousUserMessage.text);
                if (questionPlain) {
                    contextSegments.push(`User question: ${questionPlain}`);
                }
            }
            if (answerPlain) {
                contextSegments.push(answerPlain);
            }

            const context = contextSegments.join("\n\n").trim();
            const mission = missionText || (answerPlain ? `Checklist derived from: ${answerPlain}` : "Checklist requested via chat assistant");
            const normalizedRegion = toRegionValue(region);

            setChecklistSubmittingId(messageKey);
            try {
                const result = await requestChecklistGeneration({
                    mission,
                    context,
                    region: normalizedRegion,
                });

                if (!result.ok) {
                    const errorMessage = result.message || "Failed to generate checklist. Please try again.";
                    setChecklistErrors((prev) => ({ ...prev, [messageKey]: errorMessage }));
                    return;
                }

                let createdChecklistId: string | null = null;
                if (result.data && typeof result.data === "object") {
                    const data = result.data as Record<string, unknown>;
                    const metadata = data.metadata;
                    const createdChecklist = data.createdChecklist;

                    if (metadata && typeof metadata === "object") {
                        const metadataRecord = metadata as Record<string, unknown>;
                        const candidateId =
                            metadataRecord["createdChecklistId"] ?? metadataRecord["created_checklist_id"];
                        if (typeof candidateId === "string" && candidateId.trim()) {
                            createdChecklistId = candidateId.trim();
                        } else if (typeof candidateId === "number" && Number.isFinite(candidateId)) {
                            createdChecklistId = String(candidateId);
                        }
                    }

                    if (!createdChecklistId && createdChecklist && typeof createdChecklist === "object") {
                        const createdChecklistRecord = createdChecklist as Record<string, unknown>;
                        const idValue = createdChecklistRecord["id"];
                        if (typeof idValue === "string" && idValue.trim()) {
                            createdChecklistId = idValue.trim();
                        } else if (typeof idValue === "number" && Number.isFinite(idValue)) {
                            createdChecklistId = String(idValue);
                        }
                    }
                }

                setDismissedChecklistIds((prev) => (prev.includes(messageKey) ? prev : [...prev, messageKey]));

                if (createdChecklistId) {
                    router.push(`/modules/compliance-checklist/${createdChecklistId}`);
                } else {
                    router.push(`/modules/compliance-checklist`);
                }
            } catch (error) {
                console.error("Failed to generate checklist from chat", error);
                setChecklistErrors((prev) => ({
                    ...prev,
                    [messageKey]: "Failed to generate the checklist. Please try again.",
                }));
            } finally {
                setChecklistSubmittingId(null);
            }
        },
        [checklistSubmittingId, messages, region, router],
    );

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

    const isChecklistLoading = checklistSubmittingId !== null;

    return (
        <div className="relative flex flex-col rounded-2xl container px-2 w-full h-screen">
            <ChatHeader isTyping={isTyping} region={region} onRegionChange={handleRegionChange} />
            <ScrollArea className="flex-1 px-0 py-2 overflow-y-auto" ref={scrollAreaRef}>
                <ChatMessages
                    messageGroups={messageGroups}
                    isTyping={isTyping}
                    formatDate={formatDate}
                    formatTime={formatTime}
                    messagesEndRef={messagesEndRef}
                    shouldShowChecklistPrompt={shouldShowChecklistPrompt}
                    onChecklistConfirm={handleChecklistConfirm}
                    onChecklistCancel={handleChecklistCancel}
                    checklistSubmittingId={checklistSubmittingId}
                    checklistErrors={checklistErrors}
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

            {isChecklistLoading && (
                <div className="absolute inset-0 z-50 flex flex-col items-center justify-center gap-4 bg-background/80 backdrop-blur-sm">
                    <div className="flex items-center gap-3 rounded-xl border bg-card px-6 py-4 shadow-xl">
                        <Loader2 className="size-5 animate-spin" aria-hidden="true" />
                        <span className="text-sm font-medium">Generating checklist…</span>
                    </div>
                </div>
            )}
        </div>
    );
}
