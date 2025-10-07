// This file is deprecated. Please use the new API functions from /utils/api/index.ts
// Re-exporting for backward compatibility

import { getChatHistoryEntries } from "./chat-history";

/**
 * @deprecated Fetch chat history directly via getChatHistoryEntries instead.
 */
export const getData = async () => {
  const history = await getChatHistoryEntries();
  return { history };
};
