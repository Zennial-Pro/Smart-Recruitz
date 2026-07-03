"use client";

import { create } from "zustand";

export type MessageType =
  | "text"
  | "data-card"
  | "file-upload"
  | "chips"
  | "processing"
  | "skill-tags"
  | "score-card"
  | "verification";

export type MessageSender = "bot" | "user";

export interface ChatMessage {
  id: string;
  sender: MessageSender;
  type: MessageType;
  content?: string;
  data?: Record<string, unknown>;
  timestamp: number;
}

interface ChatState {
  messages: ChatMessage[];
  isTyping: boolean;
  addMessage: (message: Omit<ChatMessage, "id" | "timestamp">) => void;
  setIsTyping: (typing: boolean) => void;
  clearMessages: () => void;
}

let messageCounter = 0;

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isTyping: false,
  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...message,
          id: `msg-${++messageCounter}`,
          timestamp: Date.now(),
        },
      ],
    })),
  setIsTyping: (typing) => set({ isTyping: typing }),
  clearMessages: () => set({ messages: [] }),
}));
