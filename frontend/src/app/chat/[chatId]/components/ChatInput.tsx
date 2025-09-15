"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ArrowUp } from "lucide-react";

interface ChatInputProps {
  value: string;
  onChange: (val: string) => void;
  onSend: (val: string) => void;
  inputRef: React.RefObject<HTMLInputElement | null>;
}

export default function ChatInput({ value, onChange, onSend, inputRef }: ChatInputProps) {
  return (
    <div className="py-8 mx-auto w-full max-w-4xl">
      <div className="relative">
        <Input
              ref={inputRef}
              value={value}
              onChange={(e) => onChange(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && onSend(value)}
              placeholder="Type a message..."
              className="pl-8 pr-16 py-8 w-full rounded-full md:text-lg file:text-lg"
            />
            <div className="absolute right-4 top-1/2 transform -translate-y-1/2">
              <Button onClick={() => onSend(value)} variant="outline" size="icon" className="h-10 w-10 rounded-full">
                <ArrowUp className="h-5 w-5" />
              </Button>
            </div>
          </div>
        </div>
  );
}
