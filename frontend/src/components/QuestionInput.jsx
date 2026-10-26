import { useRef, useState } from "react";
import { MAX_QUESTION_CHARS } from "../config";

export default function QuestionInput({ disabled, busy, onSubmit }) {
  const [text, setText] = useState("");
  const ref = useRef(null);

  const resize = () => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  };

  const submit = () => {
    const question = text.trim();
    if (!question || disabled || busy) return;
    onSubmit(question);
    setText("");
    requestAnimationFrame(resize);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="composer">
      <div className="composer-inner">
        <label htmlFor="question" className="visually-hidden">Your question</label>
        <textarea
          id="question"
          ref={ref}
          rows={1}
          value={text}
          maxLength={MAX_QUESTION_CHARS}
          disabled={disabled}
          placeholder={disabled ? "Load a file to start asking" : "Ask a question about the file"}
          onChange={(e) => { setText(e.target.value); resize(); }}
          onKeyDown={handleKeyDown}
        />
        <button type="button" className="btn btn-primary" onClick={submit} disabled={disabled || busy || !text.trim()}>
          {busy ? "Reading…" : "Ask"}
        </button>
      </div>
      <p className="composer-hint">Enter to send, Shift+Enter for a new line</p>
    </div>
  );
}
