"use client"
import Image from "next/image";
import {Card, CardContent, CardHeader, CardTitle} from "@/components/ui/card";
import {Input} from "@/components/ui/input";
import {ArrowRight, MessageCircle, Paperclip, Upload} from "lucide-react";
import {Button} from "@/components/ui/button";
import {useRouter} from "next/navigation";
import {useState} from "react";
import {ToggleTheme} from "@/components/layout/toogle-theme";
import {SidebarTrigger} from "@/components/ui/sidebar";
import { SERVER_URL } from "@/utils/constants";

export default function ChatDashboard() {
    const router = useRouter();
    const [question, setQuestion] = useState("");
    const [documentFile, setDocumentFile] = useState(null);
    const [uploadError, setUploadError] = useState<any | unknown>(null);
    const [uploadedDocuments, setUploadedDocuments] = useState<any[]>([]);
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
                setUploadError("This document was already uploaded (duplicate detected)");
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
                setUploadError(error.message);
            } else {
                setUploadError("An unknown error occurred");
            }}
            finally {
            setIsUploading(false);
            }
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

                    {/* Upload Status & Error Message */}
                    {isUploading && (
                        <div className="text-center text-sm text-primary animate-pulse">
                            Uploading document...
                        </div>
                    )}

                    {uploadError && (
                        <div className="text-center text-sm text-red-500">
                            Error: {uploadError}
                        </div>
                    )}

                    {/* Recently Uploaded Documents */}
                    {uploadedDocuments.length > 0 && (
                        <Card className="border border-gray-200 dark:border-zinc-800 shadow-sm rounded-xl">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium">Recent Documents</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2 pt-0">
                                {uploadedDocuments.slice(-3).map((doc, index) => (
                                    <div key={index} className="flex items-center text-sm">
                                        <Paperclip className="w-4 h-4 mr-2 text-gray-400" />
                                        <span className="truncate max-w-[200px]">{doc.filename}</span>
                                    </div>
                                ))}
                            </CardContent>
                        </Card>
                    )}

                    {/* Action Cards */}
                    <div className="grid md:grid-cols-2 gap-4 pb-12">
                        {/* Upload Document Card */}
                        <Card className="shadow-sm border rounded-3xl border-gray-200 dark:border-zinc-800  transition-colors overflow-hidden group cursor-pointer">
                            <label className="h-36 relative p-4 space-y-2 flex flex-col items-center justify-center cursor-pointer">
                                <input
                                    type="file"
                                    accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt"
                                    className="sr-only"
                                    onChange={handleDocumentUpload}
                                />
                                <div className="w-12 h-12 flex items-center justify-center rounded-full bg-gray-100 dark:bg-zinc-800 group-hover:bg-primary-foreground transition-colors">
                                    <Upload className="w-6 h-6 text-gray-500 dark:text-gray-400 group-hover:text-primary" />
                                </div>
                                <div className="text-center">
                                    <p className="font-medium group-hover:text-primary transition-colors">Upload Document</p>
                                    <p className="text-xs text-gray-500 mt-1">
                                        PDF, Word, Excel, PowerPoint, or plain text
                                    </p>
                                </div>
                            </label>
                        </Card>

                        {/* Say Hello Card */}
                        <Card
                            className="shadow-sm border rounded-3xl border-gray-200 dark:border-zinc-800  transition-colors group cursor-pointer"
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
            </main>
        </div>
    );
}