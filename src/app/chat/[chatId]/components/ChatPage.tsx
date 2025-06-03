"use client";

import {useEffect, useRef, useState} from "react";
import {useParams, useRouter} from "next/navigation";
import {Button} from "@/components/ui/button";
import {Input} from "@/components/ui/input"
import {ScrollArea} from "@/components/ui/scroll-area";
import {
    ArrowRight,
    ArrowUp,
    ChevronDown,
    MoreVertical,
    Paperclip,
    Pencil,
    Share,
    ThumbsDown,
    ThumbsUp,
    Trash2,
    User
} from "lucide-react";
import Image from "next/image";
import {AnimatePresence, motion} from "framer-motion";
import {SidebarTrigger} from "@/components/ui/sidebar";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {ToggleTheme} from "@/components/layout/toogle-theme";
import { SERVER_URL } from "@/utils/constants";

interface Message {
    id: number;
    text: string;
    role: "user" | "bot";
    timestamp: Date;
}



export default function ChatPage() {
    const [question, setQuestion] = useState("");
    const [isUploading, setIsUploading] = useState(false);

    const handleAskQuestion = () => {
        if (!question.trim()) return;
        // Generate a unique chat ID
        const chatId = Date.now().toString();

        // Navigate to the chat page with the new chatId
        router.push(`/chat/${chatId}?initialQuestion=${encodeURIComponent(question)}`);
    };

    const handleDocumentUpload = async (e:any) => {
        const file = e.target.files[0];
        if (!file) return;

        setDocumentFile(file);
        setUploadError(null);
        setIsUploading(true);

        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch(SERVER_URL + "/api/upload_document", {
                method: "POST",
                body: formData,
            });

            if (response.status === 409) {
                // File already exists - treat as success but notify user
                setUploadedDocuments(prev => [...prev, {
                    filename: file.name,
                    upload_time: new Date().toISOString()
                }]);
                setUploadError(null);
                return;
            }

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || "Upload failed");
            }

            const data = await response.json();
            setUploadedDocuments(prev => [...prev, {
                filename: data.filename,
                upload_time: new Date().toISOString()
            }]);

            // Clear the file input
            e.target.value = null;

            // Optional: Auto-suggest a question about the document
            if (!question) {
                setQuestion(`What is the main topic of ${file.name}?`);
            }}
            catch (error) {
            console.error("Upload error:", error);
            // Narrow the type of 'error'
            if (error instanceof Error) {
                setUploadError(null);
            } else {
                setUploadError(null);
            }}
            finally {
            setIsUploading(false);
            }
    };

    const router = useRouter();
    const { chatId } = useParams();
    const [message, setMessage] = useState("");
    const [chatHistory, setChatHistory] = useState<any[]>([]);
    const [documentFile, setDocumentFile] = useState<any>(null);
    const [activeTab, setActiveTab] = useState("chat");
    const [lastResponseId, setLastResponseId] = useState<number | null>(null);
    const [uploadError, setUploadError] = useState(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [savedQueries, setSavedQueries] = useState<any[]>([]);
    const [uploadedDocuments, setUploadedDocuments] = useState<any[]>([]);
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

    const handleSend = async () => {
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
                    document: documentFile?.name || "Current Document",
                }),
            });
    
            // Refresh queries
            const queriesResponse = await fetch(SERVER_URL + "/api/get_queries");
            setSavedQueries(await queriesResponse.json());
            
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

    const messageGroups = groupMessagesByDate();

    useEffect(() => {
        const fetchData = async () => {
            try {
                console.log("SERVER_URL", SERVER_URL);
                const [queriesRes, docsRes] = await Promise.all([
                    fetch(SERVER_URL + "/api/get_queries"),
                    fetch(SERVER_URL + "/api/get_documents")
                ]);
                setSavedQueries(await queriesRes.json());
                setUploadedDocuments(await docsRes.json());
            } catch (error) {
                console.error("Error loading data:", error);
            }
        };
        fetchData();
        // console.log(savedQueries)
    }, []);
    return (
        <main className="flex flex-col rounded-2xl container px-2 w-full h-screen">
            {/* Header */}
            <header className="flex z-10 items-center justify-between p-6 border rounded-2xl my-2 bg-white dark:bg-[#171717]" >
                <div className="flex items-center gap-3">
                    <SidebarTrigger />
                    <div className="flex items-center gap-2">
                        {/*<div className="relative">*/}
                        {/*    <Image*/}
                        {/*        src="/logo.png"*/}
                        {/*        alt="Bot avatar"*/}
                        {/*        width={40}*/}
                        {/*        height={40}*/}
                        {/*        className="rounded-full border-2 border-blue-200"*/}
                        {/*    />*/}
                        {/*    <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-white"></span>*/}
                        {/*</div>*/}
                        <div>
                            <h1 className="font-medium">Reg-Guru</h1>
                            <p className="text-xs text-green-500">{isTyping ? "typing..." : "Online"}</p>
                        </div>
                    </div>
                </div>
                <div className={"flex items-center space-x-4"}>
                    <ToggleTheme/>
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="secondary" size="icon" className="w-10 h-10 rounded-full cursor-pointer">
                                <MoreVertical className="h-5 w-5" />
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent className="mx-4">
                            <DropdownMenuLabel>Chat Options</DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem>
                                <Button variant={"ghost"} className={"cursor-pointer"}>
                                    <Pencil className="" />
                                    Edit
                                </Button>
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                                <Button variant={"ghost"} className={"cursor-pointer"}>
                                    <Share className="" />
                                    Share
                                </Button>
                            </DropdownMenuItem>

                            <DropdownMenuItem>
                                <Button variant={"ghost"} className={"cursor-pointer text-red-400 hover:text-red-400"}>
                                    <Trash2 className=" text-red-400 hover:text-red-400" />
                                    Delete Chat
                                </Button>
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </div>
            </header>
            {/* Messages area */}
            <ScrollArea
                className="flex-1 px-0 py-2 overflow-y-auto"
                ref={scrollAreaRef}
            >
                <div className="w-full px-4 mx-auto space-y-6 pb-20">
                    {messageGroups.map((group, groupIndex) => (
                        <div key={group.date.toISOString()} className="space-y-4">
                            <div className="flex justify-center">
                                <div className="bg-gray-200 dark:bg-gray-700 px-3 py-1 rounded-full text-xs text-gray-700 dark:text-gray-300">
                                    {formatDate(group.date)}
                                </div>
                            </div>

                            <AnimatePresence initial={false}>
                                {group.messages.map((message) => (
                                    <motion.div
                                        key={message.id}
                                        initial={{ opacity: 0, y: 20, scale: 0.95 }}
                                        animate={{ opacity: 1, y: 0, scale: 1 }}
                                        transition={{ duration: 0.3 }}
                                        className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                                    >
                                        <div className={`flex items-start gap-2 py-2 max-w-[90%] ${message.role === "user" ? "flex-row-reverse" : ""}`}>
                                            {message.role === "bot" ? (
                                                <div className="flex-shrink-0">
                                                    <Image
                                                        src="/logo.png"
                                                        alt="Bot avatar"
                                                        width={36}
                                                        height={36}
                                                        className=""
                                                    />
                                                </div>
                                            ) : (
                                                <div className="flex-shrink-0 border bg-[#f1f1f1] dark:bg-[#171717] w-9 h-9 rounded-full flex items-center justify-center">
                                                    <User className="h-5 w-5" />
                                                </div>
                                            )}
                                            <div className={`relative group ${message.role === "user" ? "mr-1" : "ml-1"}`}>
                                                <div
                                                    className={`p-3 rounded-2xl ${
                                                        message.role === "user"
                                                            ? "rounded-tr-none bg-[#f1f1f1] dark:bg-[#171717]"
                                                            : "bg-[#F0F5FC] text-[#559BFE] dark:bg-gray-800 rounded-tl-none"
                                                    }`}
                                                >
                                                    <p>{message.text}</p>
                                                    <span className="text-xs opacity-70 block text-right mt-1">
                            {formatTime(message.timestamp)}
                          </span>
                                                </div>
                                                <div className={"py-2"}>
                                                    {message.role === "bot" ? (
                                                        <div className="flex-shrink-0">
                                                            <Button variant={"ghost"} className={"rounded-full"}>
                                                                <ThumbsUp/>
                                                            </Button>
                                                            <Button variant={"ghost"} className={"rounded-full"}>
                                                                <ThumbsDown/>
                                                            </Button>
                                                        </div>
                                                    ) : (
                                                        <div className="flex-shrink-0">

                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    </motion.div>
                                ))}
                            </AnimatePresence>
                        </div>
                    ))}

                    {/* Typing indicator */}
                    {isTyping && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="flex justify-start"
                        >
                            <div className="flex items-end gap-2">
                                <div className="flex-shrink-0">
                                    <Image
                                        src="/logo.png"
                                        alt="Bot avatar"
                                        width={36}
                                        height={36}
                                        className="rounded-full"
                                    />
                                </div>
                                <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl rounded-bl-none shadow-sm">
                                    <div className="flex space-x-1">
                                        <motion.div
                                            animate={{ y: [0, -5, 0] }}
                                            transition={{ repeat: Infinity, duration: 1, repeatDelay: 0 }}
                                            className="w-1 h-1 bg-gray-400 rounded-full"
                                        />
                                        <motion.div
                                            animate={{ y: [0, -5, 0] }}
                                            transition={{ repeat: Infinity, duration: 1, delay: 0.2, repeatDelay: 0 }}
                                            className="w-1 h-1 bg-gray-400 rounded-full"
                                        />
                                        <motion.div
                                            animate={{ y: [0, -5, 0] }}
                                            transition={{ repeat: Infinity, duration: 1, delay: 0.4, repeatDelay: 0 }}
                                            className="w-1 h-1 bg-gray-400 rounded-full"
                                        />
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    )}

                    {/* Invisible element at the end to scroll to */}
                    <div ref={messagesEndRef} />
                </div>
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
            <div className="p-4 sticky bg-white dark:bg-[#171717] max-w-[100%] w-full mx-auto flex justify-center bottom-0 border-2 rounded-2xl my-2">
                <div className="mx-auto w-full max-w-lg">
                    <div className="flex items-center gap-2">
                        <div className="relative">
                            <input
                                type="file"
                                accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt"
                                className="sr-only"
                                id="document-upload"
                                onChange={handleDocumentUpload}
                            />
                            <label htmlFor="document-upload">
                                <Button
                                    asChild
                                    variant="outline"
                                    className="cursor-pointer w-12 h-12 rounded-full text-gray-400"
                                >
                                    <span>
                                        <Paperclip />
                                    </span>
                                </Button>
                            </label>
                        </div>
                        <div className="relative flex-1">
                            <Input
                                ref={inputRef}
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyPress={(e) => e.key === "Enter" && handleSend()}
                                placeholder="Type a message..."
                                className="pl-4 pr-12 py-6 max-w-lg w-full rounded-full"
                            />
                            <AnimatePresence>
                                {input.trim() ? (
                                    <motion.div
                                        initial={{ scale: 0, opacity: 0 }}
                                        animate={{ scale: 1, opacity: 1 }}
                                        exit={{ scale: 0, opacity: 0 }}
                                        transition={{ duration: 0.2 }}
                                        className="absolute right-2 top-1/2 transform -translate-y-1/2"
                                    >
                                        <Button
                                            onClick={handleSend}
                                            size="icon"
                                            className="h-10 w-10 rounded-full cursor-pointer"
                                        >
                                            <ArrowRight className="h-5 w-5" />
                                        </Button>
                                    </motion.div>
                                ) : (
                                    <motion.div
                                        initial={{ scale: 0, opacity: 0 }}
                                        animate={{ scale: 1, opacity: 1 }}
                                        exit={{ scale: 0, opacity: 0 }}
                                        transition={{ duration: 0.2 }}
                                        className="absolute right-1 top-1/2 transform -translate-y-1/2"
                                    >
                                        <Button
                                            variant="outline"
                                            size="icon"
                                            className="h-10 w-10 rounded-full"
                                        >
                                            <ArrowUp className="h-5 w-5" />
                                        </Button>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    );
}