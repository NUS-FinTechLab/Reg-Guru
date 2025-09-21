"use client";

import Image from "next/image";
import { AnimatePresence, motion } from "framer-motion";
import { User } from "lucide-react";

interface Message {
  id: number;
  text: string;
  role: "user" | "bot";
  timestamp: Date;
}

interface MessageGroup {
  date: Date;
  messages: Message[];
}

interface ChatMessagesProps {
  messageGroups: MessageGroup[];
  isTyping: boolean;
  formatDate: (date: Date) => string;
  formatTime: (date: Date) => string;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
}

export default function ChatMessages({ messageGroups, isTyping, formatDate, formatTime, messagesEndRef }: ChatMessagesProps) {
  return (
    <div className="w-full px-4 mx-auto space-y-6 pb-20">
      {messageGroups.map((group) => (
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
                      <Image src="/logo.png" alt="Bot avatar" width={36} height={36} className="" />
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
                      <div className="text-sm" dangerouslySetInnerHTML={{ __html: message.text }} />
                      <span className="text-xs opacity-70 block text-right mt-1">{formatTime(message.timestamp)}</span>
                    </div>
                    <div className={"py-2"}>{/* reserved for actions */}</div>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      ))}

      {/* Typing indicator */}
      {isTyping && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="flex justify-start">
          <div className="flex items-end gap-2">
            <div className="flex-shrink-0">
              <Image src="/logo.png" alt="Bot avatar" width={36} height={36} className="rounded-full" />
            </div>
            <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl rounded-bl-none shadow-sm">
              <div className="flex space-x-1">
                <motion.div animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 1, repeatDelay: 0 }} className="w-1 h-1 bg-gray-400 rounded-full" />
                <motion.div animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 1, delay: 0.2, repeatDelay: 0 }} className="w-1 h-1 bg-gray-400 rounded-full" />
                <motion.div animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 1, delay: 0.4, repeatDelay: 0 }} className="w-1 h-1 bg-gray-400 rounded-full" />
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Invisible element at the end to scroll to */}
      <div ref={messagesEndRef} />
    </div>
  );
}
