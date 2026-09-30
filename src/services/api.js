const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
async function request(path, options = {}) {
  const session = JSON.parse(localStorage.getItem('finance_guru_session') || 'null');
  const headers = { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...(session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {}), ...options.headers };
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || 'Something went wrong. Please try again.');
  return payload;
}
export const login = (email, password) => request('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
export const register = (email, password) => request('/auth/register', { method: 'POST', body: JSON.stringify({ email, password }) });
export const listConversations = () => request('/conversations');
export const createConversation = () => request('/conversations', { method: 'POST' });
export const getConversation = (id) => request(`/conversations/${id}`);
export const sendMessage = (id, content) => request(`/conversations/${id}/messages`, { method: 'POST', body: JSON.stringify({ content }) });
export const listKnowledge = () => request('/admin/knowledge');
export const addKnowledgeText = (title, content) => request('/admin/knowledge/text', { method: 'POST', body: JSON.stringify({ title, content }) });
export function addKnowledgePdf(file) {
  const body = new FormData();
  body.append('file', file);
  return request('/admin/knowledge/pdf', { method: 'POST', body });
}
