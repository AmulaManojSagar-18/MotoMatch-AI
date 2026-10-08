import { useCallback, useState } from "react";
import ChatInput from "../components/chat/ChatInput";
import ChatWindow from "../components/chat/ChatWindow";
import { ApiError, getBike, sendChatMessage } from "../services/api";
import type { ChatTurn } from "../types";
import "./ChatPage.css";

let turnCounter = 0;
function uid(): string {
  turnCounter += 1;
  return `turn-${Date.now()}-${turnCounter}`;
}

const WELCOME: ChatTurn = {
  id: "welcome",
  role: "assistant",
  text: "Hi! I'm MotoMatch. Tell me about your riding needs - your budget, how far you ride, and what matters most - and I'll recommend the right bike from our lineup.",
};

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatTurn[]>([WELCOME]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const hasStarted = messages.some((m) => m.role === "user");

  const handleSend = useCallback(
    async (text: string) => {
      if (isLoading) return;

      const userTurn: ChatTurn = { id: uid(), role: "user", text };
      setMessages((prev) => [...prev, userTurn]);
      setIsLoading(true);

      try {
        const res = await sendChatMessage(text, conversationId);
        setConversationId(res.conversation_id);

        // If a bike was recommended, fetch its factual specs for the card.
        let bike;
        if (res.recommendation) {
          try {
            bike = await getBike(res.recommendation.bike_id);
          } catch {
            // Specs are a nice-to-have; the card still shows name + score.
            bike = undefined;
          }
        }

        const assistantTurn: ChatTurn = {
          id: uid(),
          role: "assistant",
          text: res.message,
          recommendation: res.recommendation ?? undefined,
          bike,
        };
        setMessages((prev) => [...prev, assistantTurn]);
      } catch (err) {
        const message =
          err instanceof ApiError
            ? err.message
            : "Something went wrong. Please try again.";
        setMessages((prev) => [
          ...prev,
          { id: uid(), role: "assistant", text: message, isError: true },
        ]);
      } finally {
        setIsLoading(false);
      }
    },
    [conversationId, isLoading],
  );

  return (
    <div className="chat-page">
      <header className="chat-header">
        <div className="chat-header__brand">
          <span className="chat-header__logo" aria-hidden="true">
            🏍️
          </span>
          <span className="chat-header__name">MotoMatch</span>
        </div>
        <div className="chat-header__status">
          <span className="chat-header__dot" aria-hidden="true" />
          Online
        </div>
      </header>

      <main className="chat-main">
        <div className="chat-main__inner">
          <ChatWindow
            messages={messages}
            isLoading={isLoading}
            showHero={!hasStarted}
            onSuggestion={handleSend}
          />
        </div>
      </main>

      <footer className="chat-footer">
        <div className="chat-footer__inner">
          <ChatInput onSend={handleSend} disabled={isLoading} />
          <p className="chat-footer__hint">
            MotoMatch recommends only from its 10-bike catalog.
          </p>
        </div>
      </footer>
    </div>
  );
}
