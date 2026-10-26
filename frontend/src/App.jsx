import { useCallback, useRef, useState } from "react";
import { askQuestion, deleteDocument, uploadDocument } from "./api";
import { validateFile } from "./config";
import { useBackendStatus } from "./hooks/useBackendStatus";
import UploadPanel from "./components/UploadPanel";
import Conversation from "./components/Conversation";
import QuestionInput from "./components/QuestionInput";

export default function App() {
  const [doc, setDoc] = useState(null); // { docId, filename, pages, chunks }
  const [upload, setUpload] = useState({ status: "idle", error: null });
  const [messages, setMessages] = useState([]); // { id, question, status, result?, error? }
  const askController = useRef(null);
  const nextId = useRef(0);
  const { status: backend, recheck } = useBackendStatus();

  const busy = messages.some((m) => m.status === "pending");

  const patchMessage = (id, patch) =>
    setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, ...patch } : m)));

  const handleFile = useCallback(
    async (file) => {
      const problem = validateFile(file);
      if (problem) return setUpload({ status: "error", error: problem });

      setUpload({ status: "uploading", error: null });
      askController.current?.abort(); // an answer for the old file would be misleading
      try {
        const info = await uploadDocument(file);
        if (doc) deleteDocument(doc.docId).catch(() => {}); // best effort: frees the old index
        setDoc({ docId: info.doc_id, filename: info.filename ?? file.name, pages: info.pages, chunks: info.chunks });
        setMessages([]);
        setUpload({ status: "idle", error: null });
      } catch (err) {
        setUpload({ status: "error", error: err.message });
      }
    },
    [doc]
  );

  const handleRemove = useCallback(() => {
    askController.current?.abort();
    if (doc) deleteDocument(doc.docId).catch(() => {});
    setDoc(null);
    setMessages([]);
    setUpload({ status: "idle", error: null });
  }, [doc]);

  const handleAsk = useCallback(
    async (question) => {
      if (!doc) return;
      const id = nextId.current++;
      const controller = new AbortController();
      askController.current = controller;
      setMessages((prev) => [...prev, { id, question, status: "pending" }]);
      try {
        const result = await askQuestion(doc.docId, question, controller.signal);
        patchMessage(id, { status: "done", result });
      } catch (err) {
        if (err.name === "AbortError") {
          setMessages((prev) => prev.filter((m) => m.id !== id)); // cancelled: drop the stuck "pending" entry
          return;
        }
        patchMessage(id, { status: "error", error: err.message });
      }
    },
    [doc]
  );

  const handleRetry = useCallback(
    (message) => {
      setMessages((prev) => prev.filter((m) => m.id !== message.id));
      handleAsk(message.question);
    },
    [handleAsk]
  );

  return (
    <div className="app">
      <UploadPanel
        doc={doc}
        upload={upload}
        backend={backend}
        onFile={handleFile}
        onRemove={handleRemove}
        onRecheck={recheck}
      />
      <main className="main">
        <Conversation doc={doc} messages={messages} onRetry={handleRetry} onSuggestion={handleAsk} />
        <QuestionInput disabled={!doc || upload.status === "uploading"} busy={busy} onSubmit={handleAsk} />
      </main>
    </div>
  );
}
