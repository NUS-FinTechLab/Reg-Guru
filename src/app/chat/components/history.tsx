"use client"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Paperclip, Search, Calendar, MessageSquare, Filter, Download, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useEffect, useState } from "react";
import { ToggleTheme } from "@/components/layout/toogle-theme";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar } from "@/components/ui/avatar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { fileNames, getFileNames } from "@/utils/api/getData";
import { title } from "process";
import { date, number } from "zod";

class ChatHistory {
    id!: number;
    title!: string;
    lastMessage!: string;
    date!: string;
    time!: string;
    documents!: string[];
    starred!: boolean;

    constructor(
        id: number,
        title: string,
        lastMessage: string,
        date: string,
        time: string,
        documents: string[],
        starred: boolean,
    ) {
        this.id = id;
        this.title = title;
        this.lastMessage = lastMessage;
        this.date = date;
        this.time = time;
        this.documents = documents;
        this.starred = starred;
    } 
}


export default function HistoryDashboard() {
    const [query, setQuery] = useState("");
    const [uploadedDocuments, setUploadedDocuments] = useState<any[]>([
        { filename: "Company_Policy_2025.pdf", date: "Apr 2, 2025" },
        { filename: "Regulatory_Guidelines_v3.docx", date: "Mar 28, 2025" },
        { filename: "Compliance_Framework.pdf", date: "Mar 15, 2025" }
    ]);
    const [filenames, setFileNames] = useState<fileNames>({filenames: []})
    const [chatHistory, setChatHistory] = useState<ChatHistory[]>([]);

    useEffect(() => {
        const load = async () => {
            const fetched = await getFileNames();
            setFileNames(fetched);
        }
        if(filenames.filenames.length == 0) {
            load();
        }

    }, [])


    const data = filenames.filenames;
    
    useEffect(() => {
        let count : number = 1;
        const some = data.map(name => new ChatHistory(
            count++,
            name,
            "",
            "Apr 4, 2025",
            "14:32",
            [name],
            true,
        ))
        setChatHistory(some);
    }, [filenames])

    // Sample chat history data
    // const chatHistory = [
    //     {
    //         id: 1,
    //         title: "Policy compliance requirements",
    //         lastMessage: "What are the key requirements for policy compliance in section 3.2?",
    //         date: "Apr 4, 2025",
    //         time: "14:32",
    //         documents: ["Company_Policy_2025.pdf"],
    //         messageCount: 8,
    //         starred: true
    //     },
    //     {
    //         id: 2,
    //         title: "Regulatory filing deadlines",
    //         lastMessage: "When is the deadline for Q2 regulatory filings?",
    //         date: "Apr 2, 2025",
    //         time: "09:15",
    //         documents: ["Regulatory_Guidelines_v3.docx"],
    //         messageCount: 5,
    //         starred: false
    //     },
    //     {
    //         id: 3,
    //         title: "Compliance framework analysis",
    //         lastMessage: "Can you summarize the key points of the compliance framework?",
    //         date: "Mar 29, 2025",
    //         time: "11:47",
    //         documents: ["Compliance_Framework.pdf"],
    //         messageCount: 12,
    //         starred: true
    //     },
    //     {
    //         id: 4,
    //         title: "International regulations comparison",
    //         lastMessage: "How do our policies align with international standards?",
    //         date: "Mar 25, 2025",
    //         time: "16:03",
    //         documents: ["Regulatory_Guidelines_v3.docx", "Compliance_Framework.pdf"],
    //         messageCount: 9,
    //         starred: false
    //     },
    //     {
    //         id: 5,
    //         title: "Document extraction test",
    //         lastMessage: "Can you extract all mentions of audit requirements?",
    //         date: "Mar 22, 2025",
    //         time: "10:22",
    //         documents: ["Company_Policy_2025.pdf"],
    //         messageCount: 3,
    //         starred: false
    //     }
    // ];

    // Filter states
    const [selectedDateRange, setSelectedDateRange] = useState("all");
    const [selectedDocuments, setSelectedDocuments] = useState<string[]>([]);

    const filteredHistory = chatHistory.filter(chat => {
        // Filter by search query
        if (query && !chat.title.toLowerCase().includes(query.toLowerCase()) &&
            !chat.lastMessage.toLowerCase().includes(query.toLowerCase())) {
            return false;
        }

        // Filter by documents if any are selected
        if (selectedDocuments.length > 0) {
            const hasSelectedDoc = chat.documents.some(doc =>
                selectedDocuments.includes(doc)
            );
            if (!hasSelectedDoc) return false;
        }

        // Filter by date range
        if (selectedDateRange === "today") {
            return chat.date === "Apr 4, 2025";
        } else if (selectedDateRange === "week") {
            // Simple implementation - would need proper date handling in production
            return ["Apr 4, 2025", "Apr 2, 2025", "Mar 29, 2025"].includes(chat.date);
        }

        return true;
    });

    return (
        <div className="w-full mx-auto">
            <div className="flex px-4 justify-between my-4 space-x-4 items-center">
                <SidebarTrigger/>
                <h1 className="font-semibold text-lg">Document History</h1>
                <ToggleTheme/>
            </div>

            <main className="flex px-6 justify-center items-center flex-col py-4">
                <div className="w-full max-w-3xl space-y-6">
                    {/* Search Bar */}
                    <div className="relative">
                        <Input
                            autoFocus={true}
                            placeholder="Search in chat history"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            className="w-full rounded-full pl-4 pr-10 py-6 focus:outline-none focus-within:outline-0"
                        />
                        <Button
                            className="absolute right-1 cursor-pointer w-10 h-10 rounded-full top-1/2 transform -translate-y-1/2 text-gray-500 dark:text-gray-300 hover:text-primary hover:bg-primary-foreground"
                            variant="outline"
                            disabled={!query.trim()}
                        >
                            <Search className="w-4 h-4" />
                        </Button>
                    </div>

                    {/* Filters */}
                    <div className="flex flex-wrap gap-2 items-center justify-between">
                        <Tabs defaultValue="all" className="w-auto" onValueChange={setSelectedDateRange}>
                            <TabsList>
                                <TabsTrigger value="all">All Time</TabsTrigger>
                                <TabsTrigger value="today">Today</TabsTrigger>
                                <TabsTrigger value="week">This Week</TabsTrigger>
                            </TabsList>
                        </Tabs>

                        <div className="flex items-center gap-2">
                            <Popover>
                                <PopoverTrigger asChild>
                                    <Button variant="outline" size="sm" className="flex items-center gap-1">
                                        <Filter className="w-4 h-4" />
                                        <span>Filter</span>
                                    </Button>
                                </PopoverTrigger>
                                <PopoverContent className="w-64">
                                    <div className="space-y-4">
                                        <h3 className="font-medium text-sm">Filter by Document</h3>
                                        <div className="space-y-2">
                                            {uploadedDocuments.map((doc, idx) => (
                                                <div key={idx} className="flex items-center space-x-2">
                                                    <Checkbox
                                                        id={`doc-${idx}`}
                                                        checked={selectedDocuments.includes(doc.filename)}
                                                        onCheckedChange={(checked) => {
                                                            if (checked) {
                                                                setSelectedDocuments([...selectedDocuments, doc.filename]);
                                                            } else {
                                                                setSelectedDocuments(selectedDocuments.filter(d => d !== doc.filename));
                                                            }
                                                        }}
                                                    />
                                                    <Label htmlFor={`doc-${idx}`} className="text-sm">{doc.filename}</Label>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </PopoverContent>
                            </Popover>
                        </div>
                    </div>

                    {/* Chat History List */}
                    <Card className="border border-gray-200 dark:border-zinc-800 shadow-sm rounded-xl">
                        <CardHeader className="pb-2">
                            <div className="flex items-center justify-between">
                                <CardTitle className="text-base font-medium">
                                    Documents uploaded
                                </CardTitle>
                                <span className="text-sm text-gray-500">
                                    {filteredHistory.length} {filteredHistory.length === 1 ? 'document' : 'documents'}
                                </span>
                            </div>
                        </CardHeader>
                        <CardContent className="pt-0">
                            <ScrollArea className="h-[400px] pr-4">
                                <div className="space-y-3">
                                    {filteredHistory.length > 0 ? (
                                        filteredHistory.map((chat) => (
                                            <div
                                                key={chat.id}
                                                className="flex flex-col p-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-zinc-900 rounded-lg transition-colors"
                                                onClick={() => console.log(`Open chat ${chat.id}`)}
                                            >
                                                <div className="flex items-start justify-between">
                                                    <div className="flex items-center gap-2">
                                                        <Avatar className="w-8 h-8 bg-primary/10 flex items-center justify-center">
                                                            <MessageSquare className="w-4 h-4 text-primary" />
                                                        </Avatar>
                                                        <div>
                                                            <div className="flex items-center gap-2">
                                                                <h3 className="font-medium text-sm">{chat.title}</h3>
                                                                {chat.starred && <Badge variant="outline" className="bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 border-yellow-200 text-[10px]">Starred</Badge>}
                                                            </div>
                                                            <p className="text-sm text-gray-500 dark:text-gray-400 truncate max-w-xs sm:max-w-sm md:max-w-md">
                                                                {chat.lastMessage}
                                                            </p>
                                                        </div>
                                                    </div>
                                                    {/*<div className="text-xs text-gray-500 dark:text-gray-400 flex flex-col items-end">*/}
                                                    {/*    <span>{chat.date}</span>*/}
                                                    {/*    <span>{chat.time}</span>*/}
                                                    {/*</div>*/}
                                                </div>
                                                <div className="mt-2 flex justify-between items-center">
                                                    <div className="flex flex-wrap gap-1">
                                                        {chat.documents.map((doc, idx) => (
                                                            <div key={idx} className="flex items-center text-xs bg-gray-100 dark:bg-zinc-800 px-2 py-1 rounded">
                                                                <Paperclip className="w-3 h-3 mr-1 text-gray-400" />
                                                                <span className="truncate max-w-[100px]">{doc}</span>
                                                            </div>
                                                        ))}
                                                    </div>
                                                    {/*<div className="flex gap-1">*/}
                                                    {/*    <Badge variant="secondary" className="text-xs">*/}
                                                    {/*        {chat.messageCount} {chat.messageCount === 1 ? 'message' : 'messages'}*/}
                                                    {/*    </Badge>*/}
                                                    {/*</div>*/}
                                                </div>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="flex flex-col items-center justify-center py-8">
                                            <MessageSquare className="h-12 w-12 text-gray-300 dark:text-gray-600 mb-2" />
                                            <h3 className="text-base font-medium">No documents found</h3>
                                        </div>
                                    )}
                                </div>
                            </ScrollArea>
                        </CardContent>
                    </Card>

                    {/* Recently Uploaded Documents */}
                    {/*{uploadedDocuments.length > 0 && (*/}
                    {/*    <Card className="border border-gray-200 dark:border-zinc-800 shadow-sm rounded-xl">*/}
                    {/*        <CardHeader className="pb-2">*/}
                    {/*            <div className="flex items-center justify-between">*/}
                    {/*                <CardTitle className="text-base font-medium">Recent Documents</CardTitle>*/}
                    {/*                <Button variant="ghost" size="sm" className="text-xs">*/}
                    {/*                    View All*/}
                    {/*                </Button>*/}
                    {/*            </div>*/}
                    {/*        </CardHeader>*/}
                    {/*        <CardContent className="space-y-2 pt-0">*/}
                    {/*            {uploadedDocuments.map((doc, index) => (*/}
                    {/*                <div key={index} className="flex items-center justify-between text-sm p-2 hover:bg-gray-50 dark:hover:bg-zinc-900 rounded-md">*/}
                    {/*                    <div className="flex items-center">*/}
                    {/*                        <Paperclip className="w-4 h-4 mr-2 text-gray-400" />*/}
                    {/*                        <span className="truncate max-w-[200px]">{doc.filename}</span>*/}
                    {/*                    </div>*/}
                    {/*                    <div className="flex items-center gap-2">*/}
                    {/*                        <span className="text-xs text-gray-500">{doc.date}</span>*/}
                    {/*                        <div className="flex space-x-1">*/}
                    {/*                            <Button variant="ghost" size="sm" className="h-6 w-6 p-0">*/}
                    {/*                                <Download className="h-3 w-3" />*/}
                    {/*                            </Button>*/}
                    {/*                            <Button variant="ghost" size="sm" className="h-6 w-6 p-0 text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950">*/}
                    {/*                                <Trash2 className="h-3 w-3" />*/}
                    {/*                            </Button>*/}
                    {/*                        </div>*/}
                    {/*                    </div>*/}
                    {/*                </div>*/}
                    {/*            ))}*/}
                    {/*        </CardContent>*/}
                    {/*    </Card>*/}
                    {/*)}*/}
                </div>
            </main>
        </div>
    );
}