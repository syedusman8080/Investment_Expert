import { useRef } from 'react';

function UploadPanel({ onUpload, busy }) {
  const inputRef = useRef(null);

  return (
    <section className="panel upload-panel">
      <div>
        <span className="eyebrow">LOCAL WORKSPACE</span>
        <h2>Add a document</h2>
        <p className="muted">Your PDF stays on this computer. Text, embeddings, and answers never leave the local backend.</p>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        hidden
        onChange={(event) => event.target.files?.[0] && onUpload(event.target.files[0])}
      />
      <button className="primary-button" disabled={busy} onClick={() => inputRef.current?.click()}>
        {busy ? 'Processing…' : 'Choose PDF'}
      </button>
    </section>
  );
}

export default UploadPanel;
