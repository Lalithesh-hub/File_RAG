import { Fragment, useState } from "react";

const PREVIEW_CHARS = 140;

/** Turns "[2]" in the answer into buttons that open the matching source. Plain text only: no HTML is ever injected. */
function renderAnswer(text, citations, openId, toggle) {
  const known = new Set(citations.map((c) => c.id));
  return text.split(/(\[\d+\])/g).map((part, i) => {
    const m = part.match(/^\[(\d+)\]$/);
    const id = m ? Number(m[1]) : null;
    if (id !== null && known.has(id)) {
      return (
        <button
          key={i}
          type="button"
          className="cite-mark"
          aria-label={`Source ${id}`}
          aria-expanded={openId === id}
          onClick={() => toggle(id)}
        >
          {id}
        </button>
      );
    }
    return <Fragment key={i}>{part}</Fragment>;
  });
}

function Sources({ citations, openId, toggle }) {
  return (
    <ol className="sources" aria-label="Sources">
      {citations.map((c) => {
        const open = openId === c.id;
        const preview =
          c.text.length > PREVIEW_CHARS ? `${c.text.slice(0, PREVIEW_CHARS).trimEnd()}…` : c.text;
        return (
          <li key={c.id} className={`source${open ? " source--open" : ""}`}>
            <button type="button" className="source-head" aria-expanded={open} onClick={() => toggle(c.id)}>
              <span className="cite-mark cite-mark--static">{c.id}</span>
              <span className="source-page">Page {c.page}</span>
            </button>
            <blockquote className="source-text">{open ? c.text : preview}</blockquote>
          </li>
        );
      })}
    </ol>
  );
}

export default function AnswerCard({ message, onRetry }) {
  const [openId, setOpenId] = useState(null);
  const toggle = (id) => setOpenId((cur) => (cur === id ? null : id));
  const { question, status, result, error } = message;

  return (
    <article className="qa" aria-busy={status === "pending"}>
      <h2 className="question">{question}</h2>

      {status === "pending" && (
        <p className="pending" role="status">
          Reading the file<span className="dots" aria-hidden="true"><i /><i /><i /></span>
        </p>
      )}

      {status === "error" && (
        <div className="answer answer--error" role="alert">
          <div className="error-copy">
            <p className="error-title">Couldn't answer this yet</p>
            <p className="error-detail">{error}</p>
          </div>
          <button type="button" className="btn btn-primary" onClick={() => onRetry(message)}>
            Try again
          </button>
        </div>
      )}

      {status === "done" && result.grounded && (
        <div className="answer">
          <p className="answer-text">{renderAnswer(result.answer, result.citations, openId, toggle)}</p>
          {result.citations.length > 0 && (
            <Sources citations={result.citations} openId={openId} toggle={toggle} />
          )}
        </div>
      )}

      {status === "done" && !result.grounded && (
        <div className="answer answer--absent">
          <p className="absent-title">Not in this file</p>
          <p className="answer-text">{result.answer}</p>
        </div>
      )}
    </article>
  );
}
