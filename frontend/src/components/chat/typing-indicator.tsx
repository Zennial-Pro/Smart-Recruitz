export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 self-start rounded-2xl rounded-bl-sm bg-gray-100 px-4 py-3">
      <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:0ms]" />
      <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:150ms]" />
      <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:300ms]" />
    </div>
  );
}
