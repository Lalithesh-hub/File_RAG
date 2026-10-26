import { useRef, useState } from "react";
import { ACCEPTED_EXTENSIONS, MAX_UPLOAD_MB, USE_MOCK } from "../config";

const STATUS_TEXT = {
  checking: "Checking the backend",
  online: "Backend connected",
  offline: "Backend not reachable",
};

export default function UploadPanel({ doc, upload, backend, onFile, onRemove, onRecheck }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const uploading = upload.status === "uploading";

  const pick = () => !uploading && inputRef.current?.click();

  const handleChange = (e) => {
    const file = e.target.files?.[0];
    e.target.value = ""; // lets the same file be chosen again after an error
    if (file) onFile(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file && !uploading) onFile(file);
  };

  return (
    <aside className="side">
      <header>
        <h1 className="brand">Ask your file</h1>
        <p className="side-extra lede">
          Answers come only from the file you load, with the passages they came from.
        </p>
      </header>

      <input
        ref={inputRef}
        type="file"
        hidden
        accept={ACCEPTED_EXTENSIONS.join(",")}
        onChange={handleChange}
      />

      {doc ? (
        <section className="file-card" aria-label="Loaded file">
          <p className="file-name" title={doc.filename}>{doc.filename}</p>
          <p className="file-meta">{doc.pages} {doc.pages === 1 ? "page" : "pages"} read</p>
          <p className="file-meta">{doc.chunks} passages indexed</p>
          <div className="file-actions">
            <button type="button" className="btn btn-quiet" onClick={pick} disabled={uploading}>
              Replace file
            </button>
            <button type="button" className="btn btn-quiet" onClick={onRemove} disabled={uploading}>
              Remove
            </button>
          </div>
          {uploading && <p className="note" role="status">Reading and indexing the new file…</p>}
        </section>
      ) : (
        <div
          className={`dropzone${dragging ? " dropzone--over" : ""}${uploading ? " dropzone--busy" : ""}`}
          role="button"
          tabIndex={0}
          aria-disabled={uploading}
          aria-label="Load a file"
          onClick={pick}
          onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), pick())}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
        >
          {uploading ? (
            <p role="status" className="drop-title">Reading and indexing…</p>
          ) : (
            <>
              <p className="drop-title">Drop a file here</p>
              <p className="drop-sub">or click to choose one</p>
            </>
          )}
        </div>
      )}

      {upload.error && <p className="error" role="alert">{upload.error}</p>}

      <p className="side-extra hint">
        Works with PDF, Word, PowerPoint, Excel, CSV, HTML, text, Markdown and images, up to {MAX_UPLOAD_MB} MB. Scanned pages are read with OCR.
      </p>

      <footer className="side-foot">
        {USE_MOCK && <p className="note">Demo mode: the answers are samples.</p>}
        <p className={`status status--${backend}`}>
          <span className="dot" aria-hidden="true" />
          {STATUS_TEXT[backend]}
        </p>
        {backend === "offline" && (
          <button type="button" className="btn btn-quiet" onClick={onRecheck}>Check again</button>
        )}
      </footer>
    </aside>
  );
}
