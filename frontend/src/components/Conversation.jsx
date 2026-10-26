import { useEffect, useRef } from "react";
import AnswerCard from "./AnswerCard";

const STARTER_QUESTIONS = [
  "Summarize the key points",
  "What are the main conclusions?",
  "List important dates and numbers",
];

export default function Conversation({ doc, messages, onRetry, onSuggestion }) {
  const endRef = useRef(null);

  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    endRef.current?.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "end" });
  }, [messages]);

  return (
    <div className="convo" aria-live="polite">
      <div className="convo-inner">
        {messages.length === 0 && (
          <div className="empty">
            {doc ? (
              <>
                <p className="empty-title">Ask about {doc.filename}</p>
                <p className="empty-sub">
                  Each answer links to the passages it was built from. If the file doesn't cover the question, you'll be told so.
                </p>
                <div className="starter-questions" aria-label="Suggested questions">
                  {STARTER_QUESTIONS.map((question, index) => (
                    <button
                      className="starter-question"
                      key={question}
                      type="button"
                      onClick={() => onSuggestion(question)}
                    >
                      <span className="starter-index">0{index + 1}</span>
                      {question}
                      <span className="starter-arrow" aria-hidden="true">↗</span>
                    </button>
                  ))}
                </div>
              </>
            ) : (
              <>
                <p className="empty-title">Load a file to begin</p>
                <p className="empty-sub">The file and your questions stay on this computer.</p>
              </>
            )}
          </div>
        )}
        {messages.map((m) => (
          <AnswerCard key={m.id} message={m} onRetry={onRetry} />
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
}
