"use client";

import { Button } from "@/components/ui/button";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { ToggleTheme } from "@/components/layout/toogle-theme";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MoreVertical, Pencil, Share, Trash2 } from "lucide-react";

interface ChatHeaderProps {
  isTyping: boolean;
  region: string;
  onRegionChange: (region: string) => void;
}

export default function ChatHeader({ isTyping, region, onRegionChange }: ChatHeaderProps) {
  return (
    <header className="flex z-10 items-center justify-between p-6 border rounded-2xl my-2 bg-white dark:bg-[#171717]">
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
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-800 dark:text-white">Region:</span>
          <Select value={region} onValueChange={onRegionChange}>
            <SelectTrigger className="w-20 text-gray-800 dark:text-white">
              <SelectValue placeholder="Select region" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="SG">SG</SelectItem>
              <SelectItem value="US">US</SelectItem>
              <SelectItem value="EU">EU</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <ToggleTheme />
      </div>
    </header>
  );
}
