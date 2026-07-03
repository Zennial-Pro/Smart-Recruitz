"use client";

import { useEffect, useRef } from "react";
import { useChatStore } from "@/stores/chat-store";
import { MessageRenderer } from "./message-renderer";
import { TypingIndicator } from "./typing-indicator";

export function ChatShell({ children }: { children?: React.ReactNode }) {
  const { messages, isTyping } = useChatStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, isTyping]);

  return (
    <div className="flex flex-1 flex-col overflow-y-auto px-4 py-6">
      <div className="mx-auto flex w-full max-w-2xl flex-col gap-3">
        {messages.map((msg) => <MessageRenderer key={msg.id} message={msg} />)}
        {isTyping && <TypingIndicator />}
        {children}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
