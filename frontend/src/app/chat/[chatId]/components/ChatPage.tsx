"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChevronDown } from "lucide-react";
import { motion } from "framer-motion";
import { SERVER_URL } from "@/utils/constants";
import ChatHeader from "./ChatHeader";
import ChatMessages from "./ChatMessages";
import ChatInput from "./ChatInput";

interface Message {
    id: number;
    text: string;
    role: "user" | "bot";
    timestamp: Date;
}

export default function ChatPage() {
    const { chatId } = useParams();
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isTyping, setIsTyping] = useState(false);
    const [autoScroll, setAutoScroll] = useState(true);
    const [showScrollButton, setShowScrollButton] = useState(false);
    const scrollAreaRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);


    // Load previous messages from localStorage on mount sidebar
    useEffect(() => {
        const savedMessages = localStorage.getItem(`chat-${chatId}-messages`);
        if (savedMessages) {
            try {
                const parsedMessages = JSON.parse(savedMessages);
                // Convert string timestamps back to Date objects
                const messagesWithDates = parsedMessages.map((msg: any) => ({
                    ...msg,
                    timestamp: new Date(msg.timestamp)
                }));
                setMessages(messagesWithDates);
            } catch (e) {
                console.error("Failed to parse saved messages", e);
            }
        }
    }, [chatId]);

    // Save messages to localStorage whenever they change
    useEffect(() => {
        if (messages.length > 0) {
            localStorage.setItem(`chat-${chatId}-messages`, JSON.stringify(messages));
        }
    }, [messages, chatId]);

    // Scroll to bottom when new messages arrive if autoScroll is true
    useEffect(() => {
        if (autoScroll && messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [messages, autoScroll]);

    // Handle scroll events to detect when user has scrolled up
    useEffect(() => {
        const scrollArea = scrollAreaRef.current;

        const handleScroll = () => {
            if (scrollArea) {
                const { scrollTop, scrollHeight, clientHeight } = scrollArea;
                const isAtBottom = scrollHeight - scrollTop - clientHeight < 20;

                setAutoScroll(isAtBottom);
                setShowScrollButton(!isAtBottom && messages.length > 0);
            }
        };

        if (scrollArea) {
            scrollArea.addEventListener("scroll", handleScroll);
            return () => scrollArea.removeEventListener("scroll", handleScroll);
        }
    }, [messages.length]);

    // Focus input on load
    useEffect(() => {
        if (inputRef.current) {
            inputRef.current.focus();
        }
    }, []);


    const scrollToBottom = () => {
        setAutoScroll(true);
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
        }
    };

    const formatTime = (date: Date) => {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    const formatDate = (date: Date) => {
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);

        const isToday = date.toDateString() === today.toDateString();
        const isYesterday = date.toDateString() === yesterday.toDateString();

        if (isToday) return "Today";
        if (isYesterday) return "Yesterday";
        return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    };

    // Group messages by date
    const groupMessagesByDate = () => {
        const groups: { [key: string]: Message[] } = {};

        messages.forEach(message => {
            const dateKey = new Date(message.timestamp).toDateString();
            if (!groups[dateKey]) {
                groups[dateKey] = [];
            }
            groups[dateKey].push(message);
        });

        return Object.entries(groups).map(([date, msgs]) => ({
            date: new Date(date),
            messages: msgs
        }));
    };

    const handleSend = async (input: string) => {
        if (!input.trim()) return;


        // Add user message
        const userMessage: Message = {
            id: Date.now(),
            text: input,
            role: "user",
            timestamp: new Date(),
        };
        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setAutoScroll(true);

        // Show typing indicator
        setIsTyping(true);
        // set initial message

        try {
            const response = await fetch(SERVER_URL + "/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: userMessage }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Add bot response to messages
            const botMessage: Message = {
                id: Date.now(),
                text: data.response,
                role: "bot",
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, botMessage]);

            // Save to query history
            await fetch(SERVER_URL + "/api/save_query", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    question: input,
                    answer: data.response,
                }),
            });
        } catch (error) {
            console.error("Error:", error);
            // Add error message from bot
            const errorMessage: Message = {
                id: Date.now(),
                text: "Sorry, something went wrong. Please try again.",
                role: "bot",
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsTyping(false);
        }
    };

    // Initiate first question
    const searchParams = useSearchParams();
    let some = false;
    useEffect(() => {
        if (some) return;
        some = true;
        if (localStorage.getItem(`chat-${chatId}-messages`)) return;

        const initialQuestionText = searchParams.get("initialQuestion") ?? "";
        if (initialQuestionText.trim()) {
            setInput(initialQuestionText);
            handleSend(initialQuestionText);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const messageGroups = groupMessagesByDate();

    return (
        <div className="flex flex-col rounded-2xl container px-2 w-full h-screen">
            {/* Header */}
            <ChatHeader isTyping={isTyping} />
            {/* Messages area */}
            <ScrollArea
                className="flex-1 px-0 py-2 overflow-y-auto"
                ref={scrollAreaRef}
            >
                <ChatMessages
                    messageGroups={messageGroups}
                    isTyping={isTyping}
                    formatDate={formatDate}
                    formatTime={formatTime}
                    messagesEndRef={messagesEndRef}
                />
            </ScrollArea>

            {/* Scroll to bottom button */}
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

            {/* Input area */}
            <ChatInput value={input} onChange={setInput} onSend={handleSend} inputRef={inputRef} />
        </div>
    );
}