# API Documentation

This directory contains all the API communication functions for the frontend to interact with the backend.

## Structure

### Available Endpoints

1. **POST /api/chat** - Send chat messages to the RAG system
2. **POST /api/log_feedback** - Submit user feedback 
3. **GET /api/test** - Test API connectivity

### Type Definitions (`types.ts`)

Core TypeScript interfaces for API communication:
- **Message**: Chat message structure
- **ChatRequest**: Chat request interface  
- **ChatResponse**: Chat response interface
- **FeedbackRequest**: Feedback submission interface
- **ApiResponse<T>**: Generic API response wrapper

### API Functions

#### Chat API (`chat.ts`)
- **sendChatMessage(request)**: Send messages to the RAG chat system

#### Feedback API (`feedback.ts`)  
- **submitFeedback(feedbackData)**: Submit user feedback

#### Data API (`getData.tsx`)
- **getTestData()**: Test API connectivity and retrieve basic info

## Usage Examples

### Chat Integration
```typescript
import { sendChatMessage } from '@/utils/api';

const response = await sendChatMessage({
  message: { id: 1, text: "What is Basel III?", role: "user", timestamp: new Date() }
});
```

### Feedback Submission
```typescript  
import { submitFeedback } from '@/utils/api';

await submitFeedback({
  query: "What is Basel III?",
  response: "Basel III is...",
  rating: "thumbs_up",
  comments: "Very helpful!"
});
```

## Component Integration Status

### Current Implementation Status
- **`ChatPage.tsx`**: Using `sendChatMessage()` for chat functionality
- **`FeedbackPage.tsx`**: Using `submitFeedback()` for feedback submission
- **`ContactPage.tsx`**: Using `submitFeedback()` for contact form submission

### CORS Configuration
The backend is configured to accept requests from:
- `http://localhost:3000` (development)
- `https://cheerful-cocada-8192f4.netlify.app` (production)

## Error Handling

All API functions include comprehensive error handling:
- Network connectivity issues
- Invalid request data
- Server-side errors
- Proper error message propagation to UI components

## Features

### Chat System
- Real-time messaging with RAG-powered responses
- Message history management
- Typing indicators and loading states

### Feedback System  
- User satisfaction ratings (thumbs up/down)
- Optional detailed comments
- Persistent feedback storage

The API layer provides a clean abstraction between the frontend components and backend services, with proper TypeScript typing and error handling throughout.
- **Message**: Chat message interface
- **ChatRequest/ChatResponse**: Chat API interfaces
- **ChatHistoryEntry**: Chat history record structure
- **FeedbackRequest**: Feedback logging interface
- **ApiResponse<T>**: Generic API response wrapper

### 2. `/frontend/src/utils/api/chat.ts`
- **sendChatMessage(message)**: Send chat messages to backend
- Automatically triggers chat history caching for quick access

### 3. `/frontend/src/utils/api/chat-history.ts`
- **getChatHistoryEntries()**: Get recent history entries
- **createChatHistoryEntry()**: Persist question/answer pairs

### 4. `/frontend/src/utils/api/feedback.ts`
- **logFeedback(feedbackData)**: Log user feedback (thumbs up/down with comments)
- **testApi()**: Test API connectivity

### 5. `/frontend/src/utils/api/index.ts`
- Central export file for all API functions and types
- Re-exports SERVER_URL constant

### 6. `/frontend/src/utils/api/getData.tsx` (Simplified)
- Backward compatibility with simplified functionality
- Document-related functions removed

## Updated Components & Pages

### ✅ Chat Components
- **`ChatPage.tsx`**: Uses `sendChatMessage()` and records chat history entries
- **`AppSidebar.tsx`**: Displays chat history via `getChatHistoryEntries()`
  - Shows recent conversations with search functionality
  - Click to resume a conversation from history
  - Loading states and error handling

### ✅ Contact & Feedback Forms
- **`FeedbackSection.tsx`**: Enhanced with API integration
  - Uses `testApi()` to verify backend connectivity
  - Better error handling and user feedback
  - Improved email formatting with proper subject lines
- **`ContactSection.tsx`**: Enhanced with API integration
  - Similar improvements to feedback form
  - Proper error states and loading indicators

### ✅ Form Improvements
- **Loading states**: "Sending..." during form submission
- **Success feedback**: Confirmation messages after submission
- **Error handling**: Graceful error messages if API fails
- **API validation**: Test connectivity before form submission

## New Features Added

### 🆕 Smart Sidebar with Saved Queries
- Displays recent chat history entries in the sidebar
- Search functionality to filter through queries
- Click any chat history entry to resume the associated conversation
- Loading skeletons while fetching data
- Empty state when no queries exist

### 🆕 Enhanced Contact Experience
- Better structured email templates
- Proper subject lines for different form types
- API connectivity testing before submission
- Improved user feedback and error handling

## Benefits of This Organization

1. **✅ Removed Dead Code**: Eliminated calls to non-existent endpoints
2. **✅ Centralized API Logic**: All API calls are now in one place
3. **✅ Type Safety**: Full TypeScript interfaces for all API interactions
4. **✅ Error Handling**: Consistent error handling across all API calls
5. **✅ Reusability**: Functions can be easily imported and reused
6. **✅ User Experience**: Enhanced forms with proper feedback and states
7. **✅ Smart Features**: Sidebar now shows recent chat history
8. **✅ Maintainability**: Easy to update API endpoints in one location

## Current API Usage Across Frontend

### Chat Features
```typescript
// ChatPage.tsx - Main chat functionality
import { sendChatMessage, createChatHistoryEntry } from '@/utils/api';

// AppSidebar.tsx - Chat history display
import { getChatHistoryEntries } from '@/utils/api';
```

### Contact & Feedback
```typescript
// FeedbackSection.tsx & ContactSection.tsx - Form enhancement
import { testApi } from '@/utils/api';
```

### Backward Compatibility
```typescript
// getData.tsx - Legacy support
import { getAllData } from '@/utils/api';
```

## Recommendations for Future Enhancement

1. **Add real-time updates** - Refresh sidebar when new history entries are saved
2. **Implement history management** - Add delete/edit functionality for history entries
3. **Tighten auth checks** - Decode JWT and authorize per user session
4. **Enhanced search** - Add full-text search across stored responses
5. **Implement proper feedback API** - Replace mailto with actual backend endpoint

## Testing Checklist ✅

- [x] Chat functionality works with new API functions
- [x] Saved queries display in sidebar
- [x] Search functionality works in sidebar
- [x] Contact form enhanced with API testing
- [x] Feedback form enhanced with API testing
- [x] No more calls to non-existent endpoints
- [x] Backward compatibility maintained
- [x] TypeScript types working correctly
- [x] Error handling implemented throughout
