import "./TypingIndicator.css";

/** Three-dot "MotoMatch is thinking..." indicator shown while awaiting /chat. */
export default function TypingIndicator() {
  return (
    <div className="typing" aria-live="polite" aria-label="MotoMatch is thinking">
      <span className="typing__label">MotoMatch is thinking</span>
      <span className="typing__dots">
        <span />
        <span />
        <span />
      </span>
    </div>
  );
}
