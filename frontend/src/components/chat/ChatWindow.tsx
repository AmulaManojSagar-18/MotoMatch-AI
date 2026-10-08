import { useEffect, useRef } from "react";
import type { ChatTurn } from "../../types";
import TypingIndicator from "../common/TypingIndicator";
import ChatMessage from "./ChatMessage";
import "./ChatWindow.css";

const SUGGESTIONS = [
  "I need a bike for daily 40 km city commuting, budget 2 lakh, mileage matters.",
  "Looking for a comfortable highway tourer under 3 lakh.",
  "I want a sporty, powerful bike for weekend rides.",
];

interface Props {
  messages: ChatTurn[];
  isLoading: boolean;
  showHero: boolean;
  onSuggestion: (text: string) => void;
}

export default function ChatWindow({
  messages,
  isLoading,
  showHero,
  onSuggestion,
}: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Keep the latest message / typing indicator in view.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <div className="chat-window">
      {showHero && (
        <div className="chat-hero">
          <h1 className="chat-hero__title">MotoMatch</h1>
          <p className="chat-hero__subtitle">Find the bike that fits you.</p>
          <div className="chat-hero__suggestions">
            {SUGGESTIONS.map((s) => (
              <button
                type="button"
                key={s}
                className="chat-hero__chip"
                onClick={() => onSuggestion(s)}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {messages.map((turn) => (
        <ChatMessage key={turn.id} turn={turn} />
      ))}

      {isLoading && (
        <div className="msg msg--assistant">
          <TypingIndicator />
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
