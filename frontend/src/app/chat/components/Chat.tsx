"use client"
import Image from "next/image";
import {Card} from "@/components/ui/card";
import {Input} from "@/components/ui/input";
import {ArrowRight, MessageCircle, Paperclip, Upload} from "lucide-react";
import {Button} from "@/components/ui/button";
import {useRouter} from "next/navigation";
import {useState} from "react";
import {ToggleTheme} from "@/components/layout/toogle-theme";
import {SidebarTrigger} from "@/components/ui/sidebar";

export default function ChatDashboard() {
    const router = useRouter();
    const [question, setQuestion] = useState("");

    const handleAskQuestion = () => {
        if (!question.trim()) return;
        // Generate a unique chat ID
        const chatId = Date.now().toString();

        // Navigate to the chat page with the new chatId
        router.push(`/chat/${chatId}?initialQuestion=${encodeURIComponent(question)}`);
    };

    return (
        <div className="w-full mx-auto">
            <div className={"flex px-4 justify-between my-4 space-x-4 items-center"}>
                <SidebarTrigger/>
                <ToggleTheme/>
            </div>
            <main className={"flex px-6 justify-center items-center flex-col"}>
                <Image src={"/logo.png"} className={"w-20 h-auto"} width={400} height={400} alt={"logo"}/>
                <div className="w-full max-w-md space-y-6">
                    {/* Header */}
                    <div className="text-center py-2">
                        <h1 className="transition-colors font-bold font-mono uppercase text-2xl duration-300 hover:text-primary">Reg-Guru</h1>
                        <p className="text-gray-500 mt-1">Upload a document & Ask anything about it</p>
                    </div>

                    {/* Search Bar */}
                    <div className="relative">
                        <Input
                            autoFocus={true}
                            placeholder="Ask a question..."
                            value={question}
                            onChange={(e) => setQuestion(e.target.value)}
                            onKeyPress={(e) => e.key === "Enter" && handleAskQuestion()}
                            className="w-full rounded-full pl-4 pr-10 py-6 focus:outline-none focus-within:outline-0"
                        />
                        <Button
                            onClick={handleAskQuestion}
                            className={"absolute right-1 cursor-pointer w-10 h-10 rounded-full top-1/2 transform -translate-y-1/2 text-gray-500 dark:text-gray-300 hover:text-primary hover:bg-primary-foreground"}
                            variant={"outline"}
                            disabled={!question.trim()}
                        >
                            <ArrowRight className={"w-4 h-4"} />
                        </Button>
                    </div>

                    {/* Action Cards */}
                    <div className="grid md:grid-cols-1 gap-4 pb-12">
                        {/* Say Hello Card */}
                        <div className="flex justify-center items-center">
                            <Card
                                className="shadow-sm border rounded-3xl border-gray-200 dark:border-zinc-800 transition-colors group cursor-pointer"
                                onClick={() => {
                                    setQuestion("Hello! Tell me what you can do.");
                                    setTimeout(handleAskQuestion, 100);
                                }}
                            >
                                <div className="h-36 relative p-4 space-y-2 flex flex-col items-center justify-center">
                                    <div className="w-12 h-12 flex items-center justify-center rounded-full bg-gray-100 dark:bg-zinc-800 group-hover:bg-primary-foreground transition-colors">
                                        <MessageCircle className="w-6 h-6 text-gray-500 dark:text-gray-400 group-hover:text-primary" />
                                    </div>
                                    <div className="text-center">
                                        <p className="font-medium group-hover:text-primary transition-colors">Say Hello</p>
                                        <p className="text-xs text-gray-500 mt-1">
                                            Ask questions without using any documents
                                        </p>
                                    </div>
                                </div>
                            </Card>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}