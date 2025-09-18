"use client";

import { motion } from "framer-motion";
import { ExternalLink } from "lucide-react";
import { Source } from "@/utils/api/types";

interface SourceLinksProps {
  sources: Source[];
}

export default function SourceLinks({ sources }: SourceLinksProps) {
  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2, duration: 0.3 }}
      className="mt-3 space-y-2"
    >
      <div className="flex flex-wrap gap-2">
        {sources.map((source, index) => (
          <motion.a
            key={index}
            href={source.link}
            target="_blank"
            rel="noopener noreferrer"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 * index, duration: 0.2 }}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-blue-700 dark:text-blue-300 bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-full hover:bg-blue-100 dark:hover:bg-blue-900/30 hover:border-blue-300 dark:hover:border-blue-700 transition-all duration-200 group"
          >
            <ExternalLink className="w-3 h-3 flex-shrink-0" />
            <span className="truncate max-w-[200px]" title={source.title}>
              {source.title}
            </span>
          </motion.a>
        ))}
      </div>
      <div className="text-xs text-gray-500 dark:text-gray-400">
        📄 {sources.length} source{sources.length > 1 ? 's' : ''} referenced
      </div>
    </motion.div>
  );
}