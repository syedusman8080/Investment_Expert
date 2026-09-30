import { useEffect, useState } from 'react';
import './App.css';
import {
  addKnowledgePdf, addKnowledgeText, createConversation, getConversation, listConversations,
  listKnowledge, login, register, sendMessage,
} from './services/api';

function AdminPanel() {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [sources, setSources] = useState([]);
  const [error, setError] = useState('');
  const refresh = () => listKnowledge().then(setSources).catch((err) => setError(err.message));
  useEffect(refresh, []);
  const submitText = async (event) => {
    event.preventDefault();
    try { await addKnowledgeText(title, content); setTitle(''); setContent(''); refresh(); }
    catch (err) { setError(err.message); }
  };
  const submitPdf = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try { await addKnowledgePdf(file); refresh(); }
    catch (err) { setError(err.message); }
    event.target.value = '';
  };
  return <section className="panel admin-panel"><div className="section-heading"><div><span className="eyebrow">SUPERADMIN</span><h2>Finance Guru knowledge base</h2></div><span className="local-pill">● RAG</span></div>
    <p className="muted">Add trusted investing material. It is embedded and retrieved when users ask related questions; this does not retrain model weights.</p>
    {error && <div className="error-banner">{error}</div>}
    <form className="admin-form" onSubmit={submitText}><input placeholder="Source title" value={title} onChange={(e) => setTitle(e.target.value)} required /><textarea placeholder="Paste educational context or investment guidance…" rows={4} value={content} onChange={(e) => setContent(e.target.value)} required /><button className="primary-button">Add text to knowledge base</button></form>
    <label className="upload-link">Or upload a PDF<input type="file" accept=".pdf,application/pdf" onChange={submitPdf} /></label>
    {sources.length > 0 && <div className="knowledge-list">{sources.map((source) => <div className="knowledge-item" key={source.id}><strong>{source.title}</strong><span>{source.source_type}</span></div>)}</div>}
  </section>;
}

function AuthScreen({ onAuthenticated }) {
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const submit = async (event) => {
    event.preventDefault(); setError('');
    try { onAuthenticated(mode === 'login' ? await login(email, password) : await register(email, password)); }
    catch (err) { setError(err.message); }
  };
  return <main className="auth-shell"><div className="auth-card">
    <div className="brand-mark">F<span>·</span>G</div><span className="eyebrow">FINANCE GURU</span>
    <h1>Investing made understandable.</h1><p className="muted">A friendly guide for learning the basics and making more confident decisions.</p>
    {error && <div className="error-banner">{error}</div>}
    <form onSubmit={submit} className="auth-form"><label>Email<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label>
      <label>Password<input type="password" minLength="8" value={password} onChange={(e) => setPassword(e.target.value)} required /></label>
      <button className="primary-button">{mode === 'login' ? 'Sign in' : 'Create account'}</button>
    </form>
    <button className="text-button" onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>{mode === 'login' ? 'New here? Create an account' : 'Already have an account? Sign in'}</button>
  </div></main>;
}

function App() {
  const [session, setSession] = useState(() => JSON.parse(localStorage.getItem('finance_guru_session') || 'null'));
  const [conversations, setConversations] = useState([]);
  const [active, setActive] = useState(null);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const refresh = async () => { const rows = await listConversations(); setConversations(rows); if (rows[0]) setActive(await getConversation(rows[0].id)); };
  useEffect(() => { if (session) refresh().catch((err) => setError(err.message)); }, [session]);
  const authenticated = (value) => { localStorage.setItem('finance_guru_session', JSON.stringify(value)); setSession(value); };
  const logout = () => { localStorage.removeItem('finance_guru_session'); setSession(null); setActive(null); };
  if (!session) return <AuthScreen onAuthenticated={authenticated} />;
  const newChat = async () => { const chat = await createConversation(); setConversations((items) => [chat, ...items]); setActive({ ...chat, messages: [] }); };
  const selectChat = async (id) => setActive(await getConversation(id));
  const submit = async (event) => {
    event.preventDefault(); if (!message.trim() || !active) return;
    const content = message.trim(); setMessage(''); setLoading(true); setError('');
    try { const reply = await sendMessage(active.id, content); setActive((current) => ({ ...current, messages: [...current.messages, { id: `u-${Date.now()}`, role: 'user', content }, reply] })); }
    catch (err) { setError(err.message); } finally { setLoading(false); }
  };
  return <main className="app-shell">
    <header className="topbar"><div className="brand-mark">F<span>·</span>G</div><div><span className="eyebrow">FINANCE GURU</span><h1>Your investing companion</h1></div><div className="account"><span>{session.user.email}</span><button className="text-button" onClick={logout}>Log out</button></div></header>
    {error && <div className="error-banner">{error}<button onClick={() => setError('')}>×</button></div>}
    {session.user.is_superadmin && <AdminPanel />}
    <div className="chat-layout"><aside className="panel history"><button className="primary-button" onClick={newChat}>+ New conversation</button><div className="history-heading"><span className="eyebrow">YOUR HISTORY</span></div>
      {conversations.map((chat) => <button key={chat.id} className={`history-item ${active?.id === chat.id ? 'selected' : ''}`} onClick={() => selectChat(chat.id)}>{chat.title}</button>)}
      {!conversations.length && <p className="muted">Your conversations will appear here.</p>}
    </aside><section className="panel chat-panel">
      {!active ? <div className="welcome"><span className="empty-icon">✦</span><h2>What would you like to learn?</h2><p className="muted">Ask about saving, investing, stocks, funds, risk, or anything else. I’ll explain it in plain language.</p><button className="primary-button" onClick={newChat}>Start a conversation</button></div> : <>
        <div className="section-heading"><div><span className="eyebrow">CONVERSATION</span><h2>{active.title}</h2></div><span className="local-pill">● EDUCATIONAL</span></div>
        <div className="messages">{active.messages.map((item) => <div className={`message ${item.role}`} key={item.id}><span className="message-label">{item.role === 'user' ? 'YOU' : 'FINANCE GURU'}</span><p>{item.content}</p></div>)}{loading && <div className="message assistant"><span className="message-label">FINANCE GURU</span><p className="typing">Thinking…</p></div>}</div>
        <form className="message-form" onSubmit={submit}><textarea value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Ask a beginner-friendly investing question…" rows={3} /><button className="primary-button" disabled={loading || !message.trim()}>Send</button></form>
        <p className="disclaimer">Finance Guru provides educational information, not personalized financial advice or guaranteed returns.</p>
      </>}
    </section></div>
  </main>;
}

export default App;
