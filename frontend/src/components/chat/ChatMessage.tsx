import type { ChatTurn } from "../../types";
import RecommendationCard from "../recommendation/RecommendationCard";
import "./ChatMessage.css";

interface Props {
  turn: ChatTurn;
}

/** Renders one chat turn: a user bubble, an AI bubble, or a recommendation card. */
export default function ChatMessage({ turn }: Props) {
  // An assistant turn with a recommendation is shown as the rich card, with the
  // AI's grounded explanation inside it (so we don't duplicate the text).
  if (turn.role === "assistant" && turn.recommendation) {
    return (
      <div className="msg msg--assistant msg--card">
        <div className="msg__card">
          <RecommendationCard
            recommendation={turn.recommendation}
            bike={turn.bike}
            explanation={turn.text}
          />
        </div>
      </div>
    );
  }

  const roleClass = turn.role === "user" ? "msg--user" : "msg--assistant";
  const errorClass = turn.isError ? " msg--error" : "";

  return (
    <div className={`msg ${roleClass}${errorClass}`}>
      <div className="msg__bubble">{turn.text}</div>
    </div>
  );
}
