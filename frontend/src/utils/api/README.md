# Frontend API Utilities

This directory contains the TypeScript helpers the frontend uses when talking to the backend.

## Endpoints Used
- `POST /api/chat` – send a message to the assistant and persist the reply
- `GET /api/chat/:chatId` – load the full message history for a chat
- `GET /api/chats` – list chats for the authenticated user
- `POST /api/auth/login` / `POST /api/auth/register` – user authentication

## Files
- **`types.ts`** – shared interfaces (`Message`, `ChatRequest`, `ChatResponse`, `ChatDetailResponse`, `ChatListItem`, `AuthUser`)
- **`chat.ts`** – `sendChatMessage()` and `fetchChat()` helpers
- **`chats.ts`** – `listChats()` helper that powers the sidebar
- **`auth.ts`** – `loginUser()`, `registerUser()`, `logoutUser()`
- **`misc.ts`** – `testApi()` helper for the contact/feedback forms
- **`index.ts`** – convenience barrel export for the helpers and types

## Example Usage
```ts
import { sendChatMessage, listChats } from "@/utils/api";

await sendChatMessage({ text: "What is Basel III?", userId: user.id });
const chats = await listChats();
```

These thin wrappers keep API calls consistent, centralize auth headers, and make it easy to evolve the transport layer without touching every component.
