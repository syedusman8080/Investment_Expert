import { useState } from 'react';

function ChatPanel({ document, onAsk, loading, answer, sources }) {
  const [question, setQuestion] = useState('');
  const submit = (event) => {
    event.preventDefault();
    if (question.trim()) onAsk(question.trim());
  };

  if (!document) {
    return <section className="panel chat-panel empty-chat"><span className="empty-icon">↗</span><h2>Select a document</h2><p className="muted">Choose a document from your library, then ask anything about its contents.</p></section>;
  }

  return (
    <section className="panel chat-panel">
      <div className="section-heading">
        <div><span className="eyebrow">DOCUMENT QA</span><h2>{document.filename}</h2></div>
        <span className="local-pill">● LOCAL</span>
      </div>
      <form className="question-form" onSubmit={submit}>
        <textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="How many locations are mentioned in this document?" rows={3} />
        <button className="primary-button" disabled={loading || !question.trim()}>{loading ? 'Thinking…' : 'Ask question'}</button>
      </form>
      {answer && <div className="answer-box"><span className="eyebrow">ANSWER</span><p>{answer}</p></div>}
      {sources.length > 0 && (
        <div className="sources">
          <div className="section-heading"><div><span className="eyebrow">RETRIEVED CONTEXT</span><h3>Sources</h3></div><span className="muted">{sources.length} matches</span></div>
          {sources.map((source) => <article className="source-card" key={source.chunk_id}><div className="source-meta"><span>Page {source.page ?? '—'}</span><span>Relevance {(source.score * 100).toFixed(0)}%</span></div><p>{source.text}</p></article>)}
        </div>
      )}
    </section>
  );
}

export default ChatPanel;
