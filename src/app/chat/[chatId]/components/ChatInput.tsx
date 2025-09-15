"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ArrowRight, ArrowUp } from "lucide-react";

interface ChatInputProps {
  value: string;
  onChange: (val: string) => void;
  onSend: (val: string) => void;
  inputRef: React.RefObject<HTMLInputElement | null>;
}

export default function ChatInput({ value, onChange, onSend, inputRef }: ChatInputProps) {
  return (
    <div className="p-4 sticky bg-white dark:bg-[#171717] max-w-[100%] w-full mx-auto flex justify-center bottom-0 border-2 rounded-2xl my-2">
      <div className="mx-auto w-full max-w-lg">
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <Input
              ref={inputRef}
              value={value}
              onChange={(e) => onChange(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && onSend(value)}
              placeholder="Type a message..."
              className="pl-4 pr-12 py-6 max-w-lg w-full rounded-full"
            />
            <AnimatePresence>
              {value.trim() ? (
                <motion.div
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2"
                >
                  <Button onClick={() => onSend(value)} size="icon" className="h-10 w-10 rounded-full cursor-pointer">
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
                  <Button variant="outline" size="icon" className="h-10 w-10 rounded-full">
                    <ArrowUp className="h-5 w-5" />
                  </Button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
}
