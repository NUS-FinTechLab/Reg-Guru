"use client";

import { useEffect, useMemo, useState, type ReactNode, type SyntheticEvent } from "react";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import {
  ArrowLeft,
  ChevronDown,
  ChevronRight,
  ClipboardCheck,
  LayoutGrid,
  MessageSquare,
  MessageSquarePlus,
} from "lucide-react";

import {
  Sidebar as SidebarPrimitive,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
} from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import {
  listChats,
  listChecklists,
  type ChatListItem,
  type ChecklistSummaryDTO,
} from "@/utils/api";
import { getStoredUser } from "@/utils/auth-client";
import { WORKSPACE_MODULES } from "@/app/modules/modules";
import { ToggleTheme } from "@/components/layout/toogle-theme";

interface SectionToggleProps {
  title: ReactNode;
  isOpen: boolean;
  onToggle: () => void;
  children: ReactNode;
}

function SectionToggle({ title, isOpen, onToggle, children }: SectionToggleProps) {
  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between rounded-lg px-2 py-1.5 text-sm font-semibold text-sidebar-foreground/80 transition hover:bg-sidebar/60"
      >
        <span>{title}</span>
        {isOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
      </button>
      {isOpen ? <div className="space-y-2 px-2">{children}</div> : null}
    </div>
  );
}

const CHECKLIST_MODULE = WORKSPACE_MODULES.find((entry) => entry.href === "/modules/compliance-checklist");

export default function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();

  const [chats, setChats] = useState<ChatListItem[]>([]);
  const [checklists, setChecklists] = useState<ChecklistSummaryDTO[]>([]);
  const [isLoadingChats, setIsLoadingChats] = useState(true);
  const [isLoadingChecklists, setIsLoadingChecklists] = useState(true);
  const [chatError, setChatError] = useState<string | null>(null);
  const [checklistError, setChecklistError] = useState<string | null>(null);
  const [chatSectionOpen, setChatSectionOpen] = useState(true);
  const [checklistSectionOpen, setChecklistSectionOpen] = useState(true);

  const handleImageError = (event: SyntheticEvent<HTMLImageElement>) => {
    event.currentTarget.style.visibility = "hidden";
  };

  const LOGIN_CHAT_MESSAGE = "Log in to view your chats";
  const LOGIN_CHECKLIST_MESSAGE = "Log in to view your checklists";
  const loginLinkClass =
    "underline underline-offset-2 font-medium text-destructive transition hover:text-primary focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary/60";

  useEffect(() => {
    let isMounted = true;
    const user = getStoredUser();

    if (!user) {
      if (isMounted) {
        setChatError(LOGIN_CHAT_MESSAGE);
        setIsLoadingChats(false);
        setChecklists([]);
        setChecklistError(LOGIN_CHECKLIST_MESSAGE);
        setIsLoadingChecklists(false);
      }
      return () => {
        isMounted = false;
      };
    }

    setIsLoadingChats(true);
    setIsLoadingChecklists(true);
    setChatError(null);
    setChecklistError(null);

    Promise.allSettled([listChats(), listChecklists()])
      .then((results) => {
        if (!isMounted) {
          return;
        }

        const [chatResult, checklistResult] = results;

        if (chatResult.status === "fulfilled") {
          const sortedChats = [...chatResult.value].sort(
            (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime(),
          );
          setChats(sortedChats);
        } else {
          console.error("Failed to load chats", chatResult.reason);
          setChatError("Unable to load chats");
        }

        if (checklistResult.status === "fulfilled") {
          const sortedChecklists = [...checklistResult.value].sort(
            (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime(),
          );
          setChecklists(sortedChecklists);
        } else {
          console.error("Failed to load checklists", checklistResult.reason);
          setChecklistError("Unable to load checklists");
        }
      })
      .finally(() => {
        if (!isMounted) {
          return;
        }
        setIsLoadingChats(false);
        setIsLoadingChecklists(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    const handleUpdated = (event: Event) => {
      const customEvent = event as CustomEvent<ChatListItem>;
      const updatedChat = customEvent.detail;
      if (!updatedChat) {
        return;
      }
      setChats((previous) => {
        const without = previous.filter((item) => item.id !== updatedChat.id);
        const next = [updatedChat, ...without];
        return next.sort(
          (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime(),
        );
      });
    };

    window.addEventListener("chat-updated", handleUpdated as EventListener);
    return () => window.removeEventListener("chat-updated", handleUpdated as EventListener);
  }, []);

  const chatEntries = useMemo(() => chats.slice(0, 20), [chats]);

  const activeChatId = useMemo(() => {
    if (!pathname?.startsWith("/modules/chat/")) {
      return null;
    }
    const [, , , chatId] = pathname.split("/");
    return chatId ?? null;
  }, [pathname]);

  const handleChatSelect = (chat: ChatListItem) => {
    if (!chat.id) {
      return;
    }
    router.push(`/modules/chat/${chat.id}`);
  };

  const handleCreateChat = () => {
    router.push("/modules/chat");
  };

  const handleCreateChecklist = () => {
    router.push("/modules/compliance-checklist");
  };

  const handleChecklistSelect = (checklistId: string) => {
    router.push(`/modules/compliance-checklist/${checklistId}`);
  };

  return (
    <SidebarPrimitive variant="sidebar" className="w-full max-w-sm">
      <SidebarHeader>
        <div className="flex items-center justify-between px-3 py-4">
          <div className="flex items-center gap-3">
            <div className="relative">
              <Image
                src="/logo.png"
                alt="Reg-Guru"
                width={40}
                height={40}
                className="rounded-full border-2 border-primary/30"
                onError={handleImageError}
              />
              <span className="absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-white bg-emerald-500" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Reg-Guru
              </p>
              <h1 className="text-sm font-semibold">Workspace Hub</h1>
            </div>
          </div>
          <ToggleTheme />
        </div>
      </SidebarHeader>
      <SidebarContent className="space-y-6 px-3 py-4">
        <Button
          type="button"
          variant="ghost"
          onClick={() => router.push("/modules")}
          className="w-full justify-start gap-2 rounded-xl text-sidebar-foreground/80 transition hover:bg-muted"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to workspace
        </Button>
      <SectionToggle
          title={
            <span
              onClick={() => router.push("/modules/chat")}
              className="flex items-center gap-2 text-sidebar-foreground/80 transition hover:text-primary"
            >
              <MessageSquare className="h-4 w-4" />
              <span>Chat</span>
            </span>
          }
          isOpen={chatSectionOpen}
          onToggle={() => setChatSectionOpen((previous) => !previous)}
        >
          <div className="space-y-2">
            {isLoadingChats ? (
              <div className="rounded-lg border border-dashed border-border/60 bg-muted/30 px-3 py-4 text-xs text-muted-foreground">
                Loading conversations…
              </div>
            ) : chatError ? (
              <div className="rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-4 text-xs text-destructive">
                {chatError === LOGIN_CHAT_MESSAGE ? (
                  <span>
                    <button
                      type="button"
                      onClick={() => router.push("/login")}
                      className={loginLinkClass}
                    >
                      Log in
                    </button>
                    <span> to view your chats.</span>
                  </span>
                ) : (
                  chatError
                )}
              </div>
            ) : chatEntries.length === 0 ? (
              <div className="rounded-lg border border-border/60 bg-muted/30 px-3 py-4 text-xs text-muted-foreground">
                No conversations yet.
              </div>
            ) : (
              <ul className="space-y-1.5">
                {chatEntries.map((chat) => {
                  const preview = chat.lastMessage?.text ?? "Start a conversation";
                  const timestamp = chat.lastMessage?.createdAt ?? chat.updatedAt;
                  const isActive = activeChatId === chat.id;

                  return (
                    <li key={chat.id}>
                      <button
                        type="button"
                        onClick={() => handleChatSelect(chat)}
                        className={`w-full rounded-xl border px-3 py-3 text-left transition hover:border-primary/40 hover:bg-primary/5 ${isActive ? "border-primary bg-primary/10" : "border-border/60 bg-background/80"
                          }`}
                      >
                        <p className="text-sm font-medium line-clamp-2">{preview}</p>
                        <p className="mt-1 text-[11px] text-muted-foreground">
                          {new Date(timestamp).toLocaleString()}
                        </p>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </SectionToggle>

        <SectionToggle
          title={
            <span
              onClick={() => router.push("/modules/compliance-checklist")}
              className="flex items-center gap-2 text-sidebar-foreground/80 transition hover:text-primary"
            >
              <ClipboardCheck className="h-4 w-4" />
              <span>Compliance Checklist</span>
            </span>
          }
          isOpen={checklistSectionOpen}
          onToggle={() => setChecklistSectionOpen((previous) => !previous)}
        >
          <div className="space-y-2">
            {isLoadingChecklists ? (
              <div className="rounded-lg border border-dashed border-border/60 bg-muted/30 px-3 py-4 text-xs text-muted-foreground">
                Loading checklists…
              </div>
            ) : checklistError ? (
              <div className="rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-4 text-xs text-destructive">
                {checklistError === LOGIN_CHECKLIST_MESSAGE ? (
                  <span>
                    <button
                      type="button"
                      onClick={() => router.push("/login")}
                      className={loginLinkClass}
                    >
                      Log in
                    </button>
                    <span> to view your checklists.</span>
                  </span>
                ) : (
                  checklistError
                )}
              </div>
            ) : checklists.length === 0 ? (
              <div className="rounded-lg border border-border/60 bg-muted/30 px-3 py-4 text-xs text-muted-foreground">
                No checklists yet. Create your first one to get started.
              </div>
            ) : (
              <ul className="space-y-1.5">
                {checklists.map((checklist) => {
                  const isActive = pathname?.startsWith(`/modules/compliance-checklist/${checklist.id}`);
                  return (
                    <li key={checklist.id}>
                      <button
                        type="button"
                        onClick={() => handleChecklistSelect(checklist.id)}
                        className={`flex w-full flex-col rounded-xl border px-3 py-3 text-left text-sm transition hover:border-primary/40 hover:bg-primary/5 ${isActive ? "border-primary bg-primary/10" : "border-border/60 bg-background/80"
                          }`}
                      >
                        <span className="font-medium">{checklist.title}</span>
                        <span className="mt-1 text-[11px] text-muted-foreground">
                          Updated {new Date(checklist.updatedAt).toLocaleString()}
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </SectionToggle>
      </SidebarContent>
      <SidebarFooter className="mt-auto px-3 pb-5">
        <div className="flex flex-col gap-2 rounded-xl border border-border/60 bg-muted/30 p-3 text-xs text-muted-foreground">
          <div className="flex items-center gap-2 text-foreground">
            <LayoutGrid className="h-4 w-4" />
            <p className="font-semibold">Quick actions</p>
          </div>
          <div className="grid gap-2 sm:grid-cols-2">
            <Button
              size="sm"
              variant="secondary"
              className="justify-center gap-2 rounded-full text-xs"
              onClick={handleCreateChat}
            >
              <MessageSquarePlus className="h-4 w-4" />
              New chat
            </Button>
            <Button
              size="sm"
              variant="secondary"
              className="justify-center gap-2 rounded-full text-xs"
              onClick={handleCreateChecklist}
            >
              <ClipboardCheck className="h-4 w-4" />
              New checklist
            </Button>
          </div>
        </div>
      </SidebarFooter>
    </SidebarPrimitive>
  );
}
