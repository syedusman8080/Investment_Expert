function DocumentList({ documents, selectedId, onSelect, onDelete }) {
  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <span className="eyebrow">LIBRARY</span>
          <h2>Your documents</h2>
        </div>
        <span className="count-badge">{documents.length}</span>
      </div>
      {documents.length === 0 ? (
        <p className="muted empty-state">Upload a PDF to start asking questions.</p>
      ) : (
        <div className="document-list">
          {documents.map((document) => (
            <div className={`document-row ${selectedId === document.document_id ? 'selected' : ''}`} key={document.document_id}>
              <button className="document-select" onClick={() => onSelect(document.document_id)}>
                <strong>{document.filename}</strong>
                <span>{document.pages} pages · {document.chunks} chunks</span>
              </button>
              <button className="delete-button" aria-label={`Delete ${document.filename}`} onClick={() => onDelete(document.document_id)}>×</button>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

export default DocumentList;
