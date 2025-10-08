"use client"
import Image from "next/image";
import { Input } from "@/components/ui/input";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import { useEffect, useState, type SyntheticEvent } from "react";
import { ToggleTheme } from "@/components/layout/toogle-theme";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { getStoredUser } from "@/utils/auth-client";

export default function ChatDashboard() {
    const router = useRouter();
    const [question, setQuestion] = useState("");

    const handleImageError = (event: SyntheticEvent<HTMLImageElement>) => {
        event.currentTarget.style.visibility = "hidden";
    };

    useEffect(() => {
        if (!getStoredUser()) {
            router.replace("/login");
        }
    }, [router]);

    const handleAskQuestion = () => {
        if (!question.trim()) return;
        const user = getStoredUser();
        if (!user) {
            router.replace("/login");
            return;
        }
        // Generate a unique chat ID compatible with backend UUID requirement
        const chatId = crypto.randomUUID();

        // Navigate to the chat page with the new chatId
        router.push(`/chat/${chatId}?initialQuestion=${encodeURIComponent(question)}`);
    };

    return (
        <div className="w-full mx-auto">
            <div className={"flex px-4 justify-between my-4 space-x-4 items-center"}>
                <SidebarTrigger />
                <ToggleTheme />
            </div>
            <main className={"flex px-6 justify-center items-center flex-col"}>
                <Image
                    src={"/logo.png"}
                    className={"w-20 h-auto"}
                    width={400}
                    height={400}
                    alt={"logo"}
                    onError={handleImageError}
                />
                <div className="w-full max-w-md space-y-6">
                    {/* Header */}
                    <div className="text-center py-2">
                        <h1 className="transition-colors font-bold font-mono uppercase text-2xl duration-300 hover:text-primary">Reg-Guru</h1>
                        <p className="text-gray-500 mt-1">Ask me anything related to regulations and laws</p>
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
                </div>
            </main>
        </div>
    );
}
